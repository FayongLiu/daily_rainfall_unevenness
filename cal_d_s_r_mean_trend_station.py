# Code for calculating rainfall unevenness and mean/trend for stations

import os
import pandas as pd
import numpy as np
from scipy.stats import linregress
import pymannkendall as mk
from multiprocessing import Pool, cpu_count
import time
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.datainfo import REGIONS


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr


# define path
DATA_NAMES = ['ghcnd', 'cma', 'hpd', 'isd', 'cdc', 'swiss', 'eca', 'saca']
IN_DIR_LS = [rf'../data/{name}_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}' for name in DATA_NAMES]
OUT_PATH_MAX_PRCP = rf'../data/max_annual_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.csv'
OUT_DIR_IDX = rf'../data/d_s_ratio/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station/'
OUT_DIR_MEAN_TREND = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.csv'
OUT_DIR_MEAN_TREND_GLOBAL = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/global_station.csv'
os.makedirs(os.path.dirname(OUT_PATH_MAX_PRCP), exist_ok=True)
os.makedirs(OUT_DIR_IDX, exist_ok=True)
os.makedirs(os.path.dirname(OUT_DIR_MEAN_TREND), exist_ok=True)


# function to calculate multi-year maximum annual precipitation
def _cal_max_prep(inpath):
   
    df = pd.read_csv(inpath)
    # ignore rianfall less than 0.1 mm
    df.loc[df['PRCP'] < 0.1, 'PRCP'] = 0
    annual_R = df.groupby(df['year'])['PRCP'].sum().dropna()
    if not annual_R.empty:
        max_prcp = annual_R.max().item()
    else:
        max_prcp = 0

    return max_prcp


# function to calculate multi-year maximum annual precipitation
def cal_max_prep(in_dir_ls, out_path, overwrite):
    
    if os.path.exists(out_path) and not overwrite:
        print(f'{out_path} has already existed')
        max_prcp = pd.read_csv(out_path)
        max_prcp = max_prcp.iloc[0, 0]
    else:
        if overwrite:
            print(f'Overwriting {out_path}...')
        else:
            print(f'{out_path} does not exist, preprocessing...')
        valid_file_ls = []
        for in_dir in in_dir_ls:
            valid_files = os.listdir(in_dir)
            for f in valid_files:
                filepath = os.path.join(in_dir, f)
                valid_file_ls.append(filepath)
        num_processes = min(100, cpu_count())
        with Pool(processes=num_processes) as pool:
            max_prcp_ls = pool.map(_cal_max_prep, valid_file_ls)
        max_prcp = max(max_prcp_ls)
        max_prep_df = pd.DataFrame({'max_annual_prcp_mm': [max_prcp]})
        max_prep_df.to_csv(out_path, index=False)
        print(f'Save {out_path}')

    return max_prcp


# function to calculate daily rainfall variability
def cal_variability(df, date_col='DATE', prcp_col='PRCP'):
   
    # Copy data to avoid modifying original DataFrame
    df_out = df.copy()
    df_out.set_index(date_col, inplace=True)

    # Calculate annual std for original data
    std_original = df_out.groupby(df_out.index.year)[prcp_col].std()
    
    # Calculate daily anomaly (remove seasonal cycle)
    # Extract month-day
    df_out['month_day'] = df_out.index.strftime('%m-%d')
    # Calculate multi-year average daily rainfall for each month-day
    clim_daily = df_out.groupby('month_day')[prcp_col].mean()
    # Map climatology to all dates
    df_out['clim_daily'] = df_out['month_day'].map(clim_daily)
    # Calculate anomaly
    df_out['anomaly'] = df_out[prcp_col] - df_out['clim_daily']
    
    # Detrend use linear regression
    # Linear regression fitting
    time_series = df_out['anomaly']
    time_index = (df_out.index - df_out.index[0]).days
    slope, intercept, _, _, _ = linregress(time_index, time_series)
    # Calculate trend values (for all positions, including NaN)
    model_series = slope * time_index + intercept
    # Detrend
    df_out['detrend'] = time_series - model_series
    
    # Calculate annual std for detrended data
    std_detrend = df_out.groupby('year')['detrend'].std()
    
    return std_original, std_detrend


