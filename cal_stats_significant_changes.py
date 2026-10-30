import os
import time
import pandas as pd
import numpy as np
import xarray as xr
from multiprocessing import Pool, cpu_count
from rainfall_ui.util.datainfo import DATA_LS_80, DATA_LS_50
from rainfall_ui.util.config import parse_args
from cal_d_s_r_mean_trend_global_regional_GRID import save_area_mask, save_station_mask


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr
DATA_LS = DATA_LS_80 if START_YEAR >= 1980 else DATA_LS_50


# function to calculate the statistics of significant change of gauge-based observations
def cal_stats_sig_gauge(isd_path, varname):
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
def cal_stats_sig_grid(data_name, varname_ls, use_station_mask, overwrite):

    if use_station_mask:
        outpath = rf'../data/stats_sig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{data_name}_station.csv'
    else:
        outpath = rf'../data/stats_sig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{data_name}.csv'
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

    ds_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/grid_{data_name}.nc'
    df_ls = []
    for varname in varname_ls:
        varnames = [f'{varname}_trend', f'{varname}_p_value']
        ds = xr.open_dataset(ds_path)[varnames]
        ds = ds.sel(lat=slice(-60, 90))
        ds_mask = xr.where(
            (~np.isnan(ds[f'{varname}_trend'])) &
            (~np.isnan(ds[f'{varname}_p_value'])),
            1, np.nan)
        if use_station_mask:
            # mask by station
            ds_mask = ds_mask.where(station_mask)
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
    result_df.to_csv(outpath)
    print(f'Saving {outpath}')

    return result_df


def main():

    t1 = time.time()

    varname_ls = ['S_daily', 'S_monthly', 'D_daily', 'D_monthly', 'PRCP_ratio', 'rain_day', 'STD_daily_orig', 'STD_daily_detr']

    # station
    outpath = rf'../data/stats_sig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.csv'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    if os.path.exists(outpath) and not OVERWRITE:
        print(f'{outpath} exists, skip...')
        return
    
    if not os.path.exists(outpath):
        print(f'{outpath} does not exist, calculating...')
    else:
        print(f'{outpath} exists, overwriting...')

    station_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.csv'
    df_ls = []
    for varname in varname_ls:
        result_df = cal_stats_sig_gauge(station_path, varname)
        df_ls.append(result_df)
    result_df = pd.concat(df_ls, axis=0)
    result_df.to_csv(outpath)
    print(f'Saving {outpath}')

    # grid-based data
    varname_ls = ['S_daily', 'S_monthly', 'D_daily', 'D_monthly', 'PRCP_ratio', 'rain_day']
    num_workers = min(len(DATA_LS), cpu_count())
    with Pool(processes=num_workers) as pool:
        pool.starmap(cal_stats_sig_grid, [(data_name, varname_ls, use_station_mask, OVERWRITE) 
                                          for use_station_mask in [True, False] for data_name in DATA_LS])

    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")

    return


if __name__ == "__main__":
    
    main()

