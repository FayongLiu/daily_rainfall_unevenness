# -*- coding: utf-8 -*-
import os
import re
import gc
import numpy as np
import xarray as xr
from scipy.stats import linregress
from multiprocessing import Pool, cpu_count
from functools import partial


def find_max_annual_precipitation(input_dir, start_year=1980, end_year=2020):
    
    # 获取所有nc文件并筛选年份
    nc_files = []
    for f in os.listdir(input_dir):
        if f.endswith('.nc') and re.match(r'pre_(\d{4})_daily\.nc', f):
            # 从文件名中提取年份
            match = re.search(r'pre_(\d{4})_daily\.nc', f)
            year = int(match.group(1))
            
            # 只处理指定年份范围内的文件
            if start_year <= year <= end_year:
                nc_files.append(os.path.join(input_dir, f))
    
    if not nc_files:
        raise FileNotFoundError(f"{input_dir} not find file")
    
    max_annual_precipitation = 0.0
    
    print(f"cal max_annual_pre,totally {len(nc_files)}files...")
    
    # 遍历每个nc文件
    for i, file_path in enumerate(nc_files):
        try:
            # 打开nc文件
            with xr.open_dataset(file_path) as ds:
                # 检查文件是否包含pre变量
                if 'pre' not in ds:
                    print(f"warning:{file_path} not find pre,passing...")
                    continue
                
                # 确保降水量非负
                precipitation = ds['pre'].where(ds['pre'] >= 0, 0)
                
                # 计算年总降水量
                annual_sum = precipitation.sum(dim='time', skipna=True)
                
                # 找到最大值
                file_max = float(annual_sum.max(skipna=True).values)
                
                # 更新全局最大值
                max_annual_precipitation = max(max_annual_precipitation, file_max)

                
        except Exception as e:
            print(f"file {file_path} error: {str(e)}")
    
    print(f"max_pre:{max_annual_precipitation}")
    return max_annual_precipitation



def calculate_seasonality_index(ds, Rmax):

    # 确保降水量非负
    precipitation = ds['pre']
    precipitation = precipitation.where(precipitation >= 0, 0)
    
    # 计算每个网格点的总降水量
    R = precipitation.sum(dim='time', skipna=True)
    
    # 计算日季节性指数
    m = precipitation.sizes['time']  # 时间步数，365或366
    q = 1 / m  # 平均比例q
    
    # 避免除以零
    valid = R > 0
    pi = xr.where(valid, precipitation / R, np.nan)  # 降水比例(pi)
    
    # 计算季节性指数D
    D_daily = xr.where(pi > 0, (pi * np.log2(pi / q)), np.nan)
    D_daily = D_daily.sum(dim='time', skipna=True)
    S_daily = D_daily * R / Rmax
    S_daily = S_daily.where(valid, np.nan)
    
    # 计算月季节性指数
    monthly_precip = precipitation.resample(time='1ME').sum(dim='time', skipna=True)  # 月总降水量
    q = 1 / 12  # 平均比例q
    
    # 避免除以零
    pi = xr.where(valid, monthly_precip / R, np.nan)  # 降水比例(pi)
    
    # 计算季节性指数D
    D_monthly = xr.where(pi > 0, (pi * np.log2(pi / q)), np.nan)
    D_monthly = D_monthly.sum(dim='time', skipna=True)
    S_monthly = D_monthly * R / Rmax
    S_monthly = S_monthly.where(valid, np.nan)
    
    # 释放内存
    del precipitation, monthly_precip, R, valid, pi
    gc.collect()
    
    return S_daily, S_monthly,D_daily,D_monthly

def process_and_save(file_path, Rmax, area_file):

    area_ds = xr.open_dataset(area_file)
    area = area_ds['area']
    area_lat = area_ds['lat']
    area_lon = area_ds['lon']
 
    try:
        # 从文件名中提取年份
        match = re.search(r'pre_(\d{4})_daily\.nc', os.path.basename(file_path))
        if not match:
            print(f"warning:file {file_path} not find year")
            return None
        year = int(match.group(1))
        
        # 打开nc文件
        with xr.open_dataset(file_path) as ds:
            # 检查文件是否包含tp变量
            if 'pre' not in ds:
                print(f"warning:{file_path} not find PRE,passing...")
                return None
            
            # 计算季节性指数
            S_daily, S_monthly, D_daily, D_monthly = calculate_seasonality_index(ds, Rmax)

            # 构建初始数据集（无统一网格）
            raw_ds = xr.Dataset(
                data_vars={
                    'S_daily': S_daily,
                    'S_monthly': S_monthly,
                    'D_daily': D_daily,
                    'D_monthly': D_monthly
                },
                coords={
                        'lat': S_daily['lat'],
                        'lon': S_daily['lon']
                    }
            )
            
            raw_ds = raw_ds.expand_dims(time=[year])

            # 重采样到统一经纬度网格
            interpolated_ds = raw_ds.interp(
                {'lat': area_lat, 'lon': area_lon},
                method='linear'
            )

            # 面积加权处理
            result_ds = xr.Dataset()
            for var in ['S_daily', 'S_monthly', 'D_daily', 'D_monthly']:
                if var in interpolated_ds:
                    data = interpolated_ds[var]

                    # 掩膜有效像元用于计算总面积
                    valid_mask = ~np.isnan(data.isel(time=0))
                    area = area.assign_coords(lat=data['lat'], lon=data['lon'])
                    total_area = area.where(valid_mask).sum()
                    # 加权计算：保留时间维度
                    weighted_data = data * area / total_area
                    result_ds[var] = weighted_data
                    #result_ds[var] = data

            return result_ds
            
    except Exception as e:
        print(f"process: {file_path} error: {str(e)}")
        return None

def main(input_dir, output_dir, output_filename='CRU_s_d.nc', num_workers=10, start_year=1980, end_year=2020):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 计算最大年降水量
    Rmax = find_max_annual_precipitation(input_dir, start_year, end_year)
    
    # 获取所有nc文件并筛选年份
    nc_files = []
    for f in os.listdir(input_dir):
        if f.endswith('.nc') and re.match(r'pre_(\d{4})_daily\.nc', f):
            # 从文件名中提取年份
            match = re.search(r'pre_(\d{4})_daily\.nc', f)
            year = int(match.group(1))
            
            # 只处理指定年份范围内的文件
            if start_year <= year <= end_year:
                nc_files.append(os.path.join(input_dir, f))
    
    if not nc_files:
        raise FileNotFoundError(f"{input_dir} not find file")
    
    # 使用多进程处理文件
    num_workers = 10
    print(f"using num_workers {num_workers} to work num of {len(nc_files)}")
    
    with Pool(processes=num_workers) as pool:
        process_func = partial(process_and_save, Rmax=Rmax,area_file=area_file)
        
        results = pool.map(process_func, nc_files)   
    results = [r for r in results if r is not None]
    if len(results) == 0:
        raise RuntimeError("All results are None. Please check data or processing function.")
         
    # 使用xarray.concat合并所有结果
    print("combined all data...")
    combined_ds = xr.concat(results, dim='time')
    
    # 确保时间维度是有序的
    combined_ds = combined_ds.sortby('time')
    
    # 保存结果
    output_path = os.path.join(output_dir, output_filename)
    print(f"save: {output_path}")
    combined_ds.to_netcdf(output_path)
    print("end")


if __name__ == "__main__":
    # 直接设置参数，不使用参数解析器
    area_file = '/data1/fyliu/c_temperature_variability/data/area_bio_cli_mask/area_mask/area_0.1deg.nc'    
    input_dir = "/data1/yyzhao/data/CRU-JRA/pre/"  # 请替换为实际的输入目录路径
    output_dir = "/data1/yyzhao/data/1980-2020/finally_result/data/"  # 请替换为实际的输出目录路径
    output_filename = 'CRU_s_d.nc'
    num_workers = None  # 设置为None将使用所有可用的CPU核心
    start_year = 1980  # 开始年份
    end_year = 2020    # 结束年份
    
    # 调用主函数
    main(input_dir, output_dir, output_filename, num_workers, start_year, end_year)