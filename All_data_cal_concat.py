# -*- coding: utf-8 -*-
import xarray as xr
import os
from pathlib import Path

def calculate_nc_mean(folder_path,output_path):
#计算cmip6的平均值
    
    # 获取文件夹中所有nc文件
    nc_files = list(Path(folder_path).glob('*.nc'))
    
    # 读取所有nc文件
    datasets = []
    for nc_file in nc_files:
        ds = xr.open_dataset(nc_file)
        datasets.append(ds)
    
    # 计算平均值
    mean_ds = xr.concat(datasets, dim='file').mean(dim='file')
    
    # 保存结果

    mean_ds.to_netcdf(output_path)
    
    # 关闭所有数据集
    for ds in datasets:
        ds.close()
    
    return output_path


def merge_nc_files(file_list, output_file):

    #合并多个 NetCDF 文件，把其中的变量合并到同一个 Dataset 中。

    try:
        # 逐个打开文件
        ds_list = [xr.open_dataset(f) for f in file_list]
        
        # 合并所有变量
        ds_merged = xr.merge(ds_list, compat="no_conflicts")  
        # compat="no_conflicts" 表示维度坐标要一致，否则报错

        # 保存到新的文件
        ds_merged.to_netcdf(output_file)

        # 关闭文件
        for ds in ds_list:
            ds.close()

        print(f"success: {output_file}")
        return True

    except Exception as e:
        print(f"error: {str(e)}")
        return False



#输入有关文件路径

cmip6_s_files = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_s_resample_mean_slope/"
cmip6_d_files = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_d_resample_mean_slope/"
cmip6_r_files = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_r_resample_mean_slope/"

mean_cmip6_s_output = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_s_all_models_mean_slope.nc"
mean_cmip6_d_output = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_d_all_models_mean_slope.nc"
mean_cmip6_r_output = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_r_all_models_mean_slope.nc"
        
#era5 = ["/data1/yyzhao/data/1980-2020/finally_result/data/ERA5_s_d_mean_slope_noarea.nc","/data1/yyzhao/data/1980-2020/finally_result/data/ERA5_r_mean_slope_noarea.nc"]
#cru = ["/data1/yyzhao/data/1980-2020/finally_result/data/CRU_s_d_mean_slope_noarea.nc","/data1/yyzhao/data/1980-2020/finally_result/data/CRU_r_mean_slope_noarea.nc"]

era5 = ["/data1/yyzhao/data/1980-2020/finally_result/data/ERA5_s_d_mean_slope.nc","/data1/yyzhao/data/1980-2020/finally_result/data/ERA5_r_mean_slope.nc"]
cru = ["/data1/yyzhao/data/1980-2020/finally_result/data/CRU_s_d_mean_slope.nc","/data1/yyzhao/data/1980-2020/finally_result/data/CRU_r_mean_slope.nc"]

cmip6 = [mean_cmip6_s_output,mean_cmip6_d_output,mean_cmip6_r_output]

#era5_output = "/data1/yyzhao/data/1980-2020/finally_result/data/ERA5_s_d_r_mean_slope_noarea.nc"
#cru_output = "/data1/yyzhao/data/1980-2020/finally_result/data/CRU_s_d_r_mean_slope_noarea.nc"
#mean_cmip6_output = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_s_d_r_all_models_mean_slope_noarea.nc"

era5_output = "/data1/yyzhao/data/1980-2020/finally_result/data/ERA5_s_d_r_mean_slope.nc"
cru_output = "/data1/yyzhao/data/1980-2020/finally_result/data/CRU_s_d_r_mean_slope.nc"
mean_cmip6_output = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_s_d_r_all_models_mean_slope.nc"




#调用函数
calculate_nc_mean(cmip6_s_files,mean_cmip6_s_output)
calculate_nc_mean(cmip6_d_files,mean_cmip6_d_output)
calculate_nc_mean(cmip6_r_files,mean_cmip6_r_output)
merge_nc_files(era5, era5_output)
merge_nc_files(cru, cru_output)
merge_nc_files(cmip6, mean_cmip6_output)




