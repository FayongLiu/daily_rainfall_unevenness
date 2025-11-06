# -*- coding: utf-8 -*-
import xarray as xr
import numpy as np
from scipy.stats import linregress
import time
import os  
    
t1 = time.time()
# Load the NetCDF file
#file_path = "/data1/yyzhao/data/1980-2020/finally_result/data/ERA5_s_d_noarea.nc"
file_path = "/data1/yyzhao/data/1980-2020/finally_result/data/ERA5_s_d.nc"
data = xr.open_dataset(file_path)

S_daily = data["S_daily"]
S_monthly = data["S_monthly"]
D_daily = data["D_daily"]
D_monthly = data["D_monthly"]

# Define a function to calculate the linear trend and p-value
def linear_fit(y, x_values):
    if np.all(np.isnan(y)):
        return np.nan, np.nan
    mask = ~np.isnan(y)
    if np.sum(mask) < 2:  # 至少需要2个有效点
        return np.nan, np.nan
    slope, _, _, p_value, _ = linregress(x_values[mask], y[mask])
    return slope, p_value


# Calculate the multi-year mean
print("Strat cal multiyear average of S")
S_daily_mean = S_daily.mean(dim="time", skipna=True)
S_monthly_mean = S_monthly.mean(dim="time", skipna=True)
print("Finish cal multiyear average of S")

print("Strat cal multiyear average of D")
D_daily_mean = D_daily.mean(dim="time", skipna=True)
D_monthly_mean = D_monthly.mean(dim="time", skipna=True)
print("Finish cal multiyear average of D")

# Extract time values for trend calculation
x_values = data['time'].values

# Calculate trend for S_daily
print("Start cal multiyear trend of S")
s_daily_result = xr.apply_ufunc(
    linear_fit,
    S_daily,
    input_core_dims=[['time']],
    output_core_dims=[[], []],
    vectorize=True,
    dask='parallelized',
    output_dtypes=[float, float],
    kwargs={'x_values': x_values}
)
s_slope_daily, s_p_values_daily = s_daily_result[0], s_daily_result[1]

# Calculate trend for S_monthly
s_monthly_result = xr.apply_ufunc(
    linear_fit,
    S_monthly,
    input_core_dims=[['time']],
    output_core_dims=[[], []],
    vectorize=True,
    dask='parallelized',
    output_dtypes=[float, float],
    kwargs={'x_values': x_values}
)

s_slope_monthly, s_p_values_monthly = s_monthly_result[0], s_monthly_result[1]
print("Finish cal multiyear trend of S")

# Calculate trend for D_daily
print("Start cal multiyear trend of D")
d_daily_result = xr.apply_ufunc(
    linear_fit,
    D_daily,
    input_core_dims=[['time']],
    output_core_dims=[[], []],
    vectorize=True,
    dask='parallelized',
    output_dtypes=[float, float],
    kwargs={'x_values': x_values}
)
d_slope_daily, d_p_values_daily = d_daily_result[0], d_daily_result[1]

# Calculate trend for D_monthly
d_monthly_result = xr.apply_ufunc(
    linear_fit,
    D_monthly,
    input_core_dims=[['time']],
    output_core_dims=[[], []],
    vectorize=True,
    dask='parallelized',
    output_dtypes=[float, float],
    kwargs={'x_values': x_values}
)

d_slope_monthly, d_p_values_monthly = d_monthly_result[0], d_monthly_result[1]
print("Finish cal multiyear trend of D")

# Combine all results into a new Dataset
result_dataset = xr.Dataset(
    {
        "S_daily_mean": S_daily_mean,
        "S_monthly_mean": S_monthly_mean,
        "S_daily_trend": s_slope_daily,
        "S_daily_p_value": s_p_values_daily,
        "S_monthly_trend": s_slope_monthly,
        "S_monthly_p_value": s_p_values_monthly,
        "D_daily_mean" : D_daily_mean,
        "D_monthly_mean" : D_monthly_mean,
        "D_daily_trend" : d_slope_daily,
        "D_daily_p_value" : d_p_values_daily,
        "D_monthly_trend" : d_slope_monthly,
        "D_monthly_p_value" : d_p_values_monthly
    }
)

# Save the results to a new NetCDF file
output_path = r"/data1/yyzhao/data/1980-2020/finally_result/data/ERA5_s_d_mean_slope.nc"
result_dataset.to_netcdf(output_path)

t2 = time.time()
print(f"Results saved to: {output_path}, running time {t2-t1} s")
