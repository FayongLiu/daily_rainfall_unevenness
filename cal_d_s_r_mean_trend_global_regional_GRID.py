# Calculate multi-year mean and trend (global and regional area weighted averages) for GRID data


import xarray as xr
import numpy as np
import os
import pandas as pd
import re
import time
from multiprocessing import Pool, cpu_count
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.datainfo import DATA_LS_80, DATA_LS_50, REGIONS


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr
DATA_LS = DATA_LS_80 if START_YEAR >= 1980 else DATA_LS_50


def save_area_mask(ref_ds, area_path, overwrite):
    """
    Function to cal the grid area, same resolution as ref_ds
    Args:
        ref_ds (xarray.DataArray)
        area_path (str)
        overwrite (bool): overwrite or not
    Returns:
        area_ds (xarray.DataArray), unit (km2)
    """

    os.makedirs(os.path.dirname(area_path), exist_ok=True)
    if os.path.exists(area_path) and not overwrite:
        area_ds = xr.open_dataset(area_path)
        area_ds = area_ds['area']
    else:
        if not os.path.exists(area_path):
            print(f'{area_path} does not exist, creating...')
        else:
            print(f'{area_path} exists, overwriting...')
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
        area_ds.to_netcdf(area_path)
        print(f'Saving {area_path}')

    return area_ds


def save_station_mask(ref_ds, station_loc, station_mask_path, overwrite):
    """
    Function to generate a station mask with the same resolution as ref_ds.
    The mask will have True where there are station locations and False elsewhere.
    Args:
        ref_ds (xarray.DataArray): The reference dataset with lat and lon coordinates.
        station_loc (pandas.DataFrame): A DataFrame containing the 'lat' and 'lon' of stations.
        station_mask_path (str): The path where the mask will be saved.
        overwrite (bool): Whether to overwrite the existing mask file.
    Returns:
        station_mask (xarray.DataArray): A boolean xarray mask with stations marked as True.
    """

    os.makedirs(os.path.dirname(station_mask_path), exist_ok=True)
    if os.path.exists(station_mask_path) and not overwrite:
        station_mask_ds = xr.open_dataset(station_mask_path)
        station_mask_ds = station_mask_ds['station']
    else:
        if not os.path.exists(station_mask_path):
            print(f'{station_mask_path} does not exist, creating...')
        else:
            print(f'{station_mask_path} exists, overwriting...')
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
        station_mask_ds.to_netcdf(station_mask_path)
        print(f'Saving {station_mask_path}')

    return station_mask_ds


# function to calculate global averages for a specific year, weighted by area
def cal_global_regional_averages_each_year(this_year_path, area_mask, station_mask, region):
    year_ds = xr.open_dataset(this_year_path)
    if region == 'global':
        year_ds = year_ds.sel(lat=slice(-60, 90))
    elif region in REGIONS.keys():
        lon_min, lon_max, lat_min, lat_max = REGIONS[region]
        year_ds = year_ds.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))
        area_mask = area_mask.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))
        station_mask = station_mask.sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))
    else:
        raise ValueError(f'Invalid region: {region}')
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
def cal_global_regional_averages_series(data_name, region, overwrite):

    if region == 'global':
        outpath = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/global_{data_name}.csv'
    elif region in REGIONS.keys():
        outpath = rf"../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/region_{region.replace(' ', '_')}_{data_name}.csv"
    else:
        raise ValueError(f'Invalid region: {region}')
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    if os.path.exists(outpath) and not overwrite:
        print(f'{outpath} exists, skip...')
        return
    
    if not os.path.exists(outpath):
        print(f'{outpath} does not exist, calculating...')
    else:
        print(f'{outpath} exists, overwriting...')

    # load ref ds, area and station mask
    file_dir = rf'../data/d_s_ratio/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{data_name}'
    file_ls = os.listdir(file_dir)
    file_ls.sort()
    file_ls = [os.path.join(file_dir, f) for f in file_ls]

    ref_path = file_ls[0]
    area_mask_path = rf'../data/mask/area_mask_{data_name}.nc'
    station_mask_path = rf'../data/mask/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station_mask_{data_name}.nc'
    ref_ds = xr.open_dataset(ref_path)['S_daily'].isel(time=0)
    ref_ds = ref_ds.sortby('lat').sortby('lon')
    area_mask = save_area_mask(ref_ds, area_mask_path, False)
    station_loc_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.csv'
    station_loc = pd.read_csv(station_loc_path, usecols=['lon', 'lat'])
    station_mask = save_station_mask(ref_ds, station_loc, station_mask_path, False)

    area_mask = area_mask.sel(lat=slice(-60, 90))
    station_mask = station_mask.sel(lat=slice(-60, 90))

    # multiprocess
    num_workers = min(len(file_ls), cpu_count())
    with Pool(processes=num_workers) as pool:
        result_ls = pool.starmap(
            cal_global_regional_averages_each_year,
            [(this_year_path, area_mask, station_mask, region) for this_year_path in file_ls])
    result_df = pd.concat(result_ls, ignore_index=True)
    result_df.to_csv(outpath, index=False)
    print(f'COMPLETE calculating mean and trend of {data_name} at {region}')
    print(f'Saving {outpath}')

    return


def main():

    t1 = time.time()

    for data_name in DATA_LS:
        for region in ['global'] + list(REGIONS.keys()):
            cal_global_regional_averages_series(data_name, region, OVERWRITE)

    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")

    return


if __name__ == "__main__":
    
    main()
    