# function to calculate rainfall unevenness
def cal_D_S_Ratio(inpath, max_prcp, out_dir, overwrite):

    dataname = inpath.split(os.sep)[-3].split('_')[0]
    outname = os.path.basename(inpath)
    station = outname.split('.')[0]
    outname = f'{dataname}_{outname}'
    outpath = os.path.join(out_dir, outname)
    if os.path.exists(outpath) and not overwrite:
        print(f'{outpath} has already existed')
        result_df = pd.read_csv(outpath)
    else:
        if overwrite:
            print(f'Overwriting {outpath}...')
        else:
            print(f'{outpath} does not exist, preprocessing...')
        
        df = pd.read_csv(inpath)
        df.loc[df['PRCP'] < 0.1, 'PRCP'] = 0
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')

        # calculate rianfall variability for reference
        std_original, std_detrend = cal_variability(df)

        # calculate rianfall unevenness
        grouped = df.groupby('year')
        results = []
        for year, group in grouped:
            prcp = group['PRCP']
            # annual precipitation
            R = prcp.sum()
            # cal index
            frequency_daily = len(prcp[prcp > 0])
            m_daily = len(prcp.dropna())
            prcp_monthly = group.resample('ME', on='DATE')['PRCP'].sum()
            m_monthly = len(prcp_monthly.dropna())
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
                pi_monthly = prcp_monthly / R
                D_monthly = np.nansum(np.where((pi_monthly > 0), pi_monthly * np.log2(pi_monthly / q_monthly), 0))
                S_monthly = D_monthly * PRCP_ratio

            # add result
            lon = round(group['LONGITUDE'].iloc[0].item(), 3)
            if lon > 180:
                lon = lon - 360
                lon = round(lon, 3)
            lat = round(group['LATITUDE'].iloc[0].item(), 3)
            results.append({
                'dataname': dataname,
                'station': station,
                'lon': lon,
                'lat': lat,
                'year': year,
                'D_daily': D_daily,
                'D_monthly': D_monthly,
                'S_daily': S_daily,
                'S_monthly': S_monthly,
                'Annual_PRCP_mm': R,
                'PRCP_ratio': PRCP_ratio,
                'valid_day': m_daily,
                'rain_day': frequency_daily,
                'STD_daily_orig': std_original.loc[year].item(),
                'STD_daily_detr': std_detrend.loc[year].item()   
            })

        # save result
        result_df = pd.DataFrame(results)
        result_df.to_csv(outpath, index=False)
        print(f'Saving {outpath}')
        
    return result_df


def sens_slope(x, y):
    ''' Function to calculate sensitivity slope considering the actual time series '''
    idx = 0
    n = len(x)
    d = np.ones(int(n*(n-1)/2)) 
    
    for i in range(n-1):
        j = np.arange(i+1,n)
        d[idx : idx + len(j)] = (x[j] - x[i]) / (y[j] - y[i])
        idx = idx + len(j)
    
    slope = np.nanmedian(d)

    return slope


