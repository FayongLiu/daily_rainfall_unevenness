import xarray as xr
import pandas as pd
import numpy as np
import gzip
import os
import re
from datetime import  datetime, timedelta
import gc
import matplotlib.pyplot as plt
import glob
from rainfall_ui.util.datainfo import CMIP6_LS


def cal_daily_prcp_era5l(year, input_dir, output_dir, overwrite):
    ''' Function to calculate daily precipitation of ERA5_Land data '''

    # Define output directory and file name
    os.makedirs(output_dir, exist_ok=True)
    outpath = os.path.join(output_dir, f"precipitation_daily_{year}.nc")
    if os.path.exists(outpath):
        if overwrite:
            print(f'Overwriting {outpath}...')   
        else:
            print(f'{outpath} already exists, skip...')
            return
    else:
        print(f'{outpath} does not exist, preprocessing...')
    
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
    combined_precip = combined_precip.sortby('time')
    if year != 1950:
        combined_precip = combined_precip.isel(time=slice(1, None))

    # Update the time dimension by shifting one day back
    updated_time = combined_precip.time - pd.Timedelta(days=1)  # Shift by 1 day
    combined_precip = combined_precip.assign_coords(time=updated_time)

    # Add attributes to the dataset
    combined_precip.attrs['units'] = 'mm'
    combined_precip.attrs['long_name'] = 'Daily Total Precipitation'

    # Save the results to NetCDF
    combined_precip.to_netcdf(outpath)
    print(f'Saving ERA5-Land daily precipitation for {year} to: {outpath}')

    return


def cal_daily_prcp_crujra(year, input_dir, output_dir, overwrite):
    ''' Function to calculate daily precipitation for CRU-JRA data '''

    os.makedirs(output_dir, exist_ok=True)
    outpath = os.path.join(output_dir, f"pre_{year}_daily.nc")
    if os.path.exists(outpath):
        if overwrite:
            print(f'Overwriting {outpath}...')   
        else:
            print(f'{outpath} already exists, skip...')
            return
    else:
        print(f'{outpath} does not exist, preprocessing...')

    input_file = os.path.join(input_dir, f"crujra.v2.2.5d.pre.{str(year)}.365d.noc.nc")
    if not os.path.exists(input_file):
        print(f"Missing file for year {year}. Skipping...")
        return
    
    ds = xr.open_dataset(input_file)

    # Resample to daily statistics
    ds = ds.sortby('time')
    ds = ds['pre'].resample(time='1D').sum(skipna=True)
    ds = xr.where(ds>=0, ds, np.nan)
    
    # Add attributes
    ds.attrs['units'] = 'mm'
    ds.attrs['long_name'] = 'Daily Total Precipitation'

    # Save results
    ds.to_netcdf(outpath)
    print(f'Saving CRU-JRA daily precipitation for {year} to: {outpath}')
          
    return


def get_all_dates(year):
    ''' Function to get all dates of a specific year '''

    start_date = datetime(year, 1, 1).date()
    end_date = datetime(year, 12, 31).date()
    delta = timedelta(days=1)
    all_dates = []
    current_date = start_date
    while current_date <= end_date:
        all_dates.append(current_date)
        current_date += delta

    return all_dates


