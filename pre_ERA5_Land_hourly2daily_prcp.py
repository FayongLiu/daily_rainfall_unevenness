# -*- coding: utf-8 -*-
import xarray as xr
import pandas as pd
import numpy as np
import os
import time
from multiprocessing import Pool, cpu_count


# cal daily prep
# Set paths
output_dir = r'/data1/share/ERA5_land/precipitation/daily/'
os.makedirs(output_dir, exist_ok=True)
input_dir = r'/data_backup/share/ERA5_land/precipitation/hourly/'


# function to calculate daily precipitation and save it as separate files
def cal_daily_prep(year):
    t1 = time.time()
    # Define the path to the current year's NetCDF file
    this_year_nc_file = f"precipitation_{year}.nc"
    next_year = year + 1
    next_year_nc_file = f"precipitation_{next_year}.nc"
    this_year_nc_path = os.path.join(input_dir, this_year_nc_file)
    next_year_nc_path = os.path.join(input_dir, next_year_nc_file)

    # Check if files exist
    if not os.path.exists(this_year_nc_path) or not os.path.exists(next_year_nc_path):
        print(f"Missing files for year {year} or {next_year}. Skipping...")
        return

    # Open the datasets
    this_year_dataset = xr.open_dataset(this_year_nc_path)
    next_year_dataset = xr.open_dataset(next_year_nc_path)

    # Extract daily precipitation
    daily_precip = this_year_dataset['tp'].sel(time=this_year_dataset['tp'].time.dt.hour == 0)
    last_day_prep = next_year_dataset['tp'].isel(time=0)

    # Combine the two datasets and convert from meters to millimeters
    combined_precip = xr.concat([daily_precip, last_day_prep], dim="time") * 1000  # Convert to mm
    if year != 1950:
        combined_precip = combined_precip.isel(time=slice(1, None))

    # Update the time dimension by shifting one day back
    updated_time = combined_precip.time - pd.Timedelta(days=1)  # Shift by 1 day
    combined_precip = combined_precip.assign_coords(time=updated_time)

    # Add attributes to the dataset
    combined_precip.attrs['units'] = 'mm'
    combined_precip.attrs['long_name'] = 'Daily Total Precipitation'

    # Define output directory and file name
    output_file = os.path.join(output_dir, f"daily_precipitation_{year}.nc")

    # Save the results to NetCDF
    combined_precip.to_netcdf(output_file)
    print(f"Processed and saved daily precipitation for {year} to: {output_file}")

    t2 = time.time()

    total_time = t2 - t1
    print(total_time)

    return


# Call the function to process one year
num_processes = min(10, cpu_count())
year_ls = np.arange(1950, 2024)
with Pool(processes=num_processes) as pool:
    pool.map(cal_daily_prep, year_ls)
