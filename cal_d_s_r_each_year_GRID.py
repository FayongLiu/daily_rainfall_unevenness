# Code for calculating rainfall unevenness for grids of each year
import xarray as xr
import numpy as np
import pandas as pd
import os
from multiprocessing import Pool, cpu_count
import gc
import re
import time
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.datainfo import DATA_LS_80, DATA_LS_50, DATAPATHS, RESOLUTIONS, CMIP6_LS
from rainfall_ui.preprocess.preprocess_station import get_total_days


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr
DATA_LS = DATA_LS_80 if START_YEAR >= 1980 else DATA_LS_50


# functions to calculate unevenness indices
def cal_D_S_Ratio(file_path, Rmax, land_mask=None):
    """
    Calculate daily and monthly seasonality index (S) for each grid point using xarray.
    """

    # Open the NetCDF file
    ds = xr.open_dataset(file_path)
    # Standardize latitude and longitude coordinate names
    if 'latitude' in ds.coords:
        ds = ds.rename({'latitude': 'lat', 'longitude': 'lon'})
    if 'latitude' in ds.dims:
        ds = ds.rename_dims({'latitude': 'lat', 'longitude': 'lon'})
    ds['lon'] = xr.where(ds['lon'] > 180, ds['lon'] - 360, ds['lon'])
    ds = ds.sortby('lon').sortby('lat').sortby('time')

    try:
        if 'tp' in ds:
            prcp = ds['tp']
        elif 'pre' in ds:
            prcp = ds['pre']
        elif 'pr' in ds:
            prcp = ds['pr'] * 86400  # convet unit to mm day-1
        elif 'precip' in ds:
            prcp = ds['precip']
        elif 'p' in ds:
            prcp = ds['p']
        elif 'prcp' in ds:
            prcp = ds['prcp']
        else:
            raise KeyError("Dataset does not contain 'tp' or 'pre' variable")

        if land_mask is not None:
            prcp['lon'] = prcp['lon'].astype('float32')
            prcp['lat'] = prcp['lat'].astype('float32')
            prcp = prcp.where(land_mask)
        prcp = xr.where(prcp < 0.1, 0, prcp)
        prcp = prcp.where(prcp >= 0, np.nan)
        R = prcp.sum(dim='time', skipna=True)  # Total prcp for each grid point
        valid_mask = prcp.count(dim='time')
        total_count = get_total_days(prcp['time.year'].values[0])
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
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        S_daily = None
        S_monthly = None
        D_daily = None
        D_monthly = None
        PRCP_ratio = None
        rain_day = None
    
    ds.close()
    del ds
    gc.collect()

    return S_daily, S_monthly, D_daily, D_monthly, PRCP_ratio, rain_day


# function to process a single NetCDF file and save results
def process_and_save(file_path, output_dir, Rmax, dataname, overwirte):
    """
    Process a single NetCDF file to compute daily and monthly seasonality indices for all grid points.
    Args:
        file_path (str): Path to the NetCDF file
    Returns:
        None
    """

    os.makedirs(output_dir, exist_ok=True)
    match = re.findall(r'(\d{4})', os.path.basename(file_path))
    if match:
        year = int(match[-1])
        print(f"Processing year of {year}")
    else:
        raise ValueError(f"Year not found in filename: {file_path}")
    
    filename = f's_d_ratio_{year}.nc'
    output_path = os.path.join(output_dir, filename)

    if os.path.exists(output_path) and not overwirte:
        print(f'{output_path} already exists, skip...')

        return
    else:
        if not os.path.exists(output_path):
            print(f'{output_path} does not exist, calculating...')
        else:
            print(f'{output_path} already exists, overwriting...')
    
    # Get land mask
    if dataname in CMIP6_LS:
        land_mask_path = rf'../data/mask/land_mask_{dataname}.nc'
        land_mask = xr.open_dataset(land_mask_path)['land']
        land_mask['lon'] = land_mask['lon'].astype('float32')
        land_mask['lat'] = land_mask['lat'].astype('float32')
    else:
        land_mask = None

    # Compute daily and monthly seasonality indices
    S_daily, S_monthly, D_daily, D_monthly, PRCP_ratio, rain_day = cal_D_S_Ratio(file_path, Rmax, land_mask)
    if S_daily is not None:
        # Add time info
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
        result_ds.to_netcdf(output_path)
        print(f"Results saved to {output_path}")

        del result_ds
        gc.collect()

    return


# function to process files in parallel
def process_files_in_parallel(input_dir, dataname, num_workers, overwrite):
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
        match = re.findall(r'(\d{4})', f)
        if match and f.endswith('.nc'):
            year = int(match[-1])
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
        pool.starmap(process_and_save, [(file_path, output_dir, Rmax, dataname, overwrite) for file_path in files])

    return


# Main function
if __name__ == "__main__":
    
    t1 = time.time()

    for dataname in DATA_LS:
        data_folder = DATAPATHS[dataname]
        resolution = RESOLUTIONS[dataname]
        if resolution >= 0.5:
            num_processes = 42
        elif resolution >= 0.1 and resolution < 0.5:
            num_processes = 6
        else:
            num_processes = 3
        process_files_in_parallel(data_folder, dataname, num_processes, OVERWRITE)

    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")

