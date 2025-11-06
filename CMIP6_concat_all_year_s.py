# -*- coding: utf-8 -*-
import xarray as xr
import os
import logging
from datetime import datetime
import re

# 设定日志输出路径
log_folder = "/data1/yyzhao/data/CMIP6/1980_2020/"  # 日志文件夹路径
os.makedirs(log_folder, exist_ok=True)  # 创建日志目录（若不存在）

# 配置日志
log_filename = os.path.join(log_folder, f"concat_s_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 设定大文件夹路径（包含多个子文件夹）
base_folder =  "/data1/ZhouJZ/precipitation/season/cmip6/s/"  # 替换为你的大文件夹路径

# 设定输出文件夹
output_folder = "/data1/yyzhao/data/CMIP6/1980_2020/s/concat_s/"
os.makedirs(output_folder, exist_ok=True)  # 创建输出目录（若不存在）

# 记录程序开始时间
start_time = datetime.now()
logging.info(f"Program started at {start_time}")

def get_coords(ds):
    lon_var = 'longitude' if 'longitude' in ds else 'lon'
    lat_var = 'latitude' if 'latitude' in ds else 'lat'
    return ds[lon_var], ds[lat_var]

def extract_year_from_filename(filename):
    # 从文件名中提取年份（格式为 yyyy）
    match = re.search(r'\d{4}', filename)
    if match:
        return int(match.group(0))
    return None

# 遍历大文件夹中的所有子文件夹
for folder_name in sorted(os.listdir(base_folder)):
    folder_path = os.path.join(base_folder, folder_name)

    # 仅处理文件夹，跳过非目录文件
    if not os.path.isdir(folder_path):
        logging.warning(f"Skipping non-directory: {folder_path}")
        continue

    logging.info(f"Processing folder: {folder_name}")

    # 检查文件夹中的 .nc 文件数量
    file_list = [f for f in os.listdir(folder_path) if f.endswith(".nc")]
    logging.info(f"Found {len(file_list)} .nc files in folder: {folder_name}")

    all_S_daily = []    # 存储符合条件的 d_daily 数据
    all_S_monthly = []  # 存储符合条件的 d_monthly 数据
    first_coords = None  # 用于保存第一个有效文件的经纬度信息
    valid_files = []     # 记录符合条件的文件
    skipped_files = []   # 记录被跳过的文件

    # 遍历子文件夹内的所有 .nc 文件
    for file_name in sorted(file_list):
        file_path = os.path.join(folder_path, file_name)
        year = extract_year_from_filename(file_name)

        if year is None:
            logging.warning(f"Cannot extract year from filename: {file_name}. Skipping.")
            skipped_files.append(file_name)
            continue

        # 检查年份是否在1980-2014范围内
        if 1980 <= year <= 2014:
            logging.info(f"Processing file: {file_path} (Year: {year})")
            try:
                with xr.open_dataset(file_path) as ds:
                    # 记录第一个有效文件的经纬度信息（同一子文件夹内的所有文件经纬度应一致）
                    if first_coords is None:
                        lon, lat = get_coords(ds)
                        first_coords = {
                            'lon': lon.copy(),
                            'lat': lat.copy()
                        }
                    # 提取 d_daily 和 d_monthly
                    if 'S_daily' in ds and 'S_monthly' in ds:
                        all_S_daily.append(ds['S_daily'])
                        all_S_monthly.append(ds['S_monthly'])
                        valid_files.append(file_name)
                    else:
                        logging.warning(f"S_daily or S_monthly not found in file: {file_path}")
                        skipped_files.append(file_name)
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}")
                skipped_files.append(file_name)
        else:
            logging.info(f"Skipping file: {file_path} (Year: {year} is out of range 1980-2014)")
            skipped_files.append(file_name)

    # 记录文件夹的处理情况
    if valid_files:
        logging.info(f"Folder {folder_name} has {len(valid_files)} valid files (1980-2014): {valid_files}")
    if skipped_files:
        logging.info(f"Folder {folder_name} skipped {len(skipped_files)} files: {skipped_files}")

    # 若收集到数据，则进行时间维度拼接
    if all_S_daily and all_S_monthly:
        try:
            # 按时间拼接 d_daily 和 d_monthly
            S_daily_combined = xr.concat(all_S_daily, dim='time')
            S_monthly_combined = xr.concat(all_S_monthly, dim='time')

            # 创建新的 Dataset，使用第一个有效文件的经纬度信息
            merged_ds = xr.Dataset({
                'S_daily': S_daily_combined,
                'S_monthly': S_monthly_combined
            }, coords={
                'time': S_daily_combined['time'],  # 使用拼接后的时间坐标
                'lon': first_coords['lon'],
                'lat': first_coords['lat']
            })

            # 输出文件路径（以子文件夹名称命名）
            output_file = os.path.join(output_folder, f"{folder_name}_S.nc")
            merged_ds.to_netcdf(output_file)
            logging.info(f"Saved merged dataset to: {output_file}")
        except Exception as e:
            logging.error(f"Error merging and saving dataset for folder {folder_name}: {e}")
    else:
        logging.warning(f"No valid data found for folder: {folder_name}")

# 记录程序结束时间
end_time = datetime.now()
logging.info(f"Program ended at {end_time}")
logging.info(f"Total execution time: {end_time - start_time}")