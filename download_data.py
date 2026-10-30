# Code for downloading data


import time
from multiprocessing import Pool, cpu_count
import os
import sys
sys.path.insert(1, './')
from rainfall_ui.download.download_station import get_url_swiss, download_swiss


OVERWRITE = False
MIN_PROCESSES = 100

# Define path
# SWISS
OUTDIR_SWISS_AWS = r'/data1/fyliu/prcp_station/SWISS/auto_weather_station'
os.makedirs(OUTDIR_SWISS_AWS, exist_ok=True)
OUTDIR_SWISS_APS = r'/data1/fyliu/prcp_station/SWISS/auto_prcp_station'
os.makedirs(OUTDIR_SWISS_APS, exist_ok=True)
OUTDIR_SWISS_MPS = r'/data1/fyliu/prcp_station/SWISS/manual_prcp_station'
os.makedirs(OUTDIR_SWISS_MPS, exist_ok=True)


def main():

    t1 = time.time()

    num_processes = min(MIN_PROCESSES, cpu_count())

    # Downloading station data
    # SWISS
    # Automatic weather stations
    url_station = r'https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_stations.csv'
    url_mode = r'https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/STATION/ogd-smn_STATION_d_historical.csv'
    urls, outpaths = get_url_swiss(url_station, url_mode, OUTDIR_SWISS_AWS, OVERWRITE)
    with Pool(processes=num_processes) as pool:
        pool.starmap(
            download_swiss,
            [(url, outpath, OVERWRITE) for url, outpath in zip(urls, outpaths)]
        )
    # Automatic precipitation stations
    url_station = r'https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn-precip/ogd-smn-precip_meta_stations.csv'
    url_mode = r'https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn-precip/STATION/ogd-smn-precip_STATION_d_historical.csv'
    urls, outpaths = get_url_swiss(url_station, url_mode, OUTDIR_SWISS_APS, OVERWRITE)
    with Pool(processes=num_processes) as pool:
        pool.starmap(
            download_swiss,
            [(url, outpath, OVERWRITE) for url, outpath in zip(urls, outpaths)]
        )
    # Manual precipitation stations
    url_station = r'https://data.geo.admin.ch/ch.meteoschweiz.ogd-nime/ogd-nime_meta_stations.csv'
    url_mode = r'https://data.geo.admin.ch/ch.meteoschweiz.ogd-nime/STATION/ogd-nime_STATION_d_historical.csv'
    urls, outpaths = get_url_swiss(url_station, url_mode, OUTDIR_SWISS_MPS, OVERWRITE)
    with Pool(processes=num_processes) as pool:
        pool.starmap(
            download_swiss,
            [(url, outpath, OVERWRITE) for url, outpath in zip(urls, outpaths)]
        )
    
    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")
    
    return


if __name__ == "__main__":

    main()

