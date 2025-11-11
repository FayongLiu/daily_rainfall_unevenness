# -*- coding: utf-8 -*-
# Fayong Liu
# 4/8/2025
# Code for concatenating valid stations at different years and preprocess
# For precipitation, PRCP
# 1. PRCP != 99.99, PRCP_ATTRIBUTES in [D, F, G]
# 2. convert unit, current unit (inch), 1 inch = 25.4 mm


import os
import pandas as pd
from multiprocessing import Pool, cpu_count
import time
from pre_isd_select_valid_station import cal_total_days, START_YEAR, END_YEAR, TH_YEAR


DATA_DIR = r'/data1/zxy/sudden_temp_change/ISD-global-daily/unzip/'
VALID_STATIONS_PATH = rf'../data/isd_valid_stations/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}.csv'
OUT_DIR = rf'../data/isd_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'
os.makedirs(OUT_DIR, exist_ok=True)


# function to deal with a station
def preprocess_station(station):
    data_ls = []
    for year in range(START_YEAR, END_YEAR + 1):
        filename = os.path.join(DATA_DIR, str(int(year)), station)
        if os.path.exists(filename):
            data = pd.read_csv(
                filename, usecols=['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'NAME', 'PRCP', 'PRCP_ATTRIBUTES']
            )
            data_ls.append(data)
    df = pd.concat(data_ls, axis=0, ignore_index=True)
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    df_valid = df[
        (df['PRCP'] >= 0) &
        (df['PRCP'] != 99.99) &
        (df['PRCP_ATTRIBUTES'].isin(['D', 'F', 'G'])) &
        (~df['DATE'].isna())
    ].copy()
    df_valid['PRCP'] = df_valid['PRCP'] * 25.4
    df_valid['year'] = df_valid['DATE'].dt.year
    year_counts = df_valid['year'].value_counts().sort_index()

    # valid year: valid day >= 0.75 * total day
    valid_years = [
        y for y in year_counts.index
        if year_counts[y] >= 0.75 * cal_total_days(int(y))
    ]
    df_valid = df_valid[df_valid['year'].isin(valid_years)]

    outname = os.path.join(OUT_DIR, station)
    df_valid.to_csv(outname, index=False)
    print(outname)

    return


def main():
    valid_station = pd.read_csv(VALID_STATIONS_PATH, usecols=['Station'], dtype={'Station': str})
    num_processes = min(100, cpu_count())
    with Pool(processes=num_processes) as pool:
        pool.map(preprocess_station, valid_station['Station'])
    print('\nCOMPLETE')

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