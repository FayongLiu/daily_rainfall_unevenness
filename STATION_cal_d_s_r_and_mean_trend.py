# -*- coding: utf-8 -*- 
import os 
import pandas as pd 
import numpy as np 
from scipy.stats import linregress 
import logging 
from datetime import datetime 
import multiprocessing

DATA_DIR = r"/data1/fyliu/f_rainfall_varaibility_daily_monthly/data/isd_daily_prep_1980_2020/" 
OUT_DIR = r'/data1/yyzhao/data/1980-2020/finally_result/data/v3_station_d_s/' 
NEW_OUT_DIR = r'/data1/yyzhao/data/1980-2020/finally_result/data/v3_station_d_s/mean_trend' 
os.makedirs(OUT_DIR, exist_ok=True) 
os.makedirs(NEW_OUT_DIR, exist_ok=True) 

# 首先计算最大降水量
valid_station = os.listdir(DATA_DIR)
max_prep = 0
for station in valid_station:
    filepath = os.path.join(DATA_DIR, station)
    df = pd.read_csv(filepath)
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce') 
    df.loc[df['DATE'].isna(), 'PRCP'] = np.nan 
    annual_R = df.groupby(df['DATE'].dt.year)['PRCP'].sum(min_count=1).dropna()
    if not annual_R.empty:
        max_prep = max(max_prep, annual_R.max())
print(f'maximum annual precipitation: {max_prep}')

def cal_D_S(station): 
    filepath = os.path.join(DATA_DIR, station) 
    df = pd.read_csv(filepath) 
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce') 
    # deal with null date or negative prep value 
    df.loc[df['DATE'].isna(), 'PRCP'] = np.nan 
    df.loc[df['PRCP'] < 0, 'PRCP'] = np.nan 
    # Extract year from the 'DATE' column 
    df['YEAR'] = df['DATE'].dt.year 
    grouped = df.groupby('YEAR') 
    results = [] 
    for year, group in grouped: 
        prep = group['PRCP'] 
        # annual precipitation 
        R = prep.sum() 
        # cal D values 
        if R <= 0: 
            D_daily = S_daily = np.nan 
            D_monthly = S_monthly = np.nan 
            PRCP_ratio = np.nan 
        else: 
            # daily 
            m = len(prep.dropna()) 
            q = 1 / m 
            pi = prep / R 
            D_daily = np.nansum(np.where((pi > 0), pi * np.log2(pi / q), 0)) 
            PRCP_ratio = R / max_prep
            S_daily = D_daily * PRCP_ratio 
            # monthly 
            monthly_prep = group.resample('ME', on='DATE')['PRCP'].sum() 
            monthly_m = len(monthly_prep.dropna()) 
            monthly_q = 1 / monthly_m 
            monthly_pi = monthly_prep / R 
            D_monthly = np.nansum(np.where((monthly_pi > 0), monthly_pi * np.log2(monthly_pi / monthly_q), 0)) 
            S_monthly = D_monthly * PRCP_ratio 
            
             
        # add result 
        results.append({ 
            'station': group['STATION'].iloc[0], 
            'name': group['NAME'].iloc[0], 
            'lon': group['LONGITUDE'].iloc[0], 
            'lat': group['LATITUDE'].iloc[0], 
            'year': year, 
            'D_daily': D_daily, 
            'D_monthly': D_monthly, 
            'S_daily': S_daily, 
            'S_monthly': S_monthly, 
            'Annual_PRCP_mm': R, 
            'PRCP_ratio': PRCP_ratio, 
        }) 
    
    # 将结果保存到文件
    result_df = pd.DataFrame(results)
    output_file = os.path.join(OUT_DIR, f'{station}.csv')
    result_df.to_csv(output_file, index=False)
    
    return results 

def calculate_trend(series, station_name, variable_name): 
    # 删除 nan 值
    valid_data = series.dropna()
    
    if len(valid_data) < 2:
        print(f"{station_name} {variable_name} cant cal")
        return np.nan, np.nan 
        
    try:
        slope, _, _, p_value, _ = linregress(range(len(valid_data)), valid_data) 
        return slope, p_value
    except Exception as e:
        print(f"{station_name} {variable_name} error:{str(e)}")
        return np.nan, np.nan


# 处理所有站点数据
num_processes = 40
with multiprocessing.Pool(processes=num_processes) as pool: 
    all_results = pool.map(cal_D_S, valid_station) 
print('\nCOMPLETE cal S values!') 

# 合并所有站点的统计结果
all_stats = []
# 在统计分析部分修改为：
for station in valid_station:
    stats_file = os.path.join(OUT_DIR, f'{station}.csv')
    if os.path.exists(stats_file):
        df = pd.read_csv(stats_file)
        
        print(f"\nstation:{station}")
        print(f"total num:{len(df)}")
        print(f"D_daily: {df['D_daily'].count()}")
        print(f"D_monthly: {df['D_monthly'].count()}")
        print(f"S_daily: {df['S_daily'].count()}")
        print(f"S_monthly: {df['S_monthly'].count()}")
        print(f"PRCP_ratio: {df['PRCP_ratio'].count()}")
        
        # 计算均值
        station_stats = {
            'station': station,
            'lon': df['lon'].iloc[0], 
            'lat': df['lat'].iloc[0], 
            'D_daily_mean': df['D_daily'].mean(),
            'D_monthly_mean': df['D_monthly'].mean(),
            'S_daily_mean': df['S_daily'].mean(),
            'S_monthly_mean': df['S_monthly'].mean(),
            'PRCP_ratio_mean': df['PRCP_ratio'].mean(),
            'valid_years_count': len(df['D_daily'].dropna())
        }
        
        # 计算趋势
        D_daily_slope, D_daily_p = calculate_trend(df['D_daily'], station, 'D_daily')
        D_monthly_slope, D_monthly_p = calculate_trend(df['D_monthly'], station, 'D_monthly')
        S_daily_slope, S_daily_p = calculate_trend(df['S_daily'], station, 'S_daily')
        S_monthly_slope, S_monthly_p = calculate_trend(df['S_monthly'], station, 'S_monthly')
        PRCP_ratio_slope, PRCP_ratio_p = calculate_trend(df['PRCP_ratio'], station, 'PRCP_ratio')
        
        # 添加趋势统计
        station_stats.update({
            'D_daily_trend': D_daily_slope,
            'D_daily_p_value': D_daily_p,
            'D_monthly_trend': D_monthly_slope,
            'D_monthly_p_value': D_monthly_p,
            'S_daily_trend': S_daily_slope,
            'S_daily_p_value': S_daily_p,
            'S_monthly_trend': S_monthly_slope,
            'S_monthly_p_value': S_monthly_p,
            'PRCP_ratio_trend': PRCP_ratio_slope,
            'PRCP_ratio_p_value': PRCP_ratio_p
        })
        
        all_stats.append(station_stats)

# 保存所有站点的统计结果
final_stats_df = pd.DataFrame(all_stats)
final_stats_df.to_csv(os.path.join(NEW_OUT_DIR, 'd_s_r_mean_trend.csv'), index=False)
print('Statistics calculation completed!')