def load_data_others(inpath, data_name):
    ''' Function to load data of other grid-based datasets 
    inlcuding IMERG-GPM, GSMaP, CMORPH, PERSIANN-CCS-CDR, PERSIANN, MSWEP, JRA3q, and CMIP6 '''

    try:
        if data_name in ['imerg', 'cmorph', 'mswep']:
            if data_name == 'imerg':
                ds = xr.open_dataset(
                        inpath,
                        engine='h5netcdf',
                        group='Grid'
                    )
                var_ds = ds['precipitation'].astype('float32') # mm hour-1
                var_ds = var_ds * 0.5 # half hour
                var_ds = var_ds.transpose('time', 'lat', 'lon')
            elif data_name == 'cmorph':
                ds = xr.open_dataset(inpath)
                var_ds = ds['cmorph'].astype('float32') # mm hour-1
                var_ds = var_ds * 0.5 # half hour
            else:
                ds = xr.open_dataset(inpath)
                var_ds = ds['precipitation'].astype('float32') # mm 3 hours-1
                if 'sfc' in ds.dims:
                    var_ds = var_ds.mean(dim='sfc')
            var_ds = var_ds.where(var_ds >= 0, np.nan)
            var_ds.name = 'prcp'
        elif data_name in ['gsmap', 'persiann', 'persiann_cdr']:
            if data_name == 'gsmap':
                nlon, nlat = 3600, 1200
                lon_start, lat_start = 0.05, 59.95
                lon_res, lat_res = 0.1, 0.1
                date_part = os.path.basename(inpath).split('.')[1]
                time_part = os.path.basename(inpath).split('.')[2]
                datetime_str = f"{date_part}{time_part}"
                dt = datetime.strptime(datetime_str, '%Y%m%d%H%M')
            elif data_name == 'persiann_cdr':
                nlon, nlat = 9000, 3000
                lon_start, lat_start = 0.02, 59.98
                lon_res, lat_res = 0.04, 0.04
                pattern = r'PCCSCDR3h(\d{6})(\d{2})?\.bin\.gz'
                match = re.search(pattern, os.path.basename(inpath))
                if match:
                    date_str = match.group(1)
                    hour_str = match.group(2)
                    year = int(os.path.basename(os.path.dirname(inpath))) 
                    month = int(date_str[2:4])
                    day = int(date_str[4:6])
                    hour = int(hour_str)
                    dt = datetime(year, month, day, hour)
            else:
                nlon, nlat = 1440, 480
                lon_start, lat_start = 0.125, 59.875
                lon_res, lat_res = 0.25, 0.25
                pattern = r'm6s4rr(\d{5})(\d{2})?\.bin'
                match = re.search(pattern, os.path.basename(inpath))
                if match:
                    date_str = match.group(1)
                    hour_str = match.group(2)
                    year = int(os.path.basename(os.path.dirname(inpath))) 
                    doy = int(date_str[2:5])
                    hour = int(hour_str)
                    base = datetime(year, 1, 1, 0, 0, 0)
                    dt = base + timedelta(days=doy - 1, hours=hour)
            if data_name == 'persiann':
                with open(inpath, 'rb') as f:
                    data = f.read()
                    prcp = np.frombuffer(data, dtype='>f4')
                    if np.nanmax(prcp) > 1000000:
                        prcp = np.frombuffer(data, dtype='<f4')
            else:
                with gzip.open(inpath, 'rb') as f:
                    data = f.read()
                    prcp = np.frombuffer(data, dtype='<f4')
            prcp = prcp.astype('float32')
            prcp = prcp.reshape(nlat, nlon)
            prcp = np.where(prcp < 0, np.nan, prcp)
            lon = np.arange(lon_start, lon_start + nlon * lon_res, lon_res)
            lat = np.arange(lat_start, lat_start - nlat * lat_res, -lat_res)
            var_ds = xr.DataArray(
                prcp,
                dims=['lat', 'lon'],
                coords={'lat': lat, 'lon': lon},
                name='prcp'
            )
            # add new time dimension
            var_ds = var_ds.expand_dims('time')
            var_ds = var_ds.assign_coords(time=np.atleast_1d(pd.to_datetime(dt)))
        elif data_name == 'jra3q':
            ds = xr.open_dataset(inpath)
            var_ds = ds['tprate1have-sfc-fc-gauss'].astype('float32') # kg m-2 s-1 or mm s-1
            var_ds = var_ds * 60 * 60 # hourly
            var_ds = var_ds.where(var_ds >= 0, np.nan)
            var_ds.name = 'prcp'
        elif data_name in CMIP6_LS:
            ds = xr.open_dataset(inpath)
            var_ds = ds['pr'] * 86400 # mm s-1
            var_ds = var_ds.where(var_ds >= 0, np.nan)
            var_ds.name = 'prcp'
        else:
            raise ValueError(f"Data name {data_name} is not supported.")

        var_ds['lon'] = xr.where(var_ds['lon'] > 180, var_ds['lon'] - 360, var_ds['lon'])
        var_ds = var_ds.sortby('lat').sortby('lon')
        var_ds['lon'] = var_ds['lon'].astype('float32')
        var_ds['lat'] = var_ds['lat'].astype('float32')
    except Exception as e:
        print(f"Error loading data from {inpath}: {e}")
        var_ds = None

    return var_ds


