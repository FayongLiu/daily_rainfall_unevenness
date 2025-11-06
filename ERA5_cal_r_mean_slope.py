# -*- coding: utf-8 -*-
import os
import re
import numpy as np
import xarray as xr
from scipy.stats import linregress

# 文件路径设置
area_file = '/data1/fyliu/c_temperature_variability/data/area_bio_cli_mask/area_mask/area_0.1deg.nc'
input_dir = "/data1/share/ERA5_land/precipitation/daily/"
output_dir = "/data1/yyzhao/data/1980-2020/finally_result/data/"
#output_filename = 'ERA5_r_mean_slope_noarea.nc'
output_filename = 'ERA5_r_mean_slope.nc'
# 加载区域面积数据
area_ds = xr.open_dataset(area_file)
area = area_ds['area']
area_lat = area_ds['lat']
area_lon = area_ds['lon']

# 筛选1980–2020年内的nc文件
nc_files = []
for f in os.listdir(input_dir):
    if f.endswith('.nc') and re.match(r'precipitation_daily_(\d{4})\.nc', f):
        year = int(re.search(r'precipitation_daily_(\d{4})\.nc', f).group(1))
        if 1980 <= year <= 2020:
            nc_files.append((year, os.path.join(input_dir, f)))

if not nc_files:
    raise FileNotFoundError(f"No valid nc files found in {input_dir}")

print(f"Total files to process: {len(nc_files)}")

# 步骤 1：获取最大年总降水
max_annual_precipitation = 0.0
for year, file_path in nc_files:
    with xr.open_dataset(file_path) as ds:
        if 'tp' not in ds:
            print(f"Warning: 'tp' not found in {file_path}, skipping...")
            continue
        precipitation = ds['tp'].where(ds['tp'] >= 0, 0)
        annual_sum = precipitation.sum(dim='time', skipna=True)
        file_max = float(annual_sum.max(skipna=True).values)
        max_annual_precipitation = max(max_annual_precipitation, file_max)
print(f"Global max annual precipitation: {max_annual_precipitation}")

# 步骤 2–4：计算每年每网格r值，并合并成时间序列
r_datasets = []
for year, file_path in nc_files:
    with xr.open_dataset(file_path) as ds:
        if 'tp' not in ds:
            continue
        ds = ds.rename({'latitude': 'lat', 'longitude': 'lon'})
        precipitation = ds['tp'].where(ds['tp'] >= 0, 0)
        annual_sum = precipitation.sum(dim='time', skipna=True)
        r = annual_sum / max_annual_precipitation
        raw_ds = xr.Dataset(
            data_vars={'R_ratio': r},
            coords={'lat': r['lat'], 'lon': r['lon']}
        )
        raw_ds = raw_ds.expand_dims(time=[year])
        r_datasets.append(raw_ds)

# 合并时间维度
combined_raw_ds = xr.concat(r_datasets, dim='time')
combined_raw_ds = combined_raw_ds.sortby('time')

# 步骤 5：重采样（插值）到area数据的经纬度网格
interpolated_ds = combined_raw_ds.interp({'lat': area_lat, 'lon': area_lon}, method='linear')
data = combined_raw_ds['R_ratio']
area = area.assign_coords(lat=data['lat'], lon=data['lon'])
# 步骤 6：面积加权
valid_mask = ~np.isnan(data.isel(time=0))
total_area = area.where(valid_mask).sum()
weighted_data = data * area / total_area

# 构建最终数据集
result_ds = xr.Dataset({'R_ratio': weighted_data})
#result_ds = xr.Dataset({'R_ratio': data})

#计算mean和slope
def linear_fit(y, x_values):
    if np.all(np.isnan(y)):
        return np.nan, np.nan
    mask = ~np.isnan(y)
    if np.sum(mask) < 2:  # 至少需要2个有效点
        return np.nan, np.nan
    slope, _, _, p_value, _ = linregress(x_values[mask], y[mask])
    return slope, p_value

print("Strat cal multiyear average of R_ratio")
R_ratio_mean = weighted_data.mean(dim="time", skipna=True)
#R_ratio_mean = data.mean(dim="time", skipna=True)    
print("Finish cal multiyear average of R_ratio")

x_values = result_ds['time'].values

# Calculate trend for S_daily
print("Start cal multiyear trend of R_ratio")
R_ratio_result = xr.apply_ufunc(
    linear_fit,
    data,
    input_core_dims=[['time']],
    output_core_dims=[[], []],
    vectorize=True,
    dask='parallelized',
    output_dtypes=[float, float],
    kwargs={'x_values': x_values}
)
R_ratio_slope, R_ratio_p_values = R_ratio_result[0], R_ratio_result[1]

# Combine all results into a new Dataset
result_dataset = xr.Dataset(
    {
        "R_ratio_mean": R_ratio_mean,
        "R_ratio_slope": R_ratio_slope,
        "R_ratio_p_values": R_ratio_p_values
    }
)


# 保存结果
output_path = os.path.join(output_dir, output_filename)
print(f"Saving to {output_path}")
result_dataset.to_netcdf(output_path)

print("Finished.")
