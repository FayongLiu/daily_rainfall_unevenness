# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.stats import gaussian_kde
import os
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.lines as mlines
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from mpl_toolkits.axes_grid1 import ImageGrid
from cartopy.mpl.geoaxes import GeoAxes

# === 设置文件夹路径（你的nc文件路径） ===
folder_path = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_s_resample_mean_slope_noarea/"
file_list = sorted([f for f in os.listdir(folder_path) if f.endswith(".nc")])

# === 准备收集所有变量的值（便于统一色阶） ===
all_values = []
for file in file_list:
    ds = xr.open_dataset(os.path.join(folder_path, file))
    da = ds['S_daily_trend']
    da = ds['S_daily_trend'].sel(lat=slice(-60, 60))* 1000
    all_values.append(da.values.flatten())
    ds.close()
all_values = np.concatenate(all_values)
all_values = all_values[~np.isnan(all_values)]  # 去除 NaN

# === 设置统一色阶 ===
vmin = np.percentile(all_values, 15)
vmax = np.percentile(all_values, 90)

trend_clr = ["#9CB0C3", "#FFFFFF", "#EAB080"]
cmap = LinearSegmentedColormap.from_list("blue2orange", trend_clr,N=256)
norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
# === 设置子图 ===
ncols = 4
nrows = int(np.ceil(len(file_list) / ncols))
fig = plt.figure(figsize=(4*ncols, 2.5*nrows))
axes_class = (GeoAxes, dict(projection=ccrs.PlateCarree()))
# 调整 ImageGrid 参数
grid = ImageGrid(
    fig, 111,
    nrows_ncols=(nrows, ncols),
    axes_pad=(0.05, 0.21),      # (行间距, 列间距)，默认0.02
    cbar_mode='single',
    cbar_location='right',
    cbar_size="1%",              # 这才是控制颜色条宽度的关键参数
    cbar_pad=0.1,               # 控制颜色条与子图的间距
    share_all=True,# 共享坐标轴
    axes_class=axes_class            
)
# === 隐藏多余的子图（避免黑框） ===
for ax in grid[len(file_list):]:
    ax.remove()  # 直接移除空白子图
# === 遍历每个文件绘图 ===
for idx, (ax, file) in enumerate(zip(grid, file_list)): 
    ds = xr.open_dataset(os.path.join(folder_path, file))
    lon = ds['lon']
    lat = ds['lat']     
    # 如果经度是0-360，转换为-180到180
    if lon.max() > 180:
        lon = ds['lon'].values  # 先获取numpy数组
        lon = np.where(lon > 180, lon - 360, lon)  # 使用numpy.where处理
        ds = ds.assign_coords(lon=lon)  # 重新分配坐标
        # 确保数据在正确的范围内

    da = ds['S_daily_trend'].sel(lat=slice(-60, 60),lon=slice(-180, 180))* 1000

    #显著性掩膜
    S_daily_p = ds['S_daily_p_value'].sel(lat=slice(-60, 60),lon=slice(-180, 180))
    significance_mask = (S_daily_p > 0.05) | np.isnan(S_daily_p)
    Lon, Lat = np.meshgrid(da['lon'], da['lat'])
    pcm = ax.pcolormesh(Lon, Lat, da,cmap=cmap,norm=norm,transform=ccrs.PlateCarree())
    contourf_plot = ax.contourf(Lon, Lat,significance_mask,hatches=[4*'.', ''],colors='none',transform=ccrs.PlateCarree())
    # 设置标题
    title = file[:-9] if file.endswith("_day_S.nc") else file[:-5]
    ax.text(
        0.02, 1.02,                    # 坐标稍微偏上左，单位是  子图坐标系
        title,                         # 子图标题
        transform=ax.transAxes,        # 使用子图坐标系
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
cbar =grid.cbar_axes[0].colorbar(
    pcm,
    orientation='vertical',
    extend='both',      
    extendrect=False,
)

cbar.ax.text( 
    3.7,              # 向右移动距离
    0.20,              # 垂直位置（0.5表示中间）
    r'1980-2014 Trend of daily UI (kyr$^{-1}$)',     # 标签文本
    transform=cbar.ax.transAxes,  # 使用颜色条的坐标系
    va='center',      # 垂直对齐方式
    ha='left',        # 水平对齐方式
    fontsize=14,       # 字体大小
    fontweight='bold', # 字体粗细
    rotation=90,      # 旋转90度使文字垂直
    rotation_mode='anchor'  # 确保旋转时文字位置gu ding
) 
plt.savefig("/data1/yyzhao/data/1980-2020/finally_result/picture/v6_figS9_muti_map_cmip6_slope.png",
            dpi=300, bbox_inches='tight')
plt.close()

