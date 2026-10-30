# Code for calculating attribution of UI to Re and R/Rmax


import xarray as xr
import pandas as pd
import numpy as np
import os
from rainfall_ui.util.config import parse_args
from cal_d_s_r_mean_trend_station2grid import point2grid
from rainfall_ui.util.datainfo import CATEGORY_NAMES


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr


def attribute_station(inpath, ref_path, outpath, overwrite):

    if os.path.exists(outpath) and not overwrite:
        print(f'File {outpath} already exists, skip...')
        
        return

    if not os.path.exists(outpath):
        print(f'File {outpath} does not exist, creating...')
    else:
        print(f'Overwriting {outpath}...')

    # load data
    df = pd.read_csv(inpath)
    for scale in ['daily', 'monthly']:
        df[f'ConRE_abs_{scale}'] = df['PRCP_ratio_mean'] * df[f'D_{scale}_trend']
        df[f'ConRRmax_abs_{scale}'] = df[f'D_{scale}_mean'] * df['PRCP_ratio_trend']
        df[f'ConInter_abs_{scale}'] = df[f'S_{scale}_trend'] - df[f'ConRE_abs_{scale}'] - df[f'ConRRmax_abs_{scale}']
        df[f'Total_rel_{scale}'] = abs(df[f'ConRE_abs_{scale}']) + abs(df[f'ConRRmax_abs_{scale}']) + abs(df[f'ConInter_abs_{scale}'])
        df[f'ConRE_rel_{scale}'] = abs(df[f'ConRE_abs_{scale}']) / df[f'Total_rel_{scale}']
        df[f'ConRRmax_rel_{scale}'] = abs(df[f'ConRRmax_abs_{scale}']) / df[f'Total_rel_{scale}']
        df[f'ConInter_rel_{scale}'] = abs(df[f'ConInter_abs_{scale}']) / df[f'Total_rel_{scale}']

    # save data
    usecols = ['lon', 'lat',
               'ConRE_abs_daily', 'ConRRmax_abs_daily', 'ConInter_abs_daily',
               'ConRE_abs_monthly', 'ConRRmax_abs_monthly', 'ConInter_abs_monthly',
               'ConRE_rel_daily', 'ConRRmax_rel_daily', 'ConInter_rel_daily',
               'ConRE_rel_monthly', 'ConRRmax_rel_monthly', 'ConInter_rel_monthly']
    df = df[usecols]
    df.to_csv(outpath, index=False)
    print(f'Saving {outpath}')

    outpath_nc = outpath.replace('.csv', '.nc')
    point2grid(outpath, ref_path, outpath_nc, overwrite)

    return


def attribute_grid(inpath, outpath, overwrite):

    if os.path.exists(outpath) and not overwrite:
        print(f'File {outpath} already exists, skip...')
        
        return

    if not os.path.exists(outpath):
        print(f'File {outpath} does not exist, creating...')
    else:
        print(f'Overwriting {outpath}...')

    # load data
    ds = xr.open_dataset(inpath)
    for scale in ['daily', 'monthly']:
        ds[f'ConRE_abs_{scale}'] = ds['PRCP_ratio_mean'] * ds[f'D_{scale}_trend']
        ds[f'ConRRmax_abs_{scale}'] = ds[f'D_{scale}_mean'] * ds['PRCP_ratio_trend']
        ds[f'ConInter_abs_{scale}'] = ds[f'S_{scale}_trend'] - ds[f'ConRE_abs_{scale}'] - ds[f'ConRRmax_abs_{scale}']
        ds[f'Total_rel_{scale}'] = abs(ds[f'ConRE_abs_{scale}']) + abs(ds[f'ConRRmax_abs_{scale}']) + abs(ds[f'ConInter_abs_{scale}'])
        ds[f'ConRE_rel_{scale}'] = abs(ds[f'ConRE_abs_{scale}']) / ds[f'Total_rel_{scale}']
        ds[f'ConRRmax_rel_{scale}'] = abs(ds[f'ConRRmax_abs_{scale}']) / ds[f'Total_rel_{scale}']
        ds[f'ConInter_rel_{scale}'] = abs(ds[f'ConInter_abs_{scale}']) / ds[f'Total_rel_{scale}']

    # save data
    usecols = ['lon', 'lat',
               'ConRE_abs_daily', 'ConRRmax_abs_daily', 'ConInter_abs_daily',
               'ConRE_abs_monthly', 'ConRRmax_abs_monthly', 'ConInter_abs_monthly',
               'ConRE_rel_daily', 'ConRRmax_rel_daily', 'ConInter_rel_daily',
               'ConRE_rel_monthly', 'ConRRmax_rel_monthly', 'ConInter_rel_monthly']
    ds[usecols].to_netcdf(outpath)
    print(f'Saving {outpath}')

    return


def main():
    
    inpath_station = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.csv'
    ref_path = r'/data4/dataset/atmosphere/precipitation/CRU-JRA/pre/pre_2001_daily.nc'
    outpath_station = inpath_station.replace('station.csv', 'station_attribution.csv')
    attribute_station(inpath_station, ref_path, outpath_station, OVERWRITE)

    for category in CATEGORY_NAMES:
        inpath = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/grid_{category}_ensembles.nc'
        outpath = inpath.replace('ensembles.nc', 'ensembles_attribution.nc')
        attribute_grid(inpath, outpath, OVERWRITE)

    return


if __name__ == '__main__':

    main()

