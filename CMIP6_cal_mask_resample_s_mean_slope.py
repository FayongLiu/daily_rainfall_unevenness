# -*- coding: utf-8 -*-
import os
import numpy as np
import xarray as xr
from scipy.stats import linregress
import logging
from tqdm import tqdm

    
def calc_trend(y, time_index):
    mask = ~np.isnan(y) & ~np.isnan(time_index)

    if np.sum(mask) < 2:
        return np.nan, np.nan
    try:
        slope, _, _, p_value, _ = linregress(time_index[mask], y[mask])
        return slope, p_value
    except Exception:
        return np.nan, np.nan    


def process_nc_files(input_folder, target_nc_file, mask_file, output_folder, log_folder):
    """
    Process NC files: resample to target grid, apply mask and calculate statistics
    
    Parameters:
    input_folder: Input folder path containing NC files
    target_nc_file: Target NC file path for grid reference
    mask_file: Mask file path for data masking
    output_folder: Output folder path for results
    log_folder: Log folder path
    """
    # Create necessary directories
    os.makedirs(log_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    # Setup logging
    log_file = os.path.join(log_folder, 'cmip6_s_weighted_mask_nc.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Read mask file
    logging.info(f"Reading mask file: {mask_file}")
    try:
        mask_ds = xr.open_dataset(mask_file)
        
        # Use S_daily_mean as mask variable
        mask_var_name = 'S_daily_mean'
        if mask_var_name not in mask_ds:
            logging.error(f"Mask variable '{mask_var_name}' not found in mask file")
            return
            
        mask_data = mask_ds[mask_var_name]
        logging.info(f"Using mask variable: {mask_var_name}")
        
        # Identify mask coordinate names
        mask_lat_name = None
        mask_lon_name = None
        for var in mask_ds.coords:
            if var.lower() in ['lat', 'latitude']:
                mask_lat_name = var
            elif var.lower() in ['lon', 'longitude']:
                mask_lon_name = var
                
        if not all([mask_lat_name, mask_lon_name]):
            logging.error("Could not identify lat-lon coordinates in mask file")
            return
            
    except Exception as e:
        logging.error(f"Error reading mask file: {str(e)}")
        return
    
    # Read target grid
    logging.info(f"Reading target grid file: {target_nc_file}")
    try:
        target_ds = xr.open_dataset(target_nc_file)
        area = target_ds['area']
        # Identify target coordinate names
        target_lat_name = None
        target_lon_name = None
        for var in target_ds.coords:
            if var.lower() in ['lat', 'latitude']:
                target_lat_name = var
            elif var.lower() in ['lon', 'longitude']:
                target_lon_name = var
        
        if not all([target_lat_name, target_lon_name]):
            logging.error("Could not identify lat-lon coordinates in target file")
            return
            
        target_lat = target_ds[target_lat_name]
        target_lon = target_ds[target_lon_name]

            
    except Exception as e:
        logging.error(f"Error reading target file: {str(e)}")
        return
    #step 1:Resampling the Mask File: The mask file was first resampled to match the target spatial resolution.
    # Resample mask to target grid
    resampled_mask = mask_data.interp(
        {mask_lat_name: target_lat, mask_lon_name: target_lon},
        method='nearest'
    )
    
    # Process input files
    nc_files = [f for f in os.listdir(input_folder) if f.endswith('.nc')]
    logging.info(f"Found {len(nc_files)} NC files to process")
    
    for filename in tqdm(nc_files, desc="Processing NC files"):
        input_path = os.path.join(input_folder, filename)
        logging.info(f"Processing file: {filename}")        
        try:        
            # Read input file
            ds = xr.open_dataset(input_path)
            
            # Identify coordinate names
            lat_name = None
            lon_name = None
            for var in ds.coords:
                if var.lower() in ['lat', 'latitude']:
                    lat_name = var
                elif var.lower() in ['lon', 'longitude']:
                    lon_name = var           
            if not all([lat_name, lon_name]):
                logging.warning(f"Skipping {filename}: Missing lat-lon coordinates")
                continue                
                
            #step 2:Resampling All NetCDF Files: All input NetCDF (*.nc) files were then resampled to the same target resolution.
            # Resample to target grid
            resampled_ds = ds.interp(
                {lat_name: target_lat, lon_name: target_lon},
                method='linear'
            )
            
            # Initialize results dataset
            result_ds = xr.Dataset()
            time_idx = np.arange(len(resampled_ds.time))
                # Process variables
            for var_name in ['S_daily', 'S_monthly']:
                if var_name in resampled_ds:
                    data = resampled_ds[var_name]
                    #step 3:Applying the Land Mask
                    masked_data = data.where(~np.isnan(resampled_mask))
                    
                     #new step4:weight of area                   
                    #weighted_area = area.broadcast_like(masked_data)
                    #total_area = area.where(~np.isnan(masked_data.isel(time=0))).sum()
                    #weighted_data = masked_data * area / total_area
                    
                    #weighted_data = masked_data.weighted(area).mean(dim=[target_lat_name, target_lon_name], skipna=True)
                    # 计算均值
                    #result_ds[f'{var_name}_mean'] = weighted_data.mean(dim='time', skipna=True)
                    result_ds[f'{var_name}_mean'] = masked_data.mean(dim='time', skipna=True)
                    # 计算趋势和p值
                    trends = xr.apply_ufunc(
                        calc_trend,
                        masked_data,
                        input_core_dims=[['time']],
                        output_core_dims=[(), ()],
                        vectorize=True,
                        dask='parallelized',
                        output_dtypes=[float, float],
                        kwargs={'time_index': time_idx}
                    )
                    result_ds[f'{var_name}_trend'] = trends[0]
                    result_ds[f'{var_name}_p_value'] = trends[1]
            # Save results
            output_path = os.path.join(output_folder, f"{filename}")
            result_ds.to_netcdf(output_path)
            logging.info(f"Successfully saved results: {output_path}")
            
        except Exception as e:
            logging.error(f"Error processing file {filename}: {str(e)}")
            continue


def main():

    input_folder = "/data1/yyzhao/data/1980-2020/CMIP6/s/concat_s"
    #target_nc_file = "/data1/yyzhao/data/1980-2020/CMIP6/s/concat_s/MPI-ESM1-2-HR_day_S.nc"
    target_nc_file ='/data1/fyliu/c_temperature_variability/data/area_bio_cli_mask/area_mask/area_0.1deg.nc'
    mask_file = "/data1/yyzhao/data/1980-2020/CRU-JRA/1980-2020_CRU_S_avg_slope.nc"
    #output_folder = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_s_resample_mean_slope/"
    output_folder = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_s_resample_mean_slope_noarea/"
    log_folder = "/data1/yyzhao/data/1980-2020/finally_result/log/"
    
    # Process files
    process_nc_files(input_folder, target_nc_file, mask_file, output_folder, log_folder)

if __name__ == "__main__":
    main()