# function to calculate mean and trend
def calculate_mean_trend(df):

    n_meta = 4
    valid_df = df.dropna()
    # calculate multi-year mean
    col_ls = valid_df.columns
    station_df = valid_df[col_ls[:n_meta]].iloc[0]
    mean_col_ls = [f'{col}_mean' for col in col_ls[n_meta+1:]]
    mean_df = valid_df[col_ls[n_meta+1:]].mean()
    for col, mean_col in zip(col_ls[n_meta+1:], mean_col_ls):
        station_df[mean_col] = mean_df[col]
    # calculate trend
    trend_col_ls = [f'{col}_trend' for col in col_ls[n_meta+1:]]
    p_col_ls = [f'{col}_p_value' for col in col_ls[n_meta+1:]]
    for col, col_trend, col_p in zip(col_ls[n_meta+1:], trend_col_ls, p_col_ls):
        col_df = valid_df[['year', col]]
        if len(col_df) < 2:
            station_df[col_trend] = np.nan
            station_df[col_p] = np.nan
        try:
            # # linear regression
            # slope, _, _, p_value, _ = linregress(col_df['year'], col_df[col])
            # station_df[col_trend] = slope
            # station_df[col_p] = p_value
            # print(f'{col} trend: {slope}, p-value: {p_value}')
            # Mann-Kendall test, the slope do not consider the real time series
            result = mk.original_test(col_df[col].values)
            p_value = result.p
            # update slope
            slope = sens_slope(col_df[col].values, col_df['year'].values)
            station_df[col_trend] = slope
            station_df[col_p] = p_value
        except Exception as e:
            print(e)
            station_df[col_trend] = np.nan
            station_df[col_p] = np.nan

    return pd.DataFrame(station_df).T


def main():

    t1 = time.time()

    max_prcp = cal_max_prep(IN_DIR_LS, OUT_PATH_MAX_PRCP, OVERWRITE)
    print(f'maximum annual precipitation: {max_prcp} mm')
    valid_file_ls = []
    for in_dir in IN_DIR_LS:
        valid_files = os.listdir(in_dir)
        for f in valid_files:
            filepath = os.path.join(in_dir, f)
            valid_file_ls.append(filepath)
    # multiprocess
    num_processes = min(100, cpu_count())
    with Pool(processes=num_processes) as pool:
        all_result = pool.starmap(
            cal_D_S_Ratio,
            [(valid_file, max_prcp, OUT_DIR_IDX, OVERWRITE) for valid_file in valid_file_ls]
        )
    print('COMPLETE calculating rainfall unevenness')

    overwrite = OVERWRITE

    if os.path.exists(OUT_DIR_MEAN_TREND) and not overwrite:
        print(f'{OUT_DIR_MEAN_TREND} has already existed')
    else:
        if overwrite:
            print(f'Overwriting {OUT_DIR_MEAN_TREND}...')
        else:
            print(f'{OUT_DIR_MEAN_TREND} does not exist, preprocessing...')
        # multiprocess
        with Pool(processes=num_processes) as pool:
            all_station_df = pool.map(calculate_mean_trend, all_result)
        station_df = pd.concat(all_station_df, ignore_index=True)
        # average those with the same location but different data source
        agg_dict = {
            'dataname': 'first',  # Keep first data source and station name
            'station': 'first', 
            # For all other numeric columns, take mean
            **{col: 'mean' for col in station_df.columns 
            if col not in ['lon', 'lat', 'dataname', 'station']}
        }
        station_df = station_df.groupby(['lon', 'lat'], as_index=False).agg(agg_dict)
        station_df.to_csv(OUT_DIR_MEAN_TREND, index=False)
        print('COMPLETE calculating mean and trend for each station')

        all_result_df = pd.concat(all_result, ignore_index=True)
        global_df = all_result_df.iloc[:, 4:].groupby('year').mean()
        global_df.to_csv(OUT_DIR_MEAN_TREND_GLOBAL, index=True)
        print('COMPLETE calculating mean and trend at global scale')

        # average by regions
        outdir = os.path.dirname(OUT_DIR_MEAN_TREND_GLOBAL)
        for region, (lon_min, lon_max, lat_min, lat_max) in REGIONS.items():
            region_df = all_result_df[
                (all_result_df['lon'] >= lon_min) & 
                (all_result_df['lon'] <= lon_max) & 
                (all_result_df['lat'] >= lat_min) & 
                (all_result_df['lat'] <= lat_max)
            ].iloc[:, 4:].groupby('year').mean()
            outname = f"region_{region.replace(' ', '_')}_station.csv"
            outpath = os.path.join(outdir, outname)
            region_df.to_csv(outpath, index=True)
            print(f'COMPLETE calculating mean and trend for {region}')

    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")

    return


if __name__ == "__main__":
    
    main()
    
