# Code for converted station results to grid


import xarray as xr
import pandas as pd
import numpy as np
import os
from rainfall_ui.util.config import parse_args


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr


def point2grid(inpath, ref_path, outpath, overwrite):
    ''' Function to preprocess point data to grid scale
    
    :param inpath: input path
    :param ref_path: reference for resampling, 0.5*0.5 deg nc file
    :param outpath: output path
    :param overwrite: whether to overwrite existing files
    
    :return None
    
    '''

    if os.path.exists(outpath) and not overwrite:
        print(f'File {outpath} already exists, skip')
        return
    if not os.path.exists(outpath):
        print(f'File {outpath} does not exist, creating...')
    else:
        print(f'Overwriting {outpath}...')
    
    # Load reference grid
    ref_ds = xr.open_dataset(ref_path)
    ref_ds = ref_ds.sortby('lat').sortby('lon')
    lon_ref = ref_ds['lon'].values
    lat_ref = ref_ds['lat'].values
    
    # Read point data
    df = pd.read_csv(inpath)
    df = df.dropna()
    cols = list(df.columns)
    varnames = [varname for varname in cols if varname not in ['lon', 'lat', 'dataname', 'station']]
    
    # Initialize arrays for statistics
    nlat, nlon, nvar = len(lat_ref), len(lon_ref), len(varnames)
    data_sum = np.zeros((nlat, nlon, nvar))
    data_count = np.zeros((nlat, nlon, nvar), dtype=int)
    # Assign each point to nearest grid cell and accumulate statistics
    print(f'Total valid points: {len(df)}')
    for _, row in df.iterrows():
        lon = row['lon']
        lat = row['lat']
        # Find nearest grid cell
        lon_idx = np.argmin(np.abs(lon_ref - lon))
        lat_idx = np.argmin(np.abs(lat_ref - lat))
        for var_idx, varname in enumerate(varnames):
            value = row[varname]
            # Accumulate statistics
            data_sum[lat_idx, lon_idx, var_idx] += value
            data_count[lat_idx, lon_idx, var_idx] += 1
    
    # Initialize output arrays
    data_value = np.full((nlat, nlon, nvar), np.nan)
    mask_has_data = data_count > 0
    # Cells with data: calculate mean
    data_value[mask_has_data] = data_sum[mask_has_data] / data_count[mask_has_data]
    
    # Create Dataset
    ds_vars = {}
    for i, varname in enumerate(varnames):
        ds_vars[varname] = (['lat', 'lon'], data_value[:, :, i])
    
    ds = xr.Dataset(
        ds_vars,
        coords={
            'lon': lon_ref,
            'lat': lat_ref
        }
    )
    
    # save results
    ds.to_netcdf(outpath)
    print(f'File saved to {outpath}')

    return ds


def main():
    
    inpath = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.csv'
    ref_path = r'/data4/dataset/atmosphere/precipitation/CRU-JRA/pre/pre_2001_daily.nc'
    outpath = inpath.replace('.csv', '.nc')
    point2grid(inpath, ref_path, outpath, OVERWRITE)

    return


if __name__ == '__main__':

    main()

