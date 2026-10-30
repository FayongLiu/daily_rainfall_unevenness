# Code for downloading station data


import os
import pandas as pd


def  get_url_swiss(url_station, url_mode, outdir, overwrite):
    ''' Function to get the URL and outpath of the station data from MeteoSwiss 
    
    :param url_station: URL of the station metadata file
    :param url_mode: mode URL of the station data file
    :param outdir: directory to save the station data file
    :param overwrite: whether to overwrite existing files

    :return: urls, list of URL of the the station data file

    '''

    basename_station = os.path.basename(url_station)
    outpath_station = os.path.join(outdir, basename_station)
    if not os.path.exists(outpath_station) or overwrite:
        print(f'Downloading station file...')
        try:
            df_station = pd.read_csv(url_station, encoding='Windows-1252', delimiter=';')
            df_station.to_csv(outpath_station, index=False)
            print(f'Saving {outpath_station}')
            url_param = url_station.replace('meta_stations.csv', 'meta_parameters.csv')
            outpath_param = os.path.join(outdir, os.path.basename(url_param))
            df_param = pd.read_csv(url_param, encoding='Windows-1252', delimiter=';')
            df_param.to_csv(outpath_param, index=False)
            print(f'Saving {outpath_param}')
            url_datainventory = url_station.replace('meta_stations.csv', 'meta_datainventory.csv')
            outpath_datainventory = os.path.join(outdir, os.path.basename(url_datainventory))
            df_datainventory = pd.read_csv(url_datainventory, encoding='Windows-1252', delimiter=';')
            df_datainventory.to_csv(outpath_datainventory, index=False)
            print(f'Saving {outpath_datainventory}')
        except Exception as e:
            print(f"Error downloading {url_station}: {e}")

    # Get all station names
    df = pd.read_csv(url_station, delimiter=';', encoding='Windows-1252', usecols=['station_abbr'], dtype={'station_abbr': str})
    df['station_abbr'] = df['station_abbr'].str.lower()
    urls = []
    outpaths = []
    for station in df['station_abbr']:
        url = url_mode.replace('STATION', station)
        basename = os.path.basename(url)
        urls.append(url)
        outpaths.append(os.path.join(outdir, basename))
    
    return urls, outpaths

    
def download_swiss(url, outpath, overwrite):
    ''' Function to download the station data from MeteoSwiss
    Refer to https://github.com/MeteoSwiss/opendata/blob/main/notebooks/MonthlyMeanGlobalRadiation_HAI.ipynb

    :param url: URL of the station data file
    :param outpath: path to save the station data file
    :param overwrite: whether to overwrite existing files

    '''

    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    if os.path.exists(outpath):
        if overwrite:
            print(f'Overwriting {outpath}...')
        else:
            print(f'{outpath} already exists, skip...')

            return
    else:
        print(f'{outpath} does not exist, downloading...')

    try:
        df = pd.read_csv(url, delimiter=';')
        df.to_csv(outpath, index=False)
        print(f'Saving {outpath}')

        return

    except Exception as e:
        print(f"Error downloading {url}: {e}")

        return

