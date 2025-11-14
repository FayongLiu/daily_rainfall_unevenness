# -*- coding: utf-8 -*-
# Fayong Liu
# 11/14/2025
# Code for counting and selecting the valid station in China station data
# standard
# valid day: PRCP >= 0
# valid year: valid day >= 0.75 * total day
# valid station: 2000-2020, valid year >= 15 and 1980-2020, valid year >= 30


import os
import pandas as pd
import numpy as np
from multiprocessing import Pool, cpu_count
import itertools
import time
from pre_isd_select_valid_station import cal_total_days, START_YEAR, END_YEAR, TH_YEAR


DATA_DIR = r'../data/China_station_1961_2021/'
OUT_DIR = rf'../data/isd_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'
os.makedirs(OUT_DIR, exist_ok=True)


# def a function to check a valid station
def check_station(station):
    filename = os.path.join(DATA_DIR, station)
    df = pd.read_csv(filename, sep='\s+', header=None,
                     names=['STATION', 'LATITUDE', 'LONGITUDE', 'ELEVATION',
                            'year', 'month', 'day', 'PRCP'])
    df['DATE'] = pd.to_datetime(df[['year', 'month', 'day']])
    df_valid = df[
        (df['year'] >= START_YEAR) &
        (df['year'] <= END_YEAR) &
        (df['PRCP'] >= 0) &
        (~df['DATE'].isna())
    ].copy()
    counts = df_valid.groupby('year')['PRCP'].count()
    counts = counts.reindex(range(START_YEAR, END_YEAR+1), fill_value=0)
    total_days = pd.Series(
        [cal_total_days(year) for year in range(START_YEAR, END_YEAR+1)],
        index=range(START_YEAR, END_YEAR+1)
    )
    valid_years = counts >= 0.75 * total_days
    if valid_years.sum() >= TH_YEAR:
        # save result
        outname = os.path.join(OUT_DIR, station.replace('.txt', '.csv'))
        valid_col = ['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'PRCP', 'year']
        df_valid[valid_col].to_csv(outname, index=False)
        print(outname)

        return 1

    else:

        return 0


# check valid station across year
def main():
    station_ls = os.listdir(DATA_DIR)
    station_ls.sort()
    num_processes = min(50, cpu_count())

    with Pool(processes=num_processes) as pool:
        result = pool.map(check_station, station_ls)

    valid_station_num = np.sum(np.array(result))
    print(f'Numbers of valid station: {valid_station_num}')

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