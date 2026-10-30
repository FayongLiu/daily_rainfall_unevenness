# Function to preprocess station data
# Including ISD, GHCNd, China Meteorological Adimistration station (CMA), eta

# Criteria
# Valid day for ISD: PRCP >= 0, PRCP != 99.99, PRCP_ATTRIBUTES in ['D', 'F', 'G'], valid date
# Valid day for GHCNd: PRCP >= 0 (missing value, -9999), Measurement flag (MF) in ['', 'B', 'D', 'T'], 
# Quality flag (QF) == '', Source flag (SF) != '', valid date
# Valid day for CMA: PRCP >= 0 (missing value, -999.00), valid date
# Valid day for CDC: RS or RSK >= 0 (missing value, -999.00), QN_6 or QN_4==10, valid date
# Valid day for SWISS: rka150d0/rre150d0 >= 0, valid date
# Valid day for ECA and SACA: RR >= 0, Q_RR == 0, valid date
# Valid day for HPD: DlySum >= 0, DlySumQF != 'P', valid date
# Valid year: valid day >= 0.75 * total days
# Valid station: valid year >= th_yr


import os
import pandas as pd
from multiprocessing import Pool, cpu_count
import calendar
import itertools
import numpy as np
import zipfile


def get_total_days(year):
    ''' Function to calculate the total days of a year '''

    if calendar.isleap(year):
        return 366
    else:
        return 365


def _valid_station_isd(year, indir_base):
    ''' Function to check valid station in each year for ISD '''

    filedir = os.path.join(indir_base, str(int(year)))
    filename_ls = os.listdir(filedir)
    filename_ls.sort()
    total_days = get_total_days(year)
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


def valid_station_isd(st_yr, end_yr, th_yr, indir_base, outdir, overwrite):
    ''' Function to check valid station across years for ISD '''

    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f'{st_yr}_{end_yr}_gte{th_yr}.csv')
    if os.path.exists(outpath):
        if overwrite:
            print(f'Overwriting {outpath}...')   
        else:
            print(f'{outpath} already exists, skip...')
            return
    else:
        print(f'{outpath} does not exist, preprocessing...')
    
    year_ls = range(st_yr, end_yr+1)
    num_processes = min(len(year_ls), cpu_count())

    with Pool(processes=num_processes) as pool:
        result = pool.starmap(_valid_station_isd, [(year, indir_base) for year in year_ls])

    all_stations = list(itertools.chain(*result))
    station_counts = pd.Series(all_stations).value_counts()
    station_counts = station_counts.reset_index()
    station_counts.columns = ['Station', 'Count']
    station_counts = station_counts[station_counts['Count'] >= th_yr]

    print(f'Numbers of valid station for ISD: {len(station_counts)}')
    station_counts.to_csv(outpath, index=False)
    print(f'Saving {outpath}...')

    return


def _concat_station_isd(station, st_yr, end_yr, indir, outdir, overwrite):
    ''' Function to concatenate each valid station across years for ISD '''

    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, station)
    if os.path.exists(outpath):
        if overwrite:
            print(f'Overwriting {outpath}...')   
        else:
            print(f'{outpath} already exists, skip...')
            return
    else:
        print(f'{outpath} does not exist, preprocessing...')

    data_ls = []
    for year in range(st_yr, end_yr + 1):
        inpath = os.path.join(indir, str(int(year)), station)
        if os.path.exists(inpath):
            data = pd.read_csv(
                inpath, usecols=['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'PRCP', 'PRCP_ATTRIBUTES']
            )
            data_ls.append(data)
        else:
            print(f'{inpath} does not exist, skip...')
    df = pd.concat(data_ls, axis=0, ignore_index=True)
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    df_valid = df[
        (df['PRCP'] >= 0) &
        (df['PRCP'] != 99.99) &
        (df['PRCP_ATTRIBUTES'].isin(['D', 'F', 'G'])) &
        (~df['DATE'].isna())
    ].copy()
    df_valid['PRCP'] = df_valid['PRCP'] * 25.4  # 1 inch = 25.4 mm
    df_valid['year'] = df_valid['DATE'].dt.year
    year_counts = df_valid['year'].value_counts().sort_index()

    # Valid year: valid day >= 0.75 * total day
    valid_years = [
        y for y in year_counts.index
        if year_counts[y] >= 0.75 * get_total_days(int(y))
    ]
    df_valid = df_valid[df_valid['year'].isin(valid_years)]
    valid_col = ['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'PRCP', 'year']
    df_valid[valid_col].to_csv(outpath, index=False)
    print(f'Saving {outpath}...')

    return


def concat_station_isd(inpath, st_yr, end_yr, indir, outdir, overwrite):
    ''' Function to concatenate all valid stations across years for ISD '''

    valid_station = pd.read_csv(inpath, usecols=['Station'], dtype={'Station': str})
    num_processes = min(100, cpu_count())
    with Pool(processes=num_processes) as pool:
        pool.starmap(_concat_station_isd, 
                     [(station, st_yr, end_yr, indir, outdir, overwrite) for station in valid_station['Station']])
    print('\nComplete concatenating all valid stations for ISD!')

    return


def _valid_station_ghcnd_cma_hpd(station, indir, st_yr, end_yr, th_yr, outdir, data_name, overwrite):
    ''' Function to check each valid station for GHCNd, CMA, and HPD '''

    os.makedirs(outdir, exist_ok=True)
    outname = station.replace('.txt', '.csv') if data_name == 'cma' else station
    outpath = os.path.join(outdir, outname)
    if os.path.exists(outpath):
        if overwrite:
            print(f'Overwriting {outpath}...')   
        else:
            print(f'{outpath} already exists, skip...')
            return 1
    else:
        print(f'{outpath} does not exist, preprocessing...')

    inpath = os.path.join(indir, station)
    try:
        if data_name == 'cma':
            df = pd.read_csv(inpath, sep='\s+', header=None, 
                            names=['STATION', 'LATITUDE', 'LONGITUDE', 'ELEVATION',
                                    'year', 'month', 'day', 'PRCP'])
            df['DATE'] = pd.to_datetime(df[['year', 'month', 'day']])
            df_valid = df[
                (df['year'] >= st_yr) &
                (df['year'] <= end_yr) &
                (df['PRCP'] >= 0) &
                (~df['DATE'].isna())
            ].copy()
        elif data_name == 'ghcnd':
            df = pd.read_csv(
                inpath, usecols=['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'PRCP', 'PRCP_ATTRIBUTES'],
                dtype={'PRCP': float, 'PRCP_ATTRIBUTES': str}
            )
            df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
            df['MF'] = df['PRCP_ATTRIBUTES'].str.split(',').str[0]
            df['QF'] = df['PRCP_ATTRIBUTES'].str.split(',').str[1]
            df['SF'] = df['PRCP_ATTRIBUTES'].str.split(',').str[2]
            df['year'] = df['DATE'].dt.year
            df_valid = df[
                (df['year'] >= st_yr) &
                (df['year'] <= end_yr) &
                (df['PRCP'] >= 0) &
                (df['MF'].isin(['', 'B', 'D', 'T'])) &
                (df['QF'] == '') &
                (df['SF'] != '') &
                (~df['DATE'].isna())
            ].copy()
            df_valid['PRCP'] = df_valid['PRCP'] / 10
        elif data_name == 'hpd':
            df = pd.read_csv(
                inpath, usecols=['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'DlySum', 'DlySumQF']
            )
            df['PRCP'] = df['DlySum'].astype(float) * 25.4 / 100 # convert 1/100 inch to mm
            df['DlySumQF'] = df['DlySumQF'].astype(str)
            df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
            df['year'] = df['DATE'].dt.year
            df_valid = df[
                (df['year'] >= st_yr) &
                (df['year'] <= end_yr) &
                (df['PRCP'] >= 0) &
                (df['DlySumQF'] != 'P') &
                (~df['DATE'].isna())
            ].copy()
        else:
            raise ValueError(f'Invalid data name: {data_name}')
    except Exception as e:
        print(f'{inpath} encountered error: {e}, skip...')
        return 0

    counts = df_valid.groupby('year')['PRCP'].count()
    counts = counts.reindex(range(st_yr, end_yr+1), fill_value=0)
    total_days = pd.Series(
        [get_total_days(year) for year in range(st_yr, end_yr+1)],
        index=range(st_yr, end_yr+1)
    )
    valid_years = counts >= 0.75 * total_days
    if valid_years.sum() >= th_yr:
        # Save result
        valid_col = ['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'PRCP', 'year']
        df_valid[valid_col].to_csv(outpath, index=False)
        print(f'Saving {outpath}')

        return 1

    else:

        return 0


def valid_station_ghcnd_cma_hpd(indir, st_yr, end_yr, th_yr, outdir, data_name, overwrite):
    ''' Function to check all valid stations for GHCNd, CMA, and HPD '''

    station_ls = os.listdir(indir)
    station_ls = [station for station in station_ls if (station.endswith('.txt')) or (station.endswith('.csv'))]
    station_ls.sort()
    num_processes = min(100, cpu_count())
    with Pool(processes=num_processes) as pool:
        result = pool.starmap(_valid_station_ghcnd_cma_hpd, 
                              [(station, indir, st_yr, end_yr, th_yr, outdir, data_name, overwrite) for station in station_ls])
    valid_station_num = np.sum(np.array(result))
    print(f'Numbers of valid station for {data_name.upper()}: {valid_station_num}')

    return


def _valid_station_cdc(inname, indir, st_yr, end_yr, th_yr, outdir, var_name, overwrite):
    ''' Function to check each valid station for CDC '''

    station = inname.split('_')[2]
    os.makedirs(outdir, exist_ok=True)
    outname = f'{var_name}_{station}.csv'
    outpath = os.path.join(outdir, outname)
    if os.path.exists(outpath):
        if overwrite:
            print(f'Overwriting {outpath}...')   
        else:
            print(f'{outpath} already exists, skip...')
            return 1
    else:
        print(f'{outpath} does not exist, preprocessing...')

    if var_name == 'prcp':
        qn_name = 'QN_6'
        prcp_name = 'RS'
    elif var_name == 'weather':
        qn_name = 'QN_4'
        prcp_name = 'RSK'
    else:
        raise ValueError(f'Invalid variable name: {var_name}')

    inpath = os.path.join(indir, inname)
    try:
        # Load data file in zip
        with zipfile.ZipFile(inpath, 'r') as zip_ref:
            files = zip_ref.namelist()
            file = [f for f in files if 'produkt' in f and f.endswith('.txt')][0]
            with zip_ref.open(file) as f:
                df = pd.read_csv(f, sep=';', skipinitialspace=True, encoding='latin1', usecols=['MESS_DATUM', qn_name, prcp_name])
                df['DATE'] = pd.to_datetime(df['MESS_DATUM'], format='%Y%m%d', errors='coerce')
                df['year'] = df['DATE'].dt.year
                df_valid = df[
                    (df['year'] >= st_yr) &
                    (df['year'] <= end_yr) &
                    (df[prcp_name] >= 0) &
                    (df[qn_name] == 10) &
                    (~df['DATE'].isna())
                ].copy()
            # Get location
            file = [f for f in files if 'Metadaten_Geographie_' in f and f.endswith('.txt')][0]
            with zip_ref.open(file) as f:
                df_mata = pd.read_csv(f, sep=';', skipinitialspace=True, encoding='latin1', usecols=['Geogr.Breite', 'Geogr.Laenge'], 
                                      dtype={'Geogr.Breite': float, 'Geogr.Laenge': float})
                lat = df_mata['Geogr.Breite'].values[-1]
                lon = df_mata['Geogr.Laenge'].values[-1]
    except Exception as e:
        print(f'{inpath} encountered error: {e}, skip...')
        return 0

    counts = df_valid.groupby('year')[prcp_name].count()
    counts = counts.reindex(range(st_yr, end_yr+1), fill_value=0)
    total_days = pd.Series(
        [get_total_days(year) for year in range(st_yr, end_yr+1)],
        index=range(st_yr, end_yr+1)
    )
    valid_years = counts >= 0.75 * total_days
    if valid_years.sum() >= th_yr:
        # Save result
        df_valid['STATION'] = station
        df_valid['LATITUDE'] = lat
        df_valid['LONGITUDE'] = lon
        df_valid['PRCP'] = df_valid[prcp_name]
        valid_col = ['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'PRCP', 'year']
        df_valid[valid_col].to_csv(outpath, index=False)
        print(f'Saving {outpath}')

        return 1

    else:

        return 0


def valid_station_cdc(indir, st_yr, end_yr, th_yr, outdir, var_name, overwrite):
    ''' Function to check all valid stations for CDC '''

    inname_ls = os.listdir(indir)
    inname_ls = [inname for inname in inname_ls if inname.endswith('.zip')]
    inname_ls.sort()
    num_processes = min(100, cpu_count())
    with Pool(processes=num_processes) as pool:
        result = pool.starmap(_valid_station_cdc, 
                              [(inname, indir, st_yr, end_yr, th_yr, outdir, var_name, overwrite) for inname in inname_ls])
    valid_station_num = np.sum(np.array(result))
    print(f'Numbers of valid station for CDC {var_name.upper()}: {valid_station_num}')

    return


def _valid_station_swiss(station_df, inname, indir, st_yr, end_yr, th_yr, outdir, var_name, overwrite):
    ''' Function to check each valid station for SWISS '''

    station = inname.split('_')[1]
    os.makedirs(outdir, exist_ok=True)
    outname = f'{var_name}_{station}.csv'
    outpath = os.path.join(outdir, outname)
    if os.path.exists(outpath):
        if overwrite:
            print(f'Overwriting {outpath}...')   
        else:
            print(f'{outpath} already exists, skip...')
            return 1
    else:
        print(f'{outpath} does not exist, preprocessing...')


    if var_name in ['aps', 'aws']:
        use_cols = ['reference_timestamp', 'rre150d0', 'rka150d0']
    elif var_name == 'mps':
        use_cols = ['reference_timestamp', 'rre150d0']
    else:
        raise ValueError(f'Invalid variable name: {var_name}')

    inpath = os.path.join(indir, inname)
    try:
        df = pd.read_csv(inpath, usecols=use_cols)
        df['DATE'] = pd.to_datetime(df['reference_timestamp'], format='%d.%m.%Y %H:%M', errors='coerce')
        df['year'] = df['DATE'].dt.year
        if var_name == 'mps':
            prcp_name = 'rre150d0'
        else:
            notnan_len_rre = df['rre150d0'].notna().sum()
            notnan_len_rka = df['rka150d0'].notna().sum()
            prcp_name = 'rre150d0' if notnan_len_rre > notnan_len_rka else 'rka150d0'
        df_valid = df[
            (df['year'] >= st_yr) &
            (df['year'] <= end_yr) &
            (df[prcp_name] >= 0) &
            (~df['DATE'].isna())
        ].copy()
        # Get location
        station_idx = station.upper()
        lat = station_df.loc[station_df['station_abbr'] == station_idx, 'station_coordinates_wgs84_lat'].values[0]
        lon = station_df.loc[station_df['station_abbr'] == station_idx, 'station_coordinates_wgs84_lon'].values[0]
    except Exception as e:
        print(f'{inpath} encountered error: {e}, skip...')
        return 0

    counts = df_valid.groupby('year')[prcp_name].count()
    counts = counts.reindex(range(st_yr, end_yr+1), fill_value=0)
    total_days = pd.Series(
        [get_total_days(year) for year in range(st_yr, end_yr+1)],
        index=range(st_yr, end_yr+1)
    )
    valid_years = counts >= 0.75 * total_days
    if valid_years.sum() >= th_yr:
        # Save result
        df_valid['STATION'] = station
        df_valid['LATITUDE'] = lat
        df_valid['LONGITUDE'] = lon
        df_valid['PRCP'] = df_valid[prcp_name]
        valid_col = ['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'PRCP', 'year']
        df_valid[valid_col].to_csv(outpath, index=False)
        print(f'Saving {outpath}')

        return 1

    else:

        return 0


def valid_station_swiss(station_path, indir, st_yr, end_yr, th_yr, outdir, data_name, overwrite):
    ''' Function to check all valid stations for SWISS '''

    station_df = pd.read_csv(station_path, usecols=['station_abbr', 'station_coordinates_wgs84_lat', 'station_coordinates_wgs84_lon'],
                             dtype={'station_abbr': str, 'station_coordinates_wgs84_lat': float, 'station_coordinates_wgs84_lon': float})
    inname_ls = os.listdir(indir)
    inname_ls = [inname for inname in inname_ls if (inname.endswith('.csv')) and ('_meta_' not in inname)]
    inname_ls.sort()
    num_processes = min(100, cpu_count())
    with Pool(processes=num_processes) as pool:
        result = pool.starmap(_valid_station_swiss, 
                              [(station_df, inname, indir, st_yr, end_yr, th_yr, outdir, data_name, overwrite) for inname in inname_ls])
    valid_station_num = np.sum(np.array(result))
    print(f'Numbers of valid station for SWISS {data_name.upper()}: {valid_station_num}')

    return


def _valid_station_eca_saca(station_df, inname, indir, st_yr, end_yr, th_yr, outdir, overwrite):
    ''' Function to check each valid station for ECA and SACA '''

    station = inname.split('.')[0].split('_')[-1]
    os.makedirs(outdir, exist_ok=True)
    outname = f'{station}.csv'
    outpath = os.path.join(outdir, outname)
    if os.path.exists(outpath):
        if overwrite:
            print(f'Overwriting {outpath}...')   
        else:
            print(f'{outpath} already exists, skip...')
            return 1
    else:
        print(f'{outpath} does not exist, preprocessing...')

    inpath = os.path.join(indir, inname)
    try:
        df = pd.read_csv(inpath, sep=',', skiprows=18, skipinitialspace=True)
        df['DATE'] = pd.to_datetime(df['DATE'], format='%Y%m%d', errors='coerce')
        df['year'] = df['DATE'].dt.year
        df_valid = df[
            (df['year'] >= st_yr) &
            (df['year'] <= end_yr) &
            (df['RR'] >= 0) &
            (df['Q_RR'] == 0) &
            (~df['DATE'].isna())
        ].copy()
        # Get location
        station_idx = df['STAID'].values[0]
        lat = station_df.loc[station_df['STAID'] == station_idx, 'LAT'].values[0]
        lon = station_df.loc[station_df['STAID'] == station_idx, 'LON'].values[0]
    except Exception as e:
        print(f'{inpath} encountered error: {e}, skip...')
        return 0

    counts = df_valid.groupby('year')['RR'].count()
    counts = counts.reindex(range(st_yr, end_yr+1), fill_value=0)
    total_days = pd.Series(
        [get_total_days(year) for year in range(st_yr, end_yr+1)],
        index=range(st_yr, end_yr+1)
    )
    valid_years = counts >= 0.75 * total_days
    if valid_years.sum() >= th_yr:
        # Save result
        df_valid['STATION'] = station
        df_valid['LATITUDE'] = lat
        df_valid['LONGITUDE'] = lon
        df_valid['PRCP'] = df_valid['RR'] * 0.1 # Convert from 0.1 mm to mm
        valid_col = ['STATION', 'DATE', 'LATITUDE', 'LONGITUDE', 'PRCP', 'year']
        df_valid[valid_col].to_csv(outpath, index=False)
        print(f'Saving {outpath}')

        return 1

    else:

        return 0


def dms_to_decimal(dms_str):
    ''' Function to convert DMS string to decimal degree '''

    if pd.isna(dms_str) or dms_str == '':
        return None
    
    # Extract sign and remove it from the string
    sign = -1 if dms_str[0] == '-' else 1
    dms_str = dms_str[1:] 
    # Separate degrees, minutes, and seconds
    parts = dms_str.split(':')
    degrees = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])
    # Convert to decimal degrees
    decimal = degrees + minutes/60 + seconds/3600

    return sign * decimal


def valid_station_eca_saca(station_path, indir, st_yr, end_yr, th_yr, outdir, data_name, overwrite):
    ''' Function to check all valid stations for ECA and SACA '''

    station_df = pd.read_csv(station_path, sep=',', skiprows=17, skipinitialspace=True, usecols=['STAID', 'LAT', 'LON'],
                             dtype={'LAT': str, 'LON': str})
    station_df['LAT'] = station_df['LAT'].apply(dms_to_decimal)
    station_df['LON'] = station_df['LON'].apply(dms_to_decimal)
    inname_ls = os.listdir(indir)
    inname_ls = [inname for inname in inname_ls if (inname.endswith('.txt')) and ('RR_SOUID' in inname)]
    inname_ls.sort()
    num_processes = min(100, cpu_count())
    with Pool(processes=num_processes) as pool:
        result = pool.starmap(_valid_station_eca_saca, 
                              [(station_df, inname, indir, st_yr, end_yr, th_yr, outdir, overwrite) for inname in inname_ls])
    valid_station_num = np.sum(np.array(result))
    print(f'Numbers of valid station for {data_name.upper()}: {valid_station_num}')

    return

