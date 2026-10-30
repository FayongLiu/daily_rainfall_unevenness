# Code for preprocessing daily precipitation data


import os
import time
import numpy as np
from multiprocessing import Pool, cpu_count
from rainfall_ui.preprocess.preprocess_grid import (cal_daily_prcp_era5l, cal_daily_prcp_crujra, 
                                                    get_land_mask, cal_daily_prcp_jra3q, cal_daily_prcp_others)
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.datainfo import CMIP6_LS, DATAPATHS


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr


if __name__ == "__main__":
    t1 = time.time()

    year_ls = np.arange(START_YEAR, END_YEAR + 1)
    num_processes = 11

    # Get land mask for cmip6 data
    land_path_ref = r'/data4/dataset/atmosphere/ERA5_land/precipitation/daily/precipitation_daily_2001.nc' # tp
    outdir_mask = r'../data/mask/'
    for data_name in CMIP6_LS:
        indir = DATAPATHS[data_name]
        inpath_ref = os.path.join(indir, os.listdir(indir)[0])
        get_land_mask(inpath_ref, land_path_ref, outdir_mask, data_name, OVERWRITE)

    # ERA5_Land
    input_dir = r'/data_backup/share/ERA5_land/precipitation/hourly/'
    output_dir = r'/data4/dataset/atmosphere/ERA5_land/precipitation/daily/'
    with Pool(processes=num_processes) as pool:
        pool.starmap(cal_daily_prcp_era5l, [(year, input_dir, output_dir, OVERWRITE) for year in year_ls])

    # CRU JRA
    input_dir = r'/data4/share/CRUJRA/v2.2/'
    output_dir = r'/data4/dataset/atmosphere/precipitation/CRU-JRA/pre/'
    with Pool(processes=num_processes) as pool:
        pool.starmap(cal_daily_prcp_crujra, [(year, input_dir, output_dir, OVERWRITE) for year in year_ls])
    
    # # JRA3q
    # ref path for land mask generation
    inpath_jra3q_ref = r'/data4/dataset/atmosphere/jra_3q/precipitation/jra3q.fcst_phy2m.0_1_52.tprate1have-sfc-fc-gauss.2001010100_2001013123.nc'
    input_dir = r'/data4/dataset/atmosphere/jra_3q/precipitation/'
    output_dir = r'/data4/dataset/atmosphere/precipitation/jra3q_daily'
    land_mask = get_land_mask(inpath_jra3q_ref, land_path_ref, outdir_mask, 'jra3q', OVERWRITE)
    with Pool(processes=num_processes) as pool:
        pool.starmap(cal_daily_prcp_jra3q, [(year, input_dir, output_dir, land_mask, OVERWRITE) for year in year_ls])

    # Other grid-based datasets
    data_names = ['imerg', 'gsmap', 'cmorph', 'persiann_cdr', 'persiann', 'mswep']
    # ref path for land mask generation
    inpath_imerg_ref = r'/data4/dataset/atmosphere/precipitation/gpm_3imerghh/2001/3B-HHR.MS.MRG.3IMERG.20011231-S233000-E235959.1410.V07A.HDF5'
    inpath_gsmap_ref = r'/data4/dataset/atmosphere/precipitation/GSMaP_v8/2019/01/gsmap_mvk.20190101.0400.v8.0000.1.dat.gz'
    inpath_morph_ref = r'/data4/dataset/atmosphere/precipitation/cmorph_30min_8km/1998/CMORPH_V1.0_ADJ_8km-30min_1998042505.nc'
    inpath_persiann_cdr_ref = r'/data4/dataset/atmosphere/precipitation/PERSIANN/PCCSCDR/1983/PCCSCDR3h83010100.bin.gz'
    inpath_persiann_ref = r'/data4/dataset/atmosphere/precipitation/PERSIANN/2014/m6s4rr1400423.bin'
    inpath_mswep_ref = r'/data4/dataset/atmosphere/precipitation/MSWEP_V2.8/glo1979/1979001.09.nc'
    inpaths = [inpath_imerg_ref, inpath_gsmap_ref, inpath_morph_ref, 
               inpath_persiann_cdr_ref, inpath_persiann_ref, inpath_mswep_ref]
    input_dir_base_ls = [r'/data4/dataset/atmosphere/precipitation/gpm_3imerghh/',
                         r'/data4/dataset/atmosphere/precipitation/GSMaP_v8/',
                         r'/data4/dataset/atmosphere/precipitation/cmorph_30min_8km/',
                         r'/data4/dataset/atmosphere/precipitation/PERSIANN/PCCSCDR/',
                         r'/data4/dataset/atmosphere/precipitation/PERSIANN/',
                         r'/data4/dataset/atmosphere/precipitation/MSWEP_V2.8/']
    
    for i in range(4, len(data_names)):
        land_mask = get_land_mask(inpaths[i], land_path_ref, outdir_mask, data_names[i], OVERWRITE)
        output_dir = rf'/data4/dataset/atmosphere/precipitation/{data_names[i]}_daily'
        with Pool(processes=num_processes) as pool:
            pool.starmap(cal_daily_prcp_others, [(year, input_dir_base_ls[i], output_dir, data_names[i], land_mask, OVERWRITE) for year in year_ls])

    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")

