# Code for checking the results of daily precipitation from different datasets
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import os


def main():

    data_names = ['jra3q', 'imerg', 'gsmap', 'cmorph', 'mswep', 'persiann']
    indir2_ls = [r'/data1/jzzhou/precipitation/data_daynight_preci/jra_3q/2001_light_dark_index/',
                 r'/data1/jzhang/datasets/gpm_3imerghh/0.5hour_direct/2001_0.1deg_output/',
                 r'/data1/jzzhou/precipitation/output/V8/process/2001_output/',
                 r'/data1/jzhang/datasets/cmorph_30min_8km/2001_8km_output/',
                 r'/data1/jzzhou/precipitation/output/gloh2o/2001_output/']
    outdir = r'../fig/daily_prcp/'
    os.makedirs(outdir, exist_ok=True)
    for i, data_name in enumerate(data_names):
        print(f'Processing {data_name}...')
        inpath1 = f'/data1/fyliu/prcp/{data_name}_daily/daily_precipitation_2001.nc'
        ds1 = xr.open_dataset(inpath1)
        ds1 = ds1['prcp'].isel(time=0)
        plt.figure(figsize=(8, 4))
        ds1.plot()
        outname1 = f'daily_precipitation_20010101_{data_name}_fyliu.png'
        outpath1 = os.path.join(outdir, outname1)
        plt.savefig(outpath1)
        plt.close()
        print(f'Saving {outpath1}')

        if data_name != 'persiann':
            indir2 = indir2_ls[i]
            inname2 = '2001-01-01.nc' if data_name == 'jra3q' else '2001-01-01_light_dark.nc'
            inpath2 = os.path.join(indir2, inname2)
            ds2 = xr.open_dataset(inpath2)
            if data_name == 'jra3q':
                ds1 = ds1.drop_vars('time')
                ds2 = ds2['daytime_sum'] + ds2['nighttime_sum']
            else:
                ds2 = ds2['lightHourlyPrecipRate'] + ds2['darkHourlyPrecipRate']
            if 'latitude' in ds2.dims:
                ds2 = ds2.rename({'latitude': 'lat', 'longitude': 'lon'})
            ds2['lon'] = xr.where(ds2['lon'] > 180, ds2['lon'] - 360, ds2['lon'])
            ds2 = ds2.sortby('lat').sortby('lon')
            ds2['lon'] = ds2['lon'].astype('float32')
            ds2['lat'] = ds2['lat'].astype('float32')
            ds2 = ds2.reindex(lat=ds1.lat, lon=ds1.lon, method='nearest')
            ds2 = ds2.where(ds1 >= 0, np.nan)
            plt.figure(figsize=(8, 4))
            ds2.plot()
            outname2 = f'daily_precipitation_20010101_{data_name}_jjzhou_jzhang.png'
            outpath2 = os.path.join(outdir, outname2)
            plt.savefig(outpath2)
            plt.close()
            print(f'Saving {outpath2}')

            print(ds1)
            print(ds2)
            differ = ds1 - ds2
            print(f'Difference of {data_name}, mean={differ.mean().values:.6f}, max={differ.max().values:.6f}, min={differ.min().values:.6f}') 
            plt.figure(figsize=(8, 4))
            differ.plot()
            outname3 = f'daily_precipitation_20010101_{data_name}_difference.png'
            outpath3 = os.path.join(outdir, outname3)
            plt.savefig(outpath3)
            plt.close()
            print(f'Saving {outpath3}')

    return


if __name__ == '__main__':

    main()

