# Code to calculate the maximum annual precipitation of each year for each model and observation dataset
import xarray as xr
import os
import pandas as pd
import numpy as np
import time
import gc
import re
from multiprocessing import Pool, cpu_count
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


def process_file(nc_file, land_mask=None):
    """
    Function to calculate the maximum annual precipitation of a single file.
    """

    # Extract year from filename
    match = re.findall(r'(\d{4})', os.path.basename(nc_file))
    if match:
        year = int(match[-1])
        print(f"Processing year of {year}")
    else:
        raise ValueError(f"Year not found in filename: {nc_file}")
    try:
        ds = xr.open_dataset(nc_file)
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
            prcp['lon'] = xr.where(prcp['lon'] > 180, prcp['lon'] - 360, prcp['lon'])
            prcp = prcp.sortby('lat').sortby('lon')
            prcp['lon'] = prcp['lon'].astype('float32')
            prcp['lat'] = prcp['lat'].astype('float32')
            prcp = prcp.where(land_mask)
        prcp = xr.where(prcp < 0.1, 0, prcp)
        prcp = prcp.where(prcp >= 0, np.nan)
        valid_mask = prcp.count(dim='time')
        total_count = get_total_days(year)
        valid_mask = valid_mask >= total_count * 0.75
        annual_prcp = prcp.sum(dim='time', skipna=True)
        annual_prcp = annual_prcp.where(valid_mask)

        max_prcp = annual_prcp.max().item()

        del ds, prcp, valid_mask, annual_prcp
        gc.collect()
    except Exception as e:
        print(f"Error from {nc_file}: {e}")
        max_prcp = 0.0

    print(f"Finished year {year}, maximum annual precipitation {max_prcp:.2f} mm")

    return year, max_prcp


def compute_max_precipitation(data_folder, dataname, num_processes, overwrite):
    """
    Compute the maximum annual precipitation for all files using multiprocessing.
    """

    # Ensure output directory exists
    output_file = rf'../data/max_annual_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{dataname}.csv'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    if os.path.exists(output_file) and not overwrite:
        print(f'{output_file} already exists, skip...')

        return
    else:
        if not os.path.exists(output_file):
            print(f'{output_file} does not exist, calculating...')
        else:
            print(f'{output_file} exists, overwriting...')

    # Get all NetCDF file paths
    files = []
    for f in os.listdir(data_folder):
        match = re.findall(r'(\d{4})', f)
        if match and f.endswith('.nc'):
            year = int(match[-1])
            if START_YEAR <= year <= END_YEAR:
                files.append(os.path.join(data_folder, f))

    if not files:
        raise FileNotFoundError(f"No NetCDF files found in {data_folder}")
    
    # Get land mask
    if dataname in CMIP6_LS:
        land_mask_path = rf'../data/mask/land_mask_{dataname}.nc'
        land_mask = xr.open_dataset(land_mask_path)['land']
        land_mask['lon'] = land_mask['lon'].astype('float32')
        land_mask['lat'] = land_mask['lat'].astype('float32')
    else:
        land_mask = None
    # Use multiprocessing to process files in parallel
    num_processes = min(num_processes, cpu_count())
    with Pool(processes=num_processes) as pool:
        results = pool.starmap(process_file, [(f, land_mask) for f in files])

    # Convert results to a DataFrame
    results.sort(key=lambda x: x[0])  # Sort by year
    df = pd.DataFrame(results, columns=['year', 'annual_prcp_mm'])
    df.to_csv(output_file, index=False)

    print(f"Results saved to {output_file}")

    return


if __name__ == "__main__":
    t1 = time.time()
    
    for dataname in DATA_LS:
        data_folder = DATAPATHS[dataname]
        resolution = RESOLUTIONS[dataname]
        if resolution >= 0.5:
            num_processes = 42
        elif resolution >= 0.1 and resolution < 0.5:
            num_processes = 9
        else:
            num_processes = 3
        compute_max_precipitation(data_folder, dataname, num_processes, OVERWRITE)

    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")

    