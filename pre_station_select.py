# Code for preprocessing station data
# Including ISD, GHCNd, China Meteorological Adimistration station (CMA), eta


import os
import time
import sys
sys.path.insert(1, './')
from rainfall_ui.preprocess.preprocess_station import (valid_station_isd, concat_station_isd, valid_station_ghcnd_cma_hpd,
                                                       valid_station_cdc, valid_station_swiss, valid_station_eca_saca)
from rainfall_ui.util.config import parse_args


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr

# Define path
INDIR_ISD = r'/data1/zxy/sudden_temp_change/ISD-global-daily/unzip/'
OUTDIR_VALID_STA_ISD = r'../data/isd_valid_stations'
PATH_VALID_STA_ISD = rf'../data/isd_valid_stations/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}.csv'
OUTDIR_CONCAT_STA_ISD = rf'../data/isd_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'

INDIR_GHCND = r'/data4/dataset/atmosphere/stations/CHCN-d/data/noaa_csv_files/'
OUTDIR_GHCND = rf'../data/ghcnd_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'

INDIR_CMA = r'/data4/dataset/atmosphere/stations/prcp_CMA/'
OUTDIR_CMA = rf'../data/cma_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'

INDIR_HPD = r'/data4/dataset/atmosphere/stations/prcp_HPD_v02r02/'
OUTDIR_HPD = rf'../data/hpd_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'

INDIR_CDC_PRCP = r'/data4/dataset/atmosphere/stations/prcp_CDC/prcp_station/'
INDIR_CDC_WEATHER = r'/data4/dataset/atmosphere/stations/prcp_CDC/weather_station/'
OUTDIR_CDC = rf'../data/cdc_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'

STA_PATH_SWISS_APS = r'/data4/dataset/atmosphere/stations/prcp_SWISS/auto_prcp_station/ogd-smn-precip_meta_stations.csv' # auto precipitation station
INDIR_SWISS_APS = os.path.dirname(STA_PATH_SWISS_APS)
STA_PATH_SWISS_AWS = r'/data4/dataset/atmosphere/stations/prcp_SWISS/auto_weather_station/ogd-smn_meta_stations.csv' # auto weather station
INDIR_SWISS_AWS = os.path.dirname(STA_PATH_SWISS_AWS)
STA_PATH_SWISS_MPS = r'/data4/dataset/atmosphere/stations/prcp_SWISS/manual_prcp_station/ogd-nime_meta_stations.csv' # manual precipitation station
INDIR_SWISS_MPS = os.path.dirname(STA_PATH_SWISS_MPS)
OUTDIR_SWISS_APS = rf'../data/swiss_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'

STA_PATH_ECA = r'/data4/dataset/atmosphere/stations/prcp_ECA_nonblend_rr/stations.txt'
INDIR_ECA = os.path.dirname(STA_PATH_ECA)
OUTDIR_ECA = rf'../data/eca_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'

STA_PATH_SACA = r'/data4/dataset/atmosphere/stations/prcp_SACA_nonblend_rr/SACA_blend_station_rr.txt'
INDIR_SACA = os.path.dirname(STA_PATH_SACA)
OUTDIR_SACA = rf'../data/saca_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'


def main():

    t1 = time.time()

    # Preprocess ISD data
    # ==========================================================================================================
    # Find out valid stations across years
    valid_station_isd(START_YEAR, END_YEAR, TH_YEAR, INDIR_ISD, OUTDIR_VALID_STA_ISD, OVERWRITE)
    # Concatenate all valid stations across years
    concat_station_isd(PATH_VALID_STA_ISD, START_YEAR, END_YEAR, INDIR_ISD, OUTDIR_CONCAT_STA_ISD, OVERWRITE)

    # Preprocess GHCNd, CMA, and HPD
    # ==========================================================================================================
    valid_station_ghcnd_cma_hpd(INDIR_GHCND, START_YEAR, END_YEAR, TH_YEAR, OUTDIR_GHCND, 'ghcnd', OVERWRITE)
    valid_station_ghcnd_cma_hpd(INDIR_CMA, START_YEAR, END_YEAR, TH_YEAR, OUTDIR_CMA, 'cma', OVERWRITE)
    valid_station_ghcnd_cma_hpd(INDIR_HPD, START_YEAR, END_YEAR, TH_YEAR, OUTDIR_HPD, 'hpd', OVERWRITE)

    # Preprocess CDC data
    # ==========================================================================================================
    # Weather station
    valid_station_cdc(INDIR_CDC_WEATHER, START_YEAR, END_YEAR, TH_YEAR, OUTDIR_CDC, 'weather', OVERWRITE)
    # Precipitation station
    valid_station_cdc(INDIR_CDC_PRCP, START_YEAR, END_YEAR, TH_YEAR, OUTDIR_CDC, 'prcp', OVERWRITE)

    # Preprocess SWISS data
    # ==========================================================================================================
    # Auto precipitation station
    valid_station_swiss(STA_PATH_SWISS_APS, INDIR_SWISS_APS, START_YEAR, END_YEAR, TH_YEAR, OUTDIR_SWISS_APS, 'aps', OVERWRITE)
    # Auto weather station
    valid_station_swiss(STA_PATH_SWISS_AWS, INDIR_SWISS_AWS, START_YEAR, END_YEAR, TH_YEAR, OUTDIR_SWISS_APS, 'aws', OVERWRITE)
    # Manual precipitation station
    valid_station_swiss(STA_PATH_SWISS_MPS, INDIR_SWISS_MPS, START_YEAR, END_YEAR, TH_YEAR, OUTDIR_SWISS_APS, 'mps', OVERWRITE)

    # Preprocess ECA, and SACA data
    # ==========================================================================================================
    valid_station_eca_saca(STA_PATH_ECA, INDIR_ECA, START_YEAR, END_YEAR, TH_YEAR, OUTDIR_ECA, 'eca', OVERWRITE)
    valid_station_eca_saca(STA_PATH_SACA, INDIR_SACA, START_YEAR, END_YEAR, TH_YEAR, OUTDIR_SACA, 'saca', OVERWRITE)

    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")

    return


if __name__ == "__main__":
    
    main()
    
