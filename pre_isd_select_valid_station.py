# -*- coding: utf-8 -*-
# Fayong Liu
# 4/8/2025
# Code for counting and selecting the valid station in ISD
# standard
# valid day: PRCP >= 0, PRCP != 99.99, PRCP_ATTRIBUTES in [D, F, G], valid date
# valid year: valid day >= 0.75 * total day
# valid station: 2000-2020, valid year >= 15 or 1980-2020, valid year >= 30, respectively
# finally total 2427 and 633 valid stations, respectively


import os
import pandas as pd
from multiprocessing import Pool, cpu_count
import calendar
import itertools
import time


DATA_DIR = r'/data1/zxy/sudden_temp_change/ISD-global-daily/unzip/'
OUT_DIR = r'../data/isd_valid_stations'
os.makedirs(OUT_DIR, exist_ok=True)
START_YEAR = 1980
END_YEAR = 2020
TH_YEAR = 30


# def a function to cal the total days of a year
def cal_total_days(year):
    if calendar.isleap(year):
        return 366
    else:
        return 365


# def a function to check valid station in each year
def check_year(year):
    filedir = os.path.join(DATA_DIR, str(int(year)))
    filename_ls = os.listdir(filedir)
    filename_ls.sort()
    total_days = cal_total_days(year)
    valid_stations = []
    for filename in filename_ls:
        filepath = os.path.join(filedir, filename)
        df = pd.read_csv(filepath, usecols=['DATE', 'PRCP', 'PRCP_ATTRIBUTES'])
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        df_valid = df[
            (df['PRCP'] >= 0) &
            (df['PRCP'] != 99.99) &
            (df['PRCP_ATTRIBUTES'].isin(['D', 'F', 'G'])) &
            (~df['DATE'].isna())
        ]
        valid_days = df_valid.shape[0]
        if (valid_days >= (0.75 * total_days)):
            valid_stations.append(filename)

    return valid_stations


# check valid station across year
def main():
    year_ls = range(START_YEAR, END_YEAR+1)
    num_processes = min(len(year_ls), cpu_count())

    with Pool(processes=num_processes) as pool:
        result = pool.map(check_year, year_ls)

    all_stations = list(itertools.chain(*result))
    station_counts = pd.Series(all_stations).value_counts()
    station_counts = station_counts.reset_index()
    station_counts.columns = ['Station', 'Count']
    station_counts = station_counts[station_counts['Count'] >= TH_YEAR]

    print(f'Numbers of valid station: {len(station_counts)}')
    output_file = os.path.join(OUT_DIR, f'{START_YEAR}_{END_YEAR}_gte{TH_YEAR}.csv')
    station_counts.to_csv(output_file, index=False)
    print(output_file)

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