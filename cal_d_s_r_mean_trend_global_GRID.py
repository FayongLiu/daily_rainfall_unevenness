# -*- coding: utf-8 -*-
import xarray as xr
import numpy as np
import os
import pandas as pd
import re
import time
from multiprocessing import Pool, cpu_count
from pre_isd_select_valid_station import START_YEAR, END_YEAR, TH_YEAR
from pre_GRID_cal_maximum_annual_prcp import model_ls


def save_area_mask(ref_ds, area_path):
    """
    Function to cal the grid area, same resolution as ref_ds
    Args:
        ref_ds (xarray.DataArray)
        area_path (str)
    Returns:
        area_ds (xarray.DataArray), unit (km2)
    """
    new_ref_ds = ref_ds.copy()
    ref_data = new_ref_ds.values
    ref_lat = new_ref_ds['lat'].values
    ref_lon = new_ref_ds['lon'].values
    lat_size = 111.3214 * (ref_lat[1] - ref_lat[0])
    for lat in range(len(ref_lat)):
        lat_cos = np.cos(np.pi * ref_lat[lat] / 180)
        ref_data[lat, :] = lat_size * lat_size * lat_cos
    # create a new xarray
    area_ds = xr.DataArray(
        ref_data,
        coords = {
            'lat': ref_lat,
            'lon': ref_lon
        },
        dims = ['lat', 'lon'],
        name = 'area'
    )
    area_ds = area_ds.sortby('lon').sortby('lat')
    os.makedirs(os.path.dirname(area_path), exist_ok=True)
    area_ds.to_netcdf(area_path)
    print(f'Saving {area_path}')

    return area_ds


def save_station_mask(ref_ds, station_loc, station_mask_path):
    """
    Function to generate a station mask with the same resolution as ref_ds.
    The mask will have True where there are station locations and False elsewhere.
    Args:
        ref_ds (xarray.DataArray): The reference dataset with lat and lon coordinates.
        station_loc (pandas.DataFrame): A DataFrame containing the 'lat' and 'lon' of stations.
        station_mask_path (str): The path where the mask will be saved.
    Returns:
        station_mask (xarray.DataArray): A boolean xarray mask with stations marked as True.
    """
    ref_lat = ref_ds['lat'].values
    ref_lon = ref_ds['lon'].values
    # Create an empty mask with the same shape as the reference dataset
    station_mask = np.zeros((len(ref_lat), len(ref_lon)), dtype=bool)
    # Iterate over the station locations and mark the corresponding grid cells
    for _, row in station_loc.iterrows():
        lat_idx = np.argmin(np.abs(ref_lat - row['lat']))
        lon_idx = np.argmin(np.abs(ref_lon - row['lon']))
        station_mask[lat_idx, lon_idx] = True

    # Create a new xarray DataArray for the station mask
    station_mask_ds = xr.DataArray(
        station_mask,
        coords={
            'lat': ref_lat,
            'lon': ref_lon
        },
        dims=['lat', 'lon'],
        name='station'
    )

    # Save the station mask as a netCDF file
    os.makedirs(os.path.dirname(station_mask_path), exist_ok=True)
    station_mask_ds.to_netcdf(station_mask_path)
    print(f'Saving {station_mask_path}')

    return station_mask_ds


# function to calculate global averages for a specific year, weighted by area
def cal_global_averages_each_year(this_year_path, area_mask, station_mask, ref_ds=None):
    year_ds = xr.open_dataset(this_year_path)
    if ref_ds is not None:
        # resample CMIP6 model to the resolution of CRU JRA
        year_ds['lon'] = xr.where(year_ds['lon'] > 180, year_ds['lon'] - 360, year_ds['lon'])
        year_ds = year_ds.sortby('lat').sortby('lon')
        template = xr.Dataset(coords={'lat': ref_ds['lat'], 'lon': ref_ds['lon']})
        year_ds = year_ds.interp_like(template, method='linear')
        year_ds = year_ds.where(~np.isnan(ref_ds))
#    area_mask = area_mask.sel(lon=slice(-70, 85))
#    station_mask = station_mask.sel(lon=slice(-70, 85))
#    year_ds = year_ds.sel(lon=slice(-70, 85))
    result = {}
    match = re.search(r'\d{4}', os.path.basename(this_year_path))
    year = int(match.group())
    result['year'] = year

    # List of variables to calculate weighted averages
    variables = ['S_daily', 'S_monthly', 'D_daily', 'D_monthly', 'PRCP_ratio', 'rain_day']
    for var_name in variables:
        var_ds = year_ds[var_name]
        weighted_avg = var_ds.weighted(area_mask).mean(skipna=True).item()
        result[var_name] = weighted_avg

        var_station_ds = var_ds.where(station_mask)
        weighted_avg = var_station_ds.weighted(area_mask).mean(skipna=True).item()
        result[f'{var_name}_station'] = weighted_avg

    return pd.DataFrame([result])


# function to calculate global averages series during 1980-2020
def cal_global_averages_series(data_name):
    # load ref ds, area and station mask
    if data_name in ['CRU_JRA', 'ERA5_Land']:
        ref_path = rf'../data/d_s_ratio/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{data_name}/s_d_ratio_{START_YEAR}.nc'
        area_mask_path = rf'../data/mask/area_mask_{data_name}.nc'
        station_mask_path = rf'../data/mask/station_mask_{START_YEAR}_{END_YEAR}_gte{TH_YEAR}_{data_name}.nc'
    else:
        # convert CMIP6 models to the resolution of CRU_JRA
        ref_path = rf'../data/d_s_ratio/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/CRU_JRA/s_d_ratio_{START_YEAR}.nc'
        area_mask_path = rf'../data/mask/area_mask_CRU_JRA.nc'
        station_mask_path = rf'../data/mask/station_mask_{START_YEAR}_{END_YEAR}_gte{TH_YEAR}_CRU_JRA.nc'
    ref_ds = xr.open_dataset(ref_path)['S_daily'].isel(time=0)
    ref_ds = ref_ds.sortby('lat').sortby('lon')
    if os.path.exists(area_mask_path):
        print(f'Area mask existed, {area_mask_path}')
        area_mask = xr.open_dataset(area_mask_path)['area']
    else:
        print(f'Area mask does not exist, {area_mask_path}')
        print(f'Creating ...')
        area_mask = save_area_mask(ref_ds, area_mask_path)
        print(f'Finish creating area mask')

    # load station mask
    station_loc_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station_isd.csv'
    if os.path.exists(station_mask_path):
        print(f'Station msdk existed, {station_mask_path}')
        station_mask = xr.open_dataset(station_mask_path)['station']
    else:
        print(f'Station mask does not exist, {station_mask_path}')
        print(f'Creating ...')
        station_loc = pd.read_csv(station_loc_path, usecols=['lon', 'lat'])
        station_mask = save_station_mask(ref_ds, station_loc, station_mask_path)
        print(f'Finish creating station mask')
    print(f'Number of station: {station_mask.sum().item()}')

    # multiprocess
    file_dir = rf'../data/d_s_ratio/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{data_name}'
    file_ls = os.listdir(file_dir)
    file_ls.sort()
    file_ls = [os.path.join(file_dir, f) for f in file_ls]
    num_workers = min(len(file_ls), cpu_count())
    if data_name in ['CRU_JRA', 'ERA5_Land']:
        ref_ds = None
    with Pool(processes=num_workers) as pool:
        result_ls = pool.starmap(
            cal_global_averages_each_year,
            [(this_year_path, area_mask, station_mask, ref_ds) for this_year_path in file_ls])
    result_df = pd.concat(result_ls, ignore_index=True)
    outpath = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/global_{data_name}.csv'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    result_df.to_csv(outpath, index=False)
    print(f'COMPLETE calculating mean and trend of {data_name} at global scale')
    print(f'Saving {outpath}')

    return


def main():
    # CMIP6 models
    for model in model_ls:
        cal_global_averages_series(model)
    cal_global_averages_series('CRU_JRA')
    cal_global_averages_series('ERA5_Land')

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