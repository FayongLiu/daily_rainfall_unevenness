# -*- coding: utf-8 -*-
import os
import time
import pandas as pd
import numpy as np
import xarray as xr
from multiprocessing import Pool, cpu_count
from pre_isd_select_valid_station import START_YEAR, END_YEAR, TH_YEAR
from pre_GRID_cal_maximum_annual_prcp import model_ls


# function to calculate the statistics of significant change of isd
def cal_stats_sig_isd(isd_path, varname):
    usecols = [f'{varname}_trend', f'{varname}_p_value']
    df = pd.read_csv(isd_path, usecols=usecols)
    df = df.dropna()
    total_count = len(df)
    sig_inc = df[(df[f'{varname}_trend'] > 0) & (df[f'{varname}_p_value'] <= 0.05)]
    sig_inc_pct = len(sig_inc)/total_count
    sig_dec = df[(df[f'{varname}_trend'] < 0) & (df[f'{varname}_p_value'] <= 0.05)]
    sig_dec_pct = len(sig_dec)/total_count
    non_sig = 1 - sig_inc_pct - sig_dec_pct

    result_df = pd.DataFrame(
        [[sig_inc_pct, sig_dec_pct, non_sig]],
        index=[varname],
        columns=['sig_inc', 'sig_dec', 'non_sig']
    )

    return result_df


# function to calculate the statistics of significant change of grid-based data
def cal_stats_sig_grid(data_name, varname_ls):
    if data_name in ['CRU_JRA', 'ERA5_Land']:
        area_mask_path = rf'../data/mask/area_mask_{data_name}.nc'
        station_mask_path = rf'../data/mask/station_mask_{START_YEAR}_{END_YEAR}_gte{TH_YEAR}_{data_name}.nc'
    else:
        # CMIP6 models refer to CRU_JRA
        area_mask_path = rf'../data/mask/area_mask_CRU_JRA.nc'
        station_mask_path = rf'../data/mask/station_mask_{START_YEAR}_{END_YEAR}_gte{TH_YEAR}_CRU_JRA.nc'
    area_mask = xr.open_dataset(area_mask_path)['area']
    station_mask = xr.open_dataset(station_mask_path)['station']
    ds_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/grid_{data_name}.nc'
    df_ls = []
    for varname in varname_ls:
        varnames = [f'{varname}_trend', f'{varname}_p_value']
        ds = xr.open_dataset(ds_path)[varnames]
        # mask by station
        ds_mask = xr.where(
            station_mask &
            (~np.isnan(ds[f'{varname}_trend'])) &
            (~np.isnan(ds[f'{varname}_p_value'])),
            1, np.nan)
        total_count = ds_mask.count(dim=['lon', 'lat']).item()
        total_area = ds_mask.weighted(area_mask).sum(skipna=True).item()

        sig_inc = ds_mask.where((ds[f'{varname}_trend'] > 0) & (ds[f'{varname}_p_value'] <= 0.05))
        sig_inc_count_pct = sig_inc.count(dim=['lon', 'lat']).item() / total_count
        sig_inc_area_pct = sig_inc.weighted(area_mask).sum(skipna=True).item() / total_area

        sig_dec = ds_mask.where((ds[f'{varname}_trend'] < 0) & (ds[f'{varname}_p_value'] <= 0.05))
        sig_dec_count_pct = sig_dec.count(dim=['lon', 'lat']).item() / total_count
        sig_dec_area_pct = sig_dec.weighted(area_mask).sum(skipna=True).item() / total_area

        non_sig_count_pct = 1 - sig_inc_count_pct - sig_dec_count_pct
        non_sig_area_pct = 1 - sig_inc_area_pct - sig_dec_area_pct

        # Return as DataFrame
        result_df = pd.DataFrame(
            [[sig_inc_count_pct, sig_dec_count_pct, non_sig_count_pct, sig_inc_area_pct, sig_dec_area_pct, non_sig_area_pct]],
            index=[varname],
            columns=['sig_inc_count', 'sig_dec_count', 'non_sig_count', 'sig_inc_area', 'sig_dec_area', 'non_sig_area']
        )
        df_ls.append(result_df)

    result_df = pd.concat(df_ls, axis=0)
    outpath = rf'../data/stats_sig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{data_name}.csv'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    result_df.to_csv(outpath)
    print(f'Saving {outpath}')

    return result_df


def main():
    # isd
    isd_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station_isd.csv'
    varname_ls = ['S_daily', 'S_monthly', 'D_daily', 'D_monthly', 'PRCP_ratio', 'rain_day']
    df_ls = []
    for varname in varname_ls:
        result_df = cal_stats_sig_isd(isd_path, varname)
        df_ls.append(result_df)
    result_df = pd.concat(df_ls, axis=0)
    outpath = rf'../data/stats_sig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/isd.csv'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    result_df.to_csv(outpath)
    print(f'Saving {outpath}')

    # grid-based data
    data_name_ls = ['CRU_JRA', 'ERA5_Land'] + model_ls
    num_workers = min(len(data_name_ls), cpu_count())
    with Pool(processes=num_workers) as pool:
        pool.starmap(cal_stats_sig_grid, [(data_name, varname_ls) for data_name in data_name_ls])

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


