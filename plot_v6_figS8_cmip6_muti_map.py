# -*- coding: utf-8 -*-
import os
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.axes_grid1 import ImageGrid
import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes

# === 设置文件夹路径（你的nc文件路径） ===
folder_path = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_s_resample_mean_slope_noarea/"
# folder_path = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_r_resample_mean_slope_noarea/"
file_list = sorted([f for f in os.listdir(folder_path) if f.endswith(".nc")])

# === 准备收集所有变量的值（便于统一色阶） ===
all_values = []
mean_sd_dict = {}  

for file in file_list:
    ds = xr.open_dataset(os.path.join(folder_path, file))
    #da = ds['S_daily_mean'].sel(lat=slice(-60, 60))
    da = ds['S_daily_mean']

    # === 计算每个文件的 mean 和 sd ===
    valid_values = da.values.flatten()
    valid_values = valid_values[~np.isnan(valid_values)]
    if len(valid_values) > 0:
        mean_val = np.mean(valid_values)
        sd_val = np.std(valid_values)
        
        print(f"{file}: mean = {mean_val:.4f}, sd = {sd_val:.4f}")
        mean_sd_dict[file] = (mean_val, sd_val)
    else:
        print(f"{file}: no valid data")
        mean_sd_dict[file] = (np.nan, np.nan)

    # === 收集有效值用于设定色阶 ===
    all_values.append(valid_values)

    ds.close()

# === 整合所有值，设置统一色阶 ===
all_values = np.concatenate(all_values)
all_values = all_values[~np.isnan(all_values)]

vmin = np.percentile(all_values, 15)
vmax = np.percentile(all_values, 90)

mean_clr = [
    "#D6D6D6", "#EDE8E0", "#FFF8E6", "#FAEBD7",
    "#FFE4B5", "#F5D7A1", "#EAB080"
]
cmap = LinearSegmentedColormap.from_list("white_yellow_orange", mean_clr, N=256)

# === 设置子图 ===
ncols = 4
nrows = int(np.ceil(len(file_list) / ncols))
fig = plt.figure(figsize=(4 * ncols, 2.5 * nrows))
axes_class = (GeoAxes, dict(projection=ccrs.PlateCarree()))

grid = ImageGrid(
    fig, 111,
    nrows_ncols=(nrows, ncols),
    axes_pad=(0.05, 0.21),
    cbar_mode='single',
    cbar_location='right',
    cbar_size="1%",
    cbar_pad=0.1,
    share_all=True,
    axes_class=axes_class
)

# === 隐藏多余的子图（避免黑框） ===
for ax in grid[len(file_list):]:
    ax.remove()

# === 遍历每个文件绘图 ===
for idx, (ax, file) in enumerate(zip(grid, file_list)):
    ds = xr.open_dataset(os.path.join(folder_path, file))
    lon = ds['lon']
    lat = ds['lat']

    if lon.max() > 180:
        lon = lon.values
        lon = np.where(lon > 180, lon - 360, lon)
        ds = ds.assign_coords(lon=lon)

    da = ds['S_daily_mean'].sel(lat=slice(-60, 60), lon=slice(-180, 180))
    Lon, Lat = np.meshgrid(da['lon'], da['lat'])
    pcm = ax.pcolormesh(Lon, Lat, da.values, cmap=cmap, vmin=vmin, vmax=vmax, transform=ccrs.PlateCarree())

    mean_val, sd_val = mean_sd_dict[file]

    title = file[:-9] if file.endswith("_day_S.nc") else file[:-5]

    ax.text(
        0.02, 1.02, f'{title}, {mean_val:.2f} \u00B1 {sd_val:.2f}',
        transform=ax.transAxes,
        fontsize=8,
        fontweight='bold',
        va='bottom',
        ha='left'
    )
    ax.coastlines(linewidth=0.4)
    ax.set_xlim([-180, 180])
    ax.set_ylim([-60, 60])
    ax.set_xticks([])
    ax.set_yticks([])

    ds.close()

# === 添加统一 colorbar ===
cbar = grid.cbar_axes[0].colorbar(
    pcm,
    orientation='vertical',
    extend='both',
    extendrect=False,
)

cbar.ax.text(
    3.7,
    0.20,
    '1980-2014 muti-year mean of daily UI',
    transform=cbar.ax.transAxes,
    va='center',
    ha='left',
    fontsize=14,
    fontweight='bold',
    rotation=90,
    rotation_mode='anchor'
)

plt.savefig("/data1/yyzhao/data/1980-2020/finally_result/picture/v6_figS8_muti_map_cmip6_mean.png",
            dpi=300, bbox_inches='tight')
plt.close()