def get_land_mask(inpath, land_path, outdir, data_name, overwrite):
    ''' Function to get land mask for each grid-based dataset '''

    os.makedirs(outdir, exist_ok=True)
    outname_land = f'land_mask_{data_name}.nc'
    outpath_land = os.path.join(outdir, outname_land)
    var_ds = load_data_others(inpath, data_name)
    print(f'\nLoad ref prcp data for {data_name}:')
    print(var_ds)
    var_ds = var_ds.isel(time=0).squeeze()
    if os.path.exists(outpath_land) and not overwrite:
        print(f'Land mask for {data_name} already exists. Loading...')
        land_mask = xr.open_dataset(outpath_land)['land']
        land_mask['lon'] = land_mask['lon'].astype('float32')
        land_mask['lat'] = land_mask['lat'].astype('float32')
    else:
        if not os.path.exists(outpath_land):
            print(f'Land mask for {data_name} does not exist. Calculating...')
        else:
            print(f'Overwriting land mask for {data_name}...')
        land_ds = xr.open_dataset(land_path)['tp'].isel(time=0).squeeze().astype('float32')
        land_ds = land_ds.rename({'latitude': 'lat', 'longitude': 'lon'})
        land_ds['lon'] = xr.where(land_ds['lon'] > 180, land_ds['lon'] - 360, land_ds['lon'])
        land_ds = land_ds.sortby('lat').sortby('lon')
        land_ds['lon'] = land_ds['lon'].astype('float32')
        land_ds['lat'] = land_ds['lat'].astype('float32')
        land_ds = land_ds.reindex(lat=var_ds.lat, lon=var_ds.lon, method='nearest')
        outname_ref = 'prcp_test_era5land.png'
        outpath_ref = os.path.join(outdir, outname_ref)
        if not os.path.exists(outpath_ref) or overwrite:
            print(land_ds)
            fig, ax = plt.subplots(1, 1, figsize=(8, 4), dpi=300)
            land_ds.plot(ax=ax)
            plt.savefig(os.path.join(outdir, outname_ref), dpi=300)
            plt.close()
        land_mask = land_ds >= 0
        land_mask.name = 'land'
        land_mask.to_netcdf(outpath_land)
        print(f'Saving {outpath_land}')

    print(f'Land mask for {data_name}:')
    print(land_mask)

    # save prcp
    outname_var = f'prcp_test_{data_name}.nc'
    outpath_var = os.path.join(outdir, outname_var)
    if not os.path.exists(outpath_var) or overwrite:
        var_ds = var_ds.where(land_mask, np.nan)
        var_ds.to_netcdf(outpath_var)
        print(f'Saving {outpath_var}')

    # save plots
    outname_land_fig = f'land_mask_{data_name}.png'
    outpath_land_fig = os.path.join(outdir, outname_land_fig)
    if not os.path.exists(outpath_land_fig) or overwrite:
        fig, ax = plt.subplots(1, 1, figsize=(8, 4), dpi=300)
        land_mask.plot(ax=ax)
        plt.savefig(outpath_land_fig, dpi=300)
        plt.close()
        print(f'Saving {outpath_land_fig}')
    outname_var_fig = f'prcp_test_{data_name}.png'
    outpath_var_fig = os.path.join(outdir, outname_var_fig)
    if not os.path.exists(outpath_var_fig) or overwrite:
        fig, ax = plt.subplots(1, 1, figsize=(8, 4), dpi=300)
        var_ds.plot(ax=ax)
        plt.savefig(outpath_var_fig, dpi=300)
        plt.close()
        print(f'Saving {outpath_var_fig}')

    return land_mask


def get_date_str(date, data_name):
    ''' Function to get date string from file name for other datasets '''
    
    if data_name in ['imerg', 'gsmap', 'cmorph']:
        date_str = date.strftime('%Y%m%d')
    elif data_name == 'persiann_cdr':
        date_str = date.strftime('%y%m%d')
        date_str = f'PCCSCDR3h{date_str}'
    elif data_name == 'persiann':
        doy = date.timetuple().tm_yday
        year = str(int(date.year))[2:4]
        date_str = f'm6s4rr{year}{doy:03d}'
    elif data_name == 'mswep':
        doy = date.timetuple().tm_yday
        date_str = f'{date.year}{doy:03d}'
    else:
        raise ValueError(f"Data name {data_name} is not supported.")

    return date_str


