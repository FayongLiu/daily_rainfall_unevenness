# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np
from scipy.stats import linregress
from multiprocessing import Pool, cpu_count
import time
from pre_isd_select_valid_station import START_YEAR, END_YEAR, TH_YEAR


# define path
IN_DIR = rf'../data/isd_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'
OUT_PATH_MAX_PRCP = rf'../data/max_annual_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/isd.csv'
OUT_DIR_IDX = rf'../data/d_s_ratio/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/isd/'
OUT_DIR_MEAN_TREND = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station_isd.csv'
OUT_DIR_MEAN_TREND_GLOBAL = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/global_isd.csv'
os.makedirs(os.path.dirname(OUT_PATH_MAX_PRCP), exist_ok=True)
os.makedirs(OUT_DIR_IDX, exist_ok=True)
os.makedirs(os.path.dirname(OUT_DIR_MEAN_TREND), exist_ok=True)


# function to calculate multi-year maximum annual precipitation
def cal_max_prep(in_dir, out_path):
    if os.path.exists(out_path):
        print(f'{out_path} has already existed')
        max_prcp = pd.read_csv(out_path)
        max_prcp = max_prcp.iloc[0, 0]
    else:
        valid_station = os.listdir(in_dir)
        valid_station.sort()
        max_prcp = 0
        for station in valid_station:
            filepath = os.path.join(in_dir, station)
            df = pd.read_csv(filepath)
            # ignore rianfall less than 0.1 mm
            df.loc[df['PRCP'] < 0.1, 'PRCP'] = 0
            annual_R = df.groupby(df['year'])['PRCP'].sum().dropna()
            if not annual_R.empty:
                max_prcp = max(max_prcp, annual_R.max())
        max_prep_df = pd.DataFrame({'max_annual_prcp_mm': [max_prcp]})
        max_prep_df.to_csv(out_path, index=False)
        print(f'Save {out_path}')

    return max_prcp


# function to calculate rainfall unevenness
def cal_D_S_Ratio(in_dir, station, max_prcp, out_dir):
    filepath = os.path.join(in_dir, station)
    df = pd.read_csv(filepath)
    df.loc[df['PRCP'] < 0.1, 'PRCP'] = 0
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    grouped = df.groupby('year')
    results = []
    for year, group in grouped:
        prcp = group['PRCP']
        # annual precipitation
        R = prcp.sum()
        # cal index
        frequency_daily = len(prcp[prcp > 0])
        m_daily = len(prcp.dropna())
        prep_monthly = group.resample('ME', on='DATE')['PRCP'].sum()
        m_monthly = len(prep_monthly.dropna())
        if R == 0:
            D_daily = S_daily = 0
            D_monthly = S_monthly = 0
            PRCP_ratio = 0
            frequency_daily = 0
        else:
            # daily
            q_daily = 1 / m_daily
            pi_daily = prcp / R
            D_daily = np.nansum(np.where((pi_daily > 0), pi_daily * np.log2(pi_daily / q_daily), 0))
            PRCP_ratio = R / max_prcp
            S_daily = D_daily * PRCP_ratio
            # monthly
            q_monthly = 1 / m_monthly
            pi_monthly = prep_monthly / R
            D_monthly = np.nansum(np.where((pi_monthly > 0), pi_monthly * np.log2(pi_monthly / q_monthly), 0))
            S_monthly = D_monthly * PRCP_ratio

        # add result
        results.append({
            'station': station.replace('.csv', ''),
            'lon': group['LONGITUDE'].iloc[0],
            'lat': group['LATITUDE'].iloc[0],
            'year': year,
            'D_daily': D_daily,
            'D_monthly': D_monthly,
            'S_daily': S_daily,
            'S_monthly': S_monthly,
            'Annual_PRCP_mm': R,
            'PRCP_ratio': PRCP_ratio,
            'valid_day': m_daily,
            'rain_day': frequency_daily
        })

    # save result
    result_df = pd.DataFrame(results)
    output_file = os.path.join(out_dir, station)
    result_df.to_csv(output_file, index=False)

    return result_df


# function to calculate mean and trend
def calculate_mean_trend(df):
    valid_df = df.dropna()
    # calculate multi-year mean
    col_ls = valid_df.columns
    station_df = valid_df[col_ls[:3]].iloc[0]
    mean_col_ls = [f'{col}_mean' for col in col_ls[4:]]
    mean_df = valid_df[col_ls[4:]].mean()
    for col, mean_col in zip(col_ls[4:], mean_col_ls):
        station_df[mean_col] = mean_df[col]
    # calculate trend
    trend_col_ls = [f'{col}_trend' for col in col_ls[4:]]
    p_col_ls = [f'{col}_p_value' for col in col_ls[4:]]
    for i, (col, col_trend, col_p) in enumerate(
            zip(col_ls[4:], trend_col_ls, p_col_ls)):
        col_df = valid_df[['year', col]]
        if len(col_df) < 2:
            station_df[col_trend] = np.nan
            station_df[col_p] = np.nan
        try:
            slope, _, _, p_value, _ = linregress(col_df['year'], col_df[col])
            station_df[col_trend] = slope
            station_df[col_p] = p_value
        except:
            station_df[col_trend] = np.nan
            station_df[col_p] = np.nan

    return pd.DataFrame(station_df).T


def main():
    max_prcp = cal_max_prep(IN_DIR, OUT_PATH_MAX_PRCP)
    print(f'maximum annual precipitation: {max_prcp} mm')
    valid_station = os.listdir(IN_DIR)
    valid_station.sort()
    # multiprocess
    num_processes = min(50, cpu_count())
    with Pool(processes=num_processes) as pool:
        all_result = pool.starmap(
            cal_D_S_Ratio,
            [(IN_DIR, station, max_prcp, OUT_DIR_IDX) for station in valid_station]
        )
    print('COMPLETE calculating rainfall unevenness')

    with Pool(processes=num_processes) as pool:
        all_station_df = pool.map(calculate_mean_trend, all_result)
    station_df = pd.concat(all_station_df, ignore_index=True)
    station_df.to_csv(OUT_DIR_MEAN_TREND, index=False)
    print('COMPLETE calculating mean and trend for each station')

    all_result_df = pd.concat(all_result, ignore_index=True)
    global_df = all_result_df.iloc[:, 3:].groupby('year').mean()
    global_df.to_csv(OUT_DIR_MEAN_TREND_GLOBAL, index=True)
    print('COMPLETE calculating mean and trend at global scale')

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