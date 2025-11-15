# -*- coding: utf-8 -*-
import os
import gc
import xarray as xr
import numpy as np
from scipy.stats import linregress
import time
from multiprocessing import Pool, cpu_count
from pre_isd_select_valid_station import START_YEAR, END_YEAR, TH_YEAR
from pre_GRID_cal_maximum_annual_prcp import model_ls


# function to calculate the linear trend and p-value
def linear_fit(y_values, x_values):
    mask = ~np.isnan(y_values)
    if np.sum(mask) < 2:
        return np.nan, np.nan

    x_mask = x_values[mask]
    y_mask = y_values[mask]
    slope, _, _, p_value, _ = linregress(x_mask, y_mask)

    return slope, p_value


# function to cal multi-year mean and trend at each grid
def cal_mean_trend_GRID(data_name):
    print(f'Process {data_name}')
    indir =  rf'../data/d_s_ratio/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{data_name}'
    # concat all nc data
    filename_ls = os.listdir(indir)
    filename_ls.sort()
    ds_ls = []
    for f in filename_ls:
        if f.endswith('.nc'):
            ds = xr.open_dataset(os.path.join(indir, f))
            ds_ls.append(ds)
    all_ds = xr.concat(ds_ls, dim='time')
    print('Finish concatenating all nc file')
    if data_name not in ['CRU_JRA', 'ERA5_Land']:
        # resample CMIP6 models into the resolution of CRU JRA
        ref_path = rf'../data/d_s_ratio/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/CRU_JRA/s_d_ratio_{START_YEAR}.nc'
        ref_ds = xr.open_dataset(ref_path)['S_daily'].isel(time=0)
        ref_ds = ref_ds.sortby('lat').sortby('lon')
        all_ds['lon'] = xr.where(all_ds['lon'] > 180, all_ds['lon'] - 360, all_ds['lon'])
        all_ds = all_ds.sortby('lat').sortby('lon')
        template = xr.Dataset(coords={'lat': ref_ds['lat'], 'lon': ref_ds['lon']})
        all_ds = all_ds.interp_like(template, method='linear')
        all_ds = all_ds.where(~np.isnan(ref_ds))

    varname_ls = ['S_daily', 'S_monthly', 'D_daily', 'D_monthly', 'PRCP_ratio', 'rain_day']
    mean_trend = {}
    for varname in varname_ls:
        print(f'Calculate mean and trend of {varname}')
        # 2000-2020
        var_ds = all_ds[varname]
        valid_mask = var_ds.count(dim='time')
        total_count = len(var_ds['time'])
        valid_mask = valid_mask >= np.floor(total_count * 0.75)
        mean = var_ds.mean(dim='time', skipna=True)
        x_values = var_ds['time'].values
        result = xr.apply_ufunc(
            linear_fit,
            var_ds,
            input_core_dims=[['time']],
            output_core_dims=[[], []],
            vectorize=True,
            dask='parallelized',
            output_dtypes=[float, float],
            kwargs={'x_values': x_values}
        )
        slope, p_value = result[0], result[1]
        mean_trend[f'{varname}_mean'] = mean.where(valid_mask)
        mean_trend[f'{varname}_trend'] = slope.where(valid_mask)
        mean_trend[f'{varname}_p_value'] = p_value.where(valid_mask)

        del var_ds, valid_mask, mean, result, slope, p_value
        gc.collect()

    print(f'Finish calculating mean and trend')
    result_ds = xr.Dataset(mean_trend)
    outpath = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/grid_{data_name}.nc'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    result_ds.to_netcdf(outpath)
    print(f'Saving {outpath}')

    del ds_ls, all_ds, mean_trend, result_ds
    gc.collect()

    return


def main():
    data_name_ls = model_ls + ['CRU_JRA', 'ERA5_Land']
    num_workers = min(27, cpu_count())
    with Pool(num_workers) as pool:
        pool.map(cal_mean_trend_GRID, data_name_ls)

    return


if __name__ == "__main__":
    t1 = time.time()
    main()
    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")