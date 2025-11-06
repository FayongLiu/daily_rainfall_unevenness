# -*- coding: utf-8 -*-
import xarray as xr
import numpy as np
import os
from multiprocessing import Pool, cpu_count
from functools import partial
import gc
import time
import pandas as pd
import re
## read the maximum precipitation 
maximum =  pd.read_csv("/data1/ZhouJZ/precipitation/season/cmip6/maximum/results.csv",encoding="utf-8")

# Functions to calculate seasonality indices
def calculate_seasonality_index(ds):
    """
    Calculate daily and monthly seasonality index (S) for each grid point using xarray.
    Args:
        ds (xarray.Dataset): Dataset containing precipitation data
    Returns:
        xarray.DataArray: Daily seasonality index for each grid point
    """
    #if not np.issubdtype(ds['time'].dtype, np.datetime64):
    #    ds['time'] = pd.to_datetime(ds['time'].values)  # Convert to datetime64
    #    ds['time'] = xr.DataArray(ds['time'], dims='time')

    
    # max annual precipitation (mm) among all grids during 1950-2023
    Rmax = maximum.loc[maximum['Model'] == model, 'MaxPrecipitation'].iloc[0]
    precipitation = ds['pr']*86400  # Precipitation data (time, lat, lon)
    precipitation = precipitation.where(precipitation>=0, 0)
    R = precipitation.sum(dim='time', skipna=True)  # Total precipitation for each grid point
    
    # Avoid division by zero
    valid = R > 0
    
    r_rmax = R/Rmax
    r_rmax = r_rmax.where(valid, np.nan)
    
    del precipitation, R, valid
    gc.collect()
    
    return r_rmax



# Function to process a single NetCDF file and save results
def process_and_save(file_path, output_dir):
    """
    Process a single NetCDF file to compute daily and monthly seasonality indices for all grid points.
    Args:
        file_path (str): Path to the NetCDF file
    Returns:
        xarray.Dataset: Dataset containing daily and monthly seasonality indices
    """
    
    print(f"Start processing: {file_path}")
    
    t1 = time.time()
    
    # Open the NetCDF file
    ds = xr.open_dataset(file_path,decode_times=True)

    # Compute daily and monthly seasonality indices
    r_rmax = calculate_seasonality_index(ds)

    # add time info
    #year = int(file_path[-7:-3])
    match =re.search(rf'{model}_(\d{{4}})\.nc', os.path.basename(file_path))
    year = int(match.group(1))

    time_info = xr.DataArray([year], dims=["time"], coords={"time": [year]}, name="time")
    r_rmax = r_rmax.expand_dims(dim='time').assign_coords(time=time_info)
    
    # Combine results into a new Dataset
    result_ds = xr.Dataset({
        'r_rmax': r_rmax
    })

    # Save the result to a NetCDF file
    filename = os.path.basename(file_path).replace('.nc', '.nc')
    output_path = os.path.join(output_dir, filename)
    result_ds.to_netcdf(output_path)
    
    t2 = time.time()
    running_time = t2-t1
    
    print(f"Processed and saved: {output_path}, running time = {running_time}s")
    
    ds.close()
    del ds, r_rmax, result_ds
    gc.collect()
    
    return
    
    
    
# Function to process files in parallel
def process_files_in_parallel(input_dir, output_dir, num_workers=None):
    """
    Process all NetCDF files in a directory in parallel to compute seasonality indices.
    Args:
        input_dir (str): Directory containing NetCDF files
        output_dir (str): Directory to save output files
        num_workers (int): Number of parallel workers (default: number of CPUs)
    """
    # Find all NetCDF files in the input directory
    files = []
    for f in os.listdir(input_dir):
        match =re.search(rf'{model}_(\d{{4}})\.nc', f)
        year = int(match.group(1))
        if year >= 1980:
            files.append(os.path.join(input_dir, f))

    if not files:
        raise FileNotFoundError(f"No NetCDF files found in {input_dir}")

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Use multiprocessing to process files in parallel
    num_workers = min(num_workers, cpu_count())
    print(f"Processing {len(files)} files using {num_workers} workers...")

    # Use a multiprocessing pool to process files
    process_and_save_with_fixed_output_dir = partial(process_and_save, output_dir=output_dir)
    with Pool(processes=num_workers) as pool:
        pool.map(process_and_save_with_fixed_output_dir, files)



# Main function
if __name__ == "__main__":
    models=["ACCESS-CM2_day", "BCC-ESM1", "CMCC-CM2-HR4_day", "IITM-ESM_day", "NorCPM1",
    "ACCESS-ESM1-5_day", "CMCC-CM2-SR5_day", "MIROC6_day", "NorESM2-LM_day",
    "CanESM5_day", "CMCC-ESM2_day", "MPI-ESM-1-2-HAM_day", "NorESM2-MM_day",
    "CESM2", "EC-Earth3-CC_day", "MPI-ESM1-2-HR_day", "AWI-ESM-1-1-LR_day",
    "CESM2-FV2_day", "FGOALS-g3_day", "MPI-ESM1-2-LR_day", "SAM0-UNICON_day",
    "AWI-ESM-1-REcoM_day", "CESM2-WACCM_day", "GISS-E2-2-G_day", "MRI-ESM2-0_day", "TaiESM1_day",
    "CESM2-WACCM-FV2_day", "ICON-ESM-LR_day"]
    # Define input and output directories
    input_dirct = r"/data1/ZhouJZ/precipitation/season/cmip6/"
    output_dirct = r"/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_r/"
    for model in models:
    # Process all files in parallel
        input_dir = os.path.join(input_dirct, model)
        output_dir = os.path.join(output_dirct, model)
        process_files_in_parallel(input_dir, output_dir, 35)