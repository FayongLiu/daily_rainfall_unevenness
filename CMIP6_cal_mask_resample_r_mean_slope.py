# -*- coding: utf-8 -*-
from multiprocessing import Pool, cpu_count
from scipy.stats import linregress
from tqdm import tqdm  
import xarray as xr
import numpy as np
import os
from functools import partial
import gc
import time
import pandas as pd
import re

# Linear trend function
def calc_trend(y, time_index):
    mask = ~np.isnan(y) & ~np.isnan(time_index)

    if np.sum(mask) < 2:
        return np.nan, np.nan
    try:
        slope, _, _, p_value, _ = linregress(time_index[mask], y[mask])
        return slope, p_value
    except Exception:
        return np.nan, np.nan    

def process_single_file(file_path, model, mask_file):
    #print(f"Processing file: {file_path}")
    match = re.search(rf'{model}_(\d{{4}})\.nc', os.path.basename(file_path))
    if not match:
        print(f"Year not found in filename: {file_path}")
        return None
    year = int(match.group(1))
   
    # 打开数据
    ds = xr.open_dataset(file_path) 

    if 'r_rmax' not in ds.variables:
        print(f"r_rmax not found in {file_path}")
        ds.close()
        return None
    
    r = ds['r_rmax']   
    # 获取经纬度变量名
    lon_name = 'lon' if 'lon' in ds.coords else 'longitude'
    lat_name = 'lat' if 'lat' in ds.coords else 'latitude'    
    # 处理经度范围
    if ds[lon_name].max() > 180:
        ds = ds.assign_coords({lon_name: np.where(ds[lon_name] > 180, ds[lon_name] - 360, ds[lon_name])})
        ds = ds.sortby(lon_name)  # 确保经度有序        
  
    # 打开掩膜和目标网格
    mask_ds = xr.open_dataset(mask_file)    
    mask_data = mask_ds['S_daily_mean']        
    # 获取掩膜文件的经纬度变量名
    mask_lon_name = 'lon' if 'lon' in mask_ds.coords else 'longitude'
    mask_lat_name = 'lat' if 'lat' in mask_ds.coords else 'latitude'
    mask_lon = mask_ds[mask_lon_name]
    mask_lat = mask_ds[mask_lat_name]    
    # 处理掩膜文件的经度范围
    if mask_ds[mask_lon_name].max() > 180:
        mask_ds = mask_ds.assign_coords({mask_lon_name: np.where(mask_ds[mask_lon_name] > 180, mask_ds[mask_lon_name] - 360, mask_ds[mask_lon_name])})
        mask_ds = mask_ds.sortby(mask_lon_name)  # 确保经度有序

    # 插值到掩膜的网格
    lon_name = 'lon' if 'lon' in r.coords else 'longitude'
    lat_name = 'lat' if 'lat' in r.coords else 'latitude'
    resampled_r = r.interp({lat_name: mask_lat, lon_name: mask_lon}, method='linear')

    # 掩膜处理
    masked_r = resampled_r.where(~np.isnan(mask_data))
    # 给时间维度    
    if "time" not in masked_r.dims:
        masked_r = masked_r.expand_dims(time=[year])
    else:
        masked_r = masked_r.assign_coords(time=[year])

    # 释放资源
    ds.close()
    mask_ds.close()
    gc.collect()
    
    return masked_r
    
# Process all files under a model directory
def process_model(model, input_dirct, output_dirct, mask_file):
    model_input_dir = os.path.join(input_dirct, model)
    model_output_dir = os.path.join(output_dirct)
    files = []
    for fname in os.listdir(model_input_dir):
        match = re.search(rf'{model}_(\d{{4}})\.nc', fname)
        if match:
            year = int(match.group(1))
            if 1980 <= year <= 2020:
                files.append(os.path.join(model_input_dir, fname))
    files.sort()
    print(f"{model}: Found {len(files)} files")

    r_list = []
    for f in files:
        #weighted_r = process_single_file(f, model, mask_file, target_nc_file)
        r = process_single_file(f, model, mask_file)
        #if weighted_r is not None:
        if r is not None:
            #r_list.append(weighted_r)
            r_list.append(r)
    if not r_list:
        print(f"No valid R_ratio for model {model}")
        return

    r_all = xr.concat(r_list, dim='time').sortby('time')
    r_mean = r_all.mean(dim='time', skipna=True)
    time_index = r_all['time'].values.astype('int')
    #time_index = r_all['time'].dt.year.values
    trends = xr.apply_ufunc(
        calc_trend,
        r_all,
        input_core_dims=[["time"]],
        output_core_dims=[[], []],
        vectorize=True,
        dask='parallelized',
        output_dtypes=[float, float],
        kwargs={'time_index': time_index}
    )
    trend, p_value = trends[0], trends[1]

    result_ds = xr.Dataset({
        "R_ratio_mean": r_mean,
        "R_ratio_trend": trend,
        "R_ratio_p_values": p_value
    })
    
    # --- 检查是否全部为 NaN ---
    for var in result_ds.data_vars:
        all_nan = result_ds[var].isnull().all().item()  # .item() 转为布尔值
        print(f"{var} all NaN:{all_nan}")
    
    output_file = os.path.join(model_output_dir, f"{model}.nc")
    os.makedirs(model_output_dir, exist_ok=True)
    result_ds.to_netcdf(output_file)
    print(f"Saved: {output_file}")
    return

# Wrapper to parallelize processing for all models
def process_all_models_parallel(models, input_dirct, output_dirct, num_workers=None):
    #num_workers = num_workers or min(cpu_count(), len(models))
    num_workers = 10
    tasks = [(model, input_dirct, output_dirct, mask_file) for model in models]
    print(f"Processing {len(models)} models using {num_workers} workers...")
    with Pool(processes=num_workers) as pool:
        pool.starmap(process_model,tasks)

# Main loop
if __name__ == "__main__":
    start_time = time.time()
    print(f"Started processing at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    models = [
        "ACCESS-CM2_day", "BCC-ESM1", "CMCC-CM2-HR4_day", "IITM-ESM_day", "NorCPM1",
        "ACCESS-ESM1-5_day", "CMCC-CM2-SR5_day", "MIROC6_day", "NorESM2-LM_day",
        "CanESM5_day", "CMCC-ESM2_day", "MPI-ESM-1-2-HAM_day", "NorESM2-MM_day",
        "CESM2", "EC-Earth3-CC_day", "MPI-ESM1-2-HR_day", "AWI-ESM-1-1-LR_day",
        "CESM2-FV2_day", "FGOALS-g3_day", "MPI-ESM1-2-LR_day", "SAM0-UNICON_day",
        "AWI-ESM-1-REcoM_day", "CESM2-WACCM_day", "GISS-E2-2-G_day", "MRI-ESM2-0_day", "TaiESM1_day",
        "CESM2-WACCM-FV2_day", 
    ]
    
    
    mask_file = "/data1/yyzhao/data/1980-2020/finally_result/data/CRU_s_d_mean_slope_noarea.nc"
    input_dirct = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_r/"
    output_dirct = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_r_resample_mean_slope_noarea/"

    process_all_models_parallel(models, input_dirct, output_dirct, num_workers=10)
    end_time = time.time()
    print(f"\nFinished processing at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total time elapsed: {(end_time - start_time) / 3600:.2f} hours")
