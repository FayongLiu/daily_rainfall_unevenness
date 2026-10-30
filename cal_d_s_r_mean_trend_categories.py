# Code for caclulating mean and trend for different categories
import os
import pandas as pd
import numpy as np
import xarray as xr
import time
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.datainfo import CATEGORY_NAMES, CATEGORY_LS_80, CATEGORY_LS_50, REGIONS

args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr
CATEGORY_LS = CATEGORY_LS_80 if START_YEAR >= 1980 else CATEGORY_LS_50


def main():
    basedir = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'
    ref_path = os.path.join(basedir, 'station.nc')
    ref_ds = xr.open_dataset(ref_path)
    for i in range(len(CATEGORY_NAMES)):
        categories = CATEGORY_LS[i]
        name = CATEGORY_NAMES[i]
        print(f'Processing {name}...')
        # calculate averages at global and regional scale
        for region in ['global'] + list(REGIONS.keys()):
            if region == 'global':
                out_name = rf'global_{name}_ensembles.csv'
                file_ls = [rf'global_{model}.csv' for model in categories]
            else:
                out_name = rf"region_{region.replace(' ', '_')}_{name}_ensembles.csv"
                file_ls = [rf"region_{region.replace(' ', '_')}_{model}.csv" for model in categories]
            out_path = os.path.join(basedir, out_name)
            if not os.path.exists(out_path) or OVERWRITE:
                if not os.path.exists(out_path):
                    print(f'{out_path} does not exist, calculating...')
                else:
                    print(f'{out_path} exists, overwriting...')
                csv_ls = []
                for f in file_ls:
                    df = pd.read_csv(os.path.join(basedir, f))
                    csv_ls.append(df)
                csv_df = pd.concat(csv_ls)
                mean_df = csv_df.groupby('year').mean()
                mean_df.to_csv(os.path.join(out_path))
                print(f'Saving {out_path}')
            else:
                print(f'{out_path} exists, skip...')

        # calculate averages of at each grid scale
        out_name = rf'grid_{name}_ensembles.nc'
        out_path = os.path.join(basedir, out_name)
        if not os.path.exists(out_path) or OVERWRITE:
            if not os.path.exists(out_path):
                print(f'{out_path} does not exist, calculating...')
            else:
                print(f'{out_path} exists, overwriting...')
            file_ls = [rf'grid_{model}.nc' for model in categories]
            nc_ls = []
            for j, f in enumerate(file_ls):
                print(f'Loading {j+1}/{len(file_ls)}: {f}...')
                ds = xr.open_dataset(os.path.join(basedir, f))
                model_name = f.split('.')[0].replace('grid_', '')
                ds = ds.expand_dims(model=[model_name])
                # resample
                ds = ds.reindex(lat=ref_ds.lat, lon=ref_ds.lon, method='nearest')
                # if model_name in SATELLITE_LS:
                #     ds = xr.where(ds.lat > 60, np.nan, ds)
                nc_ls.append(ds)
                print(f'Finish loading {f}')
            mean_ds = xr.concat(nc_ls, dim='model').mean(dim='model', skipna=True)
            mean_ds.to_netcdf(os.path.join(out_path))
            print(f'Saving {out_path}')
        else:
            print(f'{out_path} exists, skip...')

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

    