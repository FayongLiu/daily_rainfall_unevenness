# -*- coding: utf-8 -*-
import xarray as xr
import numpy as np
import pandas as pd
import os
from multiprocessing import Pool, cpu_count
import gc
import re
import time
from pre_isd_select_valid_station import START_YEAR, END_YEAR, TH_YEAR
from pre_GRID_cal_maximum_annual_prcp import model_ls


# functions to calculate unevenness indices
def cal_D_S_Ratio(ds, Rmax):
    """
    Calculate daily and monthly seasonality index (S) for each grid point using xarray.
    Args:
        ds (xarray.Dataset): Dataset containing prcp data
        Rmax (float): max annual prcp (mm) among all grids during 1980-2020
    Returns:
        xarray.DataArray: Daily seasonality index for each grid point
    """
    if 'tp' in ds:
        prcp = ds['tp']
    elif 'pre' in ds:
        prcp = ds['pre']
    elif 'pr' in ds:
        prcp = ds['pr'] * 86400  # convet unit to mm day-1
    else:
        raise KeyError("Dataset does not contain 'tp' or 'pre' variable")
    prcp = xr.where(prcp < 0.1, 0, prcp)
    prcp = prcp.where(prcp >= 0, np.nan)
    R = prcp.sum(dim='time', skipna=True)  # Total prcp for each grid point
    valid_mask = prcp.count(dim='time')
    total_count = len(prcp['time'])
    valid_mask = valid_mask >= total_count * 0.75

    # cal daily UI
    rain_mask = prcp > 0
    rain_day = rain_mask.sum(dim='time')
    m = prcp.count(dim='time')  # Number of not nan values at time dimension
    q = 1 / m  # Average proportion q
    # Avoid division by zero
    annual_rain_gt0_mask = R > 0
    pi = xr.where(annual_rain_gt0_mask, prcp / R, 0)  # Proportion of prcp (pi)
    # Compute seasonality index D
    D_daily = xr.where(pi > 0, (pi * np.log2(pi / q)), 0)
    D_daily = D_daily.sum(dim='time', skipna=True)
    D_daily = D_daily.where(valid_mask, np.nan)
    PRCP_ratio = R / Rmax
    PRCP_ratio = PRCP_ratio.where(valid_mask, np.nan)
    S_daily = D_daily * PRCP_ratio
    S_daily = S_daily.where(valid_mask, np.nan)

    # cal monthly seasonality index
    prcp_monthly = prcp.resample(time='1ME').sum(dim='time', skipna=True)  # Monthly total prcp
    m = prcp_monthly.count(dim='time')
    q = 1 / m
    # Avoid division by zero
    pi = xr.where(annual_rain_gt0_mask, prcp_monthly / R, 0)  # Proportion of prcp (pi)
    # Compute seasonality index D
    D_monthly = xr.where(pi > 0, (pi * np.log2(pi / q)), 0)
    D_monthly = D_monthly.sum(dim='time', skipna=True)
    D_monthly = D_monthly.where(valid_mask, np.nan)
    S_monthly = D_monthly * PRCP_ratio
    S_monthly = S_monthly.where(valid_mask, np.nan)

    rain_day = rain_day.where(valid_mask, np.nan)

    del prcp, R, valid_mask, rain_mask, annual_rain_gt0_mask, m, q, pi
    gc.collect()

    return S_daily, S_monthly, D_daily, D_monthly, PRCP_ratio, rain_day


# function to process a single NetCDF file and save results
def process_and_save(file_path, output_dir, Rmax):
    """
    Process a single NetCDF file to compute daily and monthly seasonality indices for all grid points.
    Args:
        file_path (str): Path to the NetCDF file
    Returns:
        None
    """
    print(f"Start processing: {file_path}")

    # Open the NetCDF file
    ds = xr.open_dataset(file_path)
    # Standardize latitude and longitude coordinate names
    if 'latitude' in ds.coords:
        ds = ds.rename({'latitude': 'lat', 'longitude': 'lon'})
    if 'latitude' in ds.dims:
        ds = ds.rename_dims({'latitude': 'lat', 'longitude': 'lon'})
    ds['lon'] = xr.where(ds['lon'] > 180, ds['lon'] - 360, ds['lon'])
    ds = ds.sortby('lon').sortby('lat')

    # Compute daily and monthly seasonality indices
    S_daily, S_monthly, D_daily, D_monthly, PRCP_ratio, rain_day = cal_D_S_Ratio(ds, Rmax)

    # Add time info
    match = re.search(r'\d{4}', os.path.basename(file_path))
    year = int(match.group())
    time_info = xr.DataArray([year], dims=["time"], coords={"time": [year]}, name="time")

    # List of variables to expand
    variables = [S_daily, S_monthly, D_daily, D_monthly, PRCP_ratio, rain_day]
    expanded_vars = {name: var.expand_dims(dim='time').assign_coords(time=time_info)
                     for name, var in
                     zip(['S_daily', 'S_monthly', 'D_daily', 'D_monthly', 'PRCP_ratio', 'rain_day'],
                         variables)}

    # Combine results into a new Dataset
    result_ds = xr.Dataset(expanded_vars)

    # Save the result to a NetCDF file
    filename = f's_d_ratio_{year}.nc'
    output_path = os.path.join(output_dir, filename)
    result_ds.to_netcdf(output_path)

    # Cleanup
    ds.close()
    del ds, result_ds
    gc.collect()

    return


# function to process files in parallel
def process_files_in_parallel(input_dir, dataname, num_workers=10):
    """
    Process all NetCDF files in a directory in parallel to compute seasonality indices.
    Args:
        input_dir (str): Directory containing NetCDF files
        dataname (str): dataset name
        num_workers (int): Number of parallel workers (default: number of CPUs)
    """
    # load maximum precipitation
    Rmax_path = rf'../data/max_annual_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{dataname}.csv'
    Rmax = pd.read_csv(Rmax_path, usecols=['annual_prcp_mm'])
    Rmax = Rmax.max().item()
    print(f'maximum annual precipitation: {Rmax} mm')

    # Find all NetCDF files in the input directory
    files = []
    for f in os.listdir(input_dir):
        match = re.search(r'\d{4}', f)
        if match and f.endswith('.nc'):
            year = int(match.group())
            if START_YEAR <= year <= END_YEAR:
                files.append(os.path.join(input_dir, f))

    if not files:
        raise FileNotFoundError(f"No NetCDF files found in {input_dir}")

    # Ensure the output directory exists
    output_dir = rf'../data/d_s_ratio/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{dataname}/'
    os.makedirs(output_dir, exist_ok=True)

    # Use a multiprocessing pool to process files
    num_workers = min(num_workers, cpu_count())
    with Pool(processes=num_workers) as pool:
        pool.starmap(process_and_save, [(file_path, output_dir, Rmax) for file_path in files])


# Main function
if __name__ == "__main__":
    t1 = time.time()
    
    # ERA5_Land
    input_dir = r"/data1/share/ERA5_land/precipitation/daily/"
    process_files_in_parallel(input_dir, 'ERA5_Land', num_workers=3)

    # CMIP6 models
    data_dir = r'/data1/jzzhou/precipitation/season/cmip6/'
    for model in model_ls:
        input_dir = os.path.join(data_dir, model)
        process_files_in_parallel(input_dir, model, num_workers=21)

    # CRU JRA
    input_dir = r"/data1/yyzhao/data/CRU-JRA/pre/"
    process_files_in_parallel(input_dir, 'CRU_JRA', num_workers=21)

    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")