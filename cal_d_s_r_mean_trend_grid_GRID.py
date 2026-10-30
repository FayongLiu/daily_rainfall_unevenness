# Calculate multi-year mean and trend at each grid


import os
import gc
import xarray as xr
import numpy as np
from scipy.stats import linregress
import pymannkendall as mk
import time
from multiprocessing import Pool, cpu_count
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.datainfo import DATA_LS_80, DATA_LS_50


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr
DATA_LS = DATA_LS_80 if START_YEAR >= 1980 else DATA_LS_50


# function to calculate the linear trend and p-value
def linear_fit(y_values, x_values):
    mask = ~np.isnan(y_values)
    if np.sum(mask) < 10:
        return np.nan, np.nan

    x_mask = x_values[mask]
    y_mask = y_values[mask]
    slope, _, _, p_value, _ = linregress(x_mask, y_mask)

    return slope, p_value


# function to mk test
def mk_test(y_values, x_values):
    mask = ~np.isnan(y_values)
    if np.sum(mask) < 10:
        return np.nan, np.nan

    x_mask = x_values[mask]
    y_mask = y_values[mask]

    result = mk.original_test(y_mask)
    slope = result.slope
    p_value = result.p

    return slope, p_value


# function to cal multi-year mean and trend at each grid
def cal_mean_trend_GRID(data_name, overwrite):

    outpath = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/grid_{data_name}.nc'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    if os.path.exists(outpath) and not overwrite:
        print(f'File existed, {outpath}')
        return
    else:
        if not os.path.exists(outpath):
            print(f'File does not exist, {outpath}')
        else:
            print(f'File exists, overwriting {outpath}...')

    indir =  rf'../data/d_s_ratio/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{data_name}'
    # concat all nc data
    filename_ls = os.listdir(indir)
    filename_ls.sort()
    ds_ls = []
    for f in filename_ls:
        if f.endswith('.nc'):
            ds = xr.open_dataset(os.path.join(indir, f))
            ds_ls.append(ds)
    all_ds = xr.concat(ds_ls, dim='time').sortby('time')
    all_ds['lon'] = xr.where(all_ds['lon'] > 180, all_ds['lon'] - 360, all_ds['lon'])
    all_ds = all_ds.sortby('lat').sortby('lon')
    print('Finish concatenating all nc file')
    varname_ls = ['S_daily', 'S_monthly', 'D_daily', 'D_monthly', 'PRCP_ratio', 'rain_day']
    mean_trend = {}
    for varname in varname_ls:
        print(f'Calculate mean and trend of {varname}')
        var_ds = all_ds[varname]
        valid_mask = var_ds.count(dim='time')
        valid_mask = valid_mask >= 0.75*len(var_ds['time'])
        mean = var_ds.mean(dim='time', skipna=True)
        x_values = var_ds['time'].values
        result = xr.apply_ufunc(
            mk_test, #linear_fit,
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
    print(result_ds)
    result_ds.to_netcdf(outpath)
    print(f'Saving {outpath}')

    del ds_ls, all_ds, mean_trend, result_ds
    gc.collect()

    return


def main():
    num_workers = min(len(DATA_LS), cpu_count())
    with Pool(num_workers) as pool:
        pool.starmap(cal_mean_trend_GRID, [(data_name, OVERWRITE) for data_name in DATA_LS])

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