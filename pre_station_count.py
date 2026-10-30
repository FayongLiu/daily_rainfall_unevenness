# Code for counting valid stations


import os
from rainfall_ui.util.config import parse_args


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr


def count_valid_stations(dataset_name, start_yr, end_yr, th_year):
    ''' Function to count stations in each dataset '''

    indir = f'../data/{dataset_name}_daily_prcp/{start_yr}_{end_yr}_gte{th_year}'

    num_station = len(os.listdir(indir))
    print(f'{dataset_name.upper()}: {num_station}')
        
    return num_station


def main():
    
    data_names = ['ghcnd', 'cma', 'hpd', 'isd', 'cdc', 'swiss', 'eca', 'saca']
    start_yr, end_yr, th_year = START_YEAR, END_YEAR, TH_YEAR
    print(f'Counting valid stations during {start_yr}-{end_yr}, greater than or equal to {th_year} years ...')
    num_station_ls = []
    for var in data_names:
        num_station_ls.append(count_valid_stations(var, start_yr, end_yr, th_year))
    
    print(f'\nTotal number of valid stations: {sum(num_station_ls)}\n')
    

    return


if __name__ == '__main__':

    main()