def cal_daily_prcp_jra3q(year, input_dir, output_dir, land_mask, overwrite):
    ''' Function to calculate daily precipitation of JRA3q data '''

    # Define output directory and file name
    os.makedirs(output_dir, exist_ok=True)
    outpath = os.path.join(output_dir, f"daily_precipitation_{year}.nc")
    if os.path.exists(outpath):
        if overwrite:
            print(f'Overwriting {outpath}...')   
        else:
            print(f'{outpath} already exists, skip...')
            return
    else:
        print(f'{outpath} does not exist, preprocessing...')

    # get all files for this year
    file_name_ls = os.listdir(input_dir)
    file_name_ls = [f for f in file_name_ls if f.endswith('.nc') and f'gauss.{year}' in f]
    
    annual_ds = []
    for file_name in file_name_ls:
        inpath = os.path.join(input_dir, file_name)
        print(f'Preprocessing {inpath} ...')
        if not os.path.exists(inpath):
            print(f"Missing file for year {year}. Skipping...")
            return
        
        var_ds = load_data_others(inpath, 'jra3q')
        if var_ds is not None:
            var_ds = var_ds.sortby('time')
            var_ds = var_ds.resample(time='1D').sum(skipna=True)
            annual_ds.append(var_ds)

        del var_ds
        gc.collect()
    
    annual_ds = xr.concat(annual_ds, dim='time').sortby('time')
    annual_ds = annual_ds.where(land_mask, np.nan)

    # Add attributes to the dataset
    annual_ds.attrs['units'] = 'mm'
    annual_ds.attrs['long_name'] = 'Daily Total Precipitation'

    # Save the results to NetCDF
    annual_ds.to_netcdf(outpath)
    print(f'Saving JRA3q daily precipitation for {year} to: {outpath}')

    return


def cal_daily_prcp_others(year, input_dir_base, output_dir, data_name, land_mask, overwrite):
    ''' Function to calculate daily precipitation of other data,
    including IMERG-GPM, GSMaP, CMORPH, PERSIANN-CCS-CDR, PERSIANN, and MSWEP '''

    # Define output directory and file name
    os.makedirs(output_dir, exist_ok=True)
    outpath = os.path.join(output_dir, f"daily_precipitation_{year}.nc")
    if os.path.exists(outpath):
        if overwrite:
            print(f'Overwriting {outpath}...')   
        else:
            print(f'{outpath} already exists, skip...')
            return
    else:
        print(f'{outpath} does not exist, preprocessing...')

    input_dir = os.path.join(input_dir_base, f'glo{year}') if data_name == 'mswep' else os.path.join(input_dir_base, str(year))
    if not os.path.isdir(input_dir):
        print(f"Missing files for year {year}. Skipping...")
        return
    
    # get all files for this year
    file_name_ls = glob.glob(os.path.join(input_dir, '**', '*'), recursive=True)
    if data_name == 'persiann':
        suffixes = ('.bin',)
    else:
        suffixes = ('.HDF5', '.nc', '.bin.gz', '.dat.gz')
    file_name_ls = [f for f in file_name_ls if f.endswith(suffixes)]
    file_name_ls.sort()

    annual_ds = []
    all_dates = get_all_dates(year)
    for date in all_dates:
        print(f'Preprocessing {date} for {data_name}...')
        # get date string
        date_str = get_date_str(date, data_name)
        sub_file_name_ls = [ff for ff in file_name_ls if date_str in os.path.basename(ff)]
        daily_ds = []
        for data_file in sub_file_name_ls:
            # load data
            var_ds = load_data_others(data_file, data_name)
            if var_ds is not None:
                daily_ds.append(var_ds)
            
            del var_ds
            gc.collect()

        if len(daily_ds) > 0:
            daily_ds = xr.concat(daily_ds, dim='time').sortby('time')
            daily_ds = daily_ds.resample(time='1D').sum(skipna=True)
            annual_ds.append(daily_ds)

        del daily_ds
        gc.collect()

    annual_ds = xr.concat(annual_ds, dim='time').sortby('time')
    annual_ds = annual_ds.where(land_mask, np.nan)

    # Add attributes to the dataset
    annual_ds.attrs['units'] = 'mm'
    annual_ds.attrs['long_name'] = 'Daily Total Precipitation'

    # Save the results to NetCDF
    annual_ds.to_netcdf(outpath)
    print(f'Saving {data_name.upper()} daily precipitation for {year} to: {outpath}')

    return

