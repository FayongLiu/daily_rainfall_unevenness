# -*- coding: utf-8 -*-
import os
import pandas as pd
import xarray as xr
import time
from pre_GRID_cal_maximum_annual_prcp import model_ls
from pre_isd_select_valid_station import START_YEAR, END_YEAR, TH_YEAR


def main():
    basedir = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}'
    # calculate averages of all CMIP6 models at global scale
    file_ls = [rf'global_{model}.csv' for model in model_ls]
    csv_ls = []
    for f in file_ls:
        df = pd.read_csv(os.path.join(basedir, f))
        csv_ls.append(df)
    csv_df = pd.concat(csv_ls)
    mean_df = csv_df.groupby('year').mean()
    out_name = r'global_CMIP6_ensembles.csv'
    out_path = os.path.join(basedir, out_name)
    mean_df.to_csv(os.path.join(out_path))
    print(f'Saving {out_path}')

    # calculate averages of all CMIP6 models at each grid scale
    file_ls = [rf'grid_{model}.nc' for model in model_ls]
    nc_ls = []
    for f in file_ls:
        ds = xr.open_dataset(os.path.join(basedir, f))
        nc_ls.append(ds)
    nc_ds = xr.concat(nc_ls, dim='model')
    mean_ds = nc_ds.mean(dim='model', skipna=True)
    out_name = r'grid_CMIP6_ensembles.nc'
    out_path = os.path.join(basedir, out_name)
    mean_ds.to_netcdf(os.path.join(out_path))
    print(f'Saving {out_path}')

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