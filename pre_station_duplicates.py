# Code for removing duplicate stations from GHCNd, ISD, and CMA data

import pandas as pd
import numpy as np
import os
from multiprocessing import Pool, cpu_count
from rainfall_ui.util.config import parse_args


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr


def get_reference(indir, filename):
    ''' Function to get reference stations from GHCNd data '''

    filepath = os.path.join(indir, filename)
    df = pd.read_csv(filepath, usecols=['STATION', 'LATITUDE', 'LONGITUDE'], nrows=1)
    df['STATION'] = filename
    df = df.iloc[0]

    return df


def save_reference(indir, outpath, num_processes, overwrite):
    ''' Function to save reference stations from GHCNd data '''

    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    if os.path.exists(outpath):
        if overwrite:
            print(f'Overwriting {outpath}...')   
        else:
            print(f'{outpath} already exists, skip...')
            ref_df = pd.read_csv(outpath)

            return ref_df
    else:
        print(f'{outpath} does not exist, preprocessing...')

    filename_ls = os.listdir(indir)
    filename_ls.sort()
    with Pool(processes=num_processes) as pool:
        result = pool.starmap(get_reference, [(indir, filename) for filename in filename_ls])

    ref_df = pd.DataFrame(result, columns=['STATION', 'LATITUDE', 'LONGITUDE'])
    ref_df = ref_df.reset_index(drop=True)
    ref_df.to_csv(outpath, index=False)
    print(f'Saving {outpath}')

    return ref_df


def get_min_distance(indir, filename, ref_df):
    ''' Function to get minimum distance for each station from ISD and CMA data, reference to GHCNd data '''

    df = pd.read_csv(os.path.join(indir, filename), usecols=['STATION', 'LATITUDE', 'LONGITUDE'], nrows=1)
    df['STATION'] = filename
    lat = df.iloc[0]['LATITUDE']
    lon = df.iloc[0]['LONGITUDE']

    ref_df['DISTANCE'] = np.sqrt((ref_df['LATITUDE'] - lat)**2 + (ref_df['LONGITUDE'] - lon)**2)

    min_dis = ref_df['DISTANCE'].min()
    ref_idx = ref_df['DISTANCE'].idxmin()
    dis_ls = [min_dis, df.iloc[0]['STATION'], df.iloc[0]['LATITUDE'], df.iloc[0]['LONGITUDE'], 
              ref_df.iloc[ref_idx]['STATION'], ref_df.iloc[ref_idx]['LATITUDE'], ref_df.iloc[ref_idx]['LONGITUDE']]

    return dis_ls


def save_duplicates(dataset_name, st_yr, end_yr, th_yr, ref_df, th_dis, num_processes, outdir_base, overwrite):
    ''' Function to save duplicate stations from other station data, reference to GHCNd data '''

    outdir = os.path.join(outdir_base, f'{st_yr}_{end_yr}_gte{th_yr}')
    os.makedirs(outdir_base, exist_ok=True)
    outname = f'{dataset_name}_duplicate_stations.csv'
    outpath = os.path.join(outdir, outname)
    if os.path.exists(outpath):
        if overwrite:
            print(f'Overwriting {outpath}...')   
        else:
            print(f'{outpath} already exists, skip...')
            dis_df = pd.read_csv(outpath)
            print(f'Duplicate stations in {dataset_name}: {dis_df.shape}')
            print(dis_df.head())
            return
    else:
        print(f'{outpath} does not exist, preprocessing...')

    indir = f'../data/{dataset_name}_daily_prcp/{st_yr}_{end_yr}_gte{th_yr}'
    with Pool(processes=num_processes) as pool:
        result = pool.starmap(get_min_distance, [(indir, filename, ref_df) for filename in os.listdir(indir)])
    
    dis_df = pd.DataFrame(result, columns=['MIN_DISTANCE', 'STATION', 'LATITUDE', 'LONGITUDE', 'REF_STATION', 'REF_LATITUDE', 'REF_LONGITUDE'])
    dis_df = dis_df[dis_df['MIN_DISTANCE'] < th_dis]
    print(f'Duplicate stations in {dataset_name}: {dis_df.shape}')
    print(dis_df.head())
    dis_df.to_csv(outpath, index=False)
    print(f'Saving {outpath}...')

    return
        

def main():

    num_processes = min(100, cpu_count())

    # Load reference data
    indir_ghcnd = f'../data/ghcnd_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'
    outpath_ghcnd = f'../data/station_duplicates/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/ghcnd_reference.csv'
    ref_df = save_reference(indir_ghcnd, outpath_ghcnd, num_processes, OVERWRITE)
    print(ref_df.shape)
    print(ref_df.head())

    # Save duplicates
    outdir_base = f'../data/station_duplicates/'
    data_names = ['cma', 'hpd', 'isd', 'cdc', 'swiss', 'eca', 'saca']
    th_dis = 0.000001 # theshold for Euclidean distance between stations
    for data_name in data_names:
        save_duplicates(data_name, START_YEAR, END_YEAR, TH_YEAR, ref_df, th_dis, num_processes, outdir_base, OVERWRITE)

    return


if __name__ == '__main__':

    main()

