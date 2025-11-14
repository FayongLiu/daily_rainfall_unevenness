# -*- coding: utf-8 -*-
import xarray as xr
import os
import pandas as pd
import numpy as np
import time
import gc
import re
from multiprocessing import Pool, cpu_count
from pre_isd_select_valid_station import START_YEAR, END_YEAR, TH_YEAR

model_ls = ["ACCESS-CM2_day", "ACCESS-ESM1-5_day", "AWI-ESM-1-1-LR_day", "AWI-ESM-1-REcoM_day",
            "BCC-ESM1", "CanESM5_day", "CESM2-FV2_day", "CESM2-WACCM-FV2_day",
            "CESM2-WACCM_day", "CESM2", "CMCC-CM2-HR4_day", "CMCC-CM2-SR5_day",
            "CMCC-ESM2_day", "EC-Earth3-CC_day", "FGOALS-g3_day", "GISS-E2-2-G_day",
            "IITM-ESM_day", "MIROC6_day", "MPI-ESM-1-2-HAM_day", "MPI-ESM1-2-HR_day",
            "MPI-ESM1-2-LR_day", "NorCPM1", "NorESM2-LM_day", "NorESM2-MM_day", "SAM0-UNICON_day"]


def process_file(nc_file):
    """
    Function to calculate the maximum annual precipitation of a single file.
    """
    # Extract year from filename
    match = re.search(r'(\d{4})', os.path.basename(nc_file))
    if match:
        year = int(match.group(1))
        print(f"Processing year of {year}")
    else:
        raise ValueError(f"Year not found in filename: {nc_file}")

    ds = xr.open_dataset(nc_file)
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
    valid_mask = prcp.count(dim='time')
    total_count = len(prcp['time'])
    valid_mask = valid_mask >= total_count * 0.75
    annual_prcp = prcp.sum(dim='time', skipna=True)
    annual_prcp = annual_prcp.where(valid_mask)
    max_prcp = annual_prcp.max().item()

    print(f"Finished year {year}, maximum annual precipitation {max_prcp:.2f} mm")

    del ds, prcp, valid_mask, annual_prcp
    gc.collect()

    return year, max_prcp


def compute_max_precipitation(data_folder, dataname, num_processes=10):
    """
    Compute the maximum annual precipitation for all files using multiprocessing.
    """
    print(f'Processing {dataname}')
    # Get all NetCDF file paths
    files = []
    for f in os.listdir(data_folder):
        match = re.search(r'\d{4}', f)
        if match and f.endswith('.nc'):
            year = int(match.group())
            if START_YEAR <= year <= END_YEAR:
                files.append(os.path.join(data_folder, f))

    if not files:
        raise FileNotFoundError(f"No NetCDF files found in {data_folder}")

    # Use multiprocessing to process files in parallel
    num_processes = min(num_processes, cpu_count())
    with Pool(processes=num_processes) as pool:
        results = pool.map(process_file, files)

    # Convert results to a DataFrame
    results.sort(key=lambda x: x[0])  # Sort by year
    df = pd.DataFrame(results, columns=['year', 'annual_prcp_mm'])

    # Ensure output directory exists
    output_file = rf'../data/max_annual_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{dataname}.csv'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)

    print(f"Results saved to {output_file}")

    return


if __name__ == "__main__":
    t1 = time.time()
    
    # CMIP6 models
    data_dir = r'/data1/jzzhou/precipitation/season/cmip6/'
    for model in model_ls:
        data_folder = os.path.join(data_dir, model)
        compute_max_precipitation(data_folder, model, num_processes=21)

    # CRU JRA
    data_folder = r'/data1/yyzhao/data/CRU-JRA/pre/'
    compute_max_precipitation(data_folder, 'CRU_JRA', num_processes=21)
    
    # ERA5_Land
    data_folder = r'/data1/share/ERA5_land/precipitation/daily/'
    compute_max_precipitation(data_folder, 'ERA5_Land', num_processes=4)
    
    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")