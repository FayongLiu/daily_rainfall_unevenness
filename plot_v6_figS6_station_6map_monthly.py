# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import gaussian_kde
import os
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import TwoSlopeNorm
import matplotlib.ticker as ticker
import matplotlib.lines as mlines

csv_file = "/data1/yyzhao/data/1980-2020/finally_result/data/v3_station_d_s/mean_trend/d_s_r_mean_trend.csv"


# ========== 读取 ==========
df = pd.read_csv(csv_file)

lon = df['lon']
lat = df['lat']

#S=ui;D=re;R = R/Rmax input
S_daily_mean = df['S_monthly_mean']
S_daily_trend = df['S_monthly_trend']* 1000
S_daily_p = df['S_monthly_p_value']

D_daily_mean = df['D_monthly_mean']
D_daily_trend = df['D_monthly_trend']* 1000
D_daily_p = df['D_monthly_p_value']

R_daily_mean = df['PRCP_ratio_mean']
R_daily_trend = df['PRCP_ratio_trend']* 1000
R_daily_p = df['PRCP_ratio_p_value']

# === S mean / trend : 1D array (去NaN) === 
S_daily_mean_1d = S_daily_mean.values.flatten() 
S_daily_mean_1d = S_daily_mean_1d[~np.isnan(S_daily_mean_1d)]  # 移除NaN 
S_daily_mean_vmin = np.percentile(S_daily_mean_1d, 12) 
S_daily_mean_vmax = np.percentile(S_daily_mean_1d, 88) 

S_daily_trend_1d = S_daily_trend.values.flatten() 
S_daily_trend_1d = S_daily_trend_1d[~np.isnan(S_daily_trend_1d)]  # 移除NaN 
S_daily_trend_vmin = np.percentile(S_daily_trend_1d, 10) 
S_daily_trend_vmax = -S_daily_trend_vmin  # 对称设置最大值

# === D mean / trend : 1D array (去NaN) === 
D_daily_mean_1d = D_daily_mean.values.flatten() 
D_daily_mean_1d = D_daily_mean_1d[~np.isnan(D_daily_mean_1d)]  # 移除NaN 
D_daily_mean_vmin = np.percentile(D_daily_mean_1d, 12) 
D_daily_mean_vmax = np.percentile(D_daily_mean_1d, 88) 

D_daily_trend_1d = D_daily_trend.values.flatten() 
D_daily_trend_1d = D_daily_trend_1d[~np.isnan(D_daily_trend_1d)]  # 移除NaN 
D_daily_trend_vmin = np.percentile(D_daily_trend_1d, 10) 
D_daily_trend_vmax = -D_daily_trend_vmin  # 对称设置最大值

# === R mean / trend : 1D array (去NaN) === 
R_daily_mean_1d = R_daily_mean.values.flatten() 
R_daily_mean_1d = R_daily_mean_1d[~np.isnan(R_daily_mean_1d)]  # 移除NaN 
R_daily_mean_vmin = np.percentile(R_daily_mean_1d, 12) 
R_daily_mean_vmax = np.percentile(R_daily_mean_1d, 88) 

R_daily_trend_1d = R_daily_trend.values.flatten() 
R_daily_trend_1d = R_daily_trend_1d[~np.isnan(R_daily_trend_1d)]  # 移除NaN 
R_daily_trend_vmin = np.percentile(R_daily_trend_1d, 10) 
R_daily_trend_vmax = -R_daily_trend_vmin  # 对称设置最大值

# 打印范围（确保无NaN）
print(f"every var min and max:")
print(f"S Mean range: {S_daily_mean_1d.min():.5f} ~ {S_daily_mean_1d.max():.5f}")
print(f"D Mean range: {D_daily_mean_1d.min():.5f} ~ {D_daily_mean_1d.max():.5f}")
print(f"R Mean range: {R_daily_mean_1d.min():.5f} ~ {R_daily_mean_1d.max():.5f}")
print(f"S Trend range: {S_daily_trend_1d.min():.5f} ~ {S_daily_trend_1d.max():.5f}")
print(f"D Trend range: {D_daily_trend_1d.min():.5f} ~ {D_daily_trend_1d.max():.5f}")
print(f"R Trend range: {R_daily_trend_1d.min():.5f} ~ {R_daily_trend_1d.max():.5f}")

print(f"every var mean and std:")
print(f"S Mean range: {S_daily_mean_1d.mean():.5f} and {S_daily_mean_1d.std():.5f}")
print(f"D Mean range: {D_daily_mean_1d.mean():.5f} and {D_daily_mean_1d.std():.5f}")
print(f"R Mean range: {R_daily_mean_1d.mean():.5f} and {R_daily_mean_1d.std():.5f}")
print(f"S Trend range: {S_daily_trend_1d.mean():.5f} and {S_daily_trend_1d.std():.5f}")
print(f"D Trend range: {D_daily_trend_1d.mean():.5f} and {D_daily_trend_1d.std():.5f}")
print(f"R Trend range: {R_daily_trend_1d.mean():.5f} and {R_daily_trend_1d.std():.5f}")

norm_s_trend = TwoSlopeNorm(vmin=S_daily_trend_vmin, vcenter=0, vmax=S_daily_trend_vmax)
norm_d_trend = TwoSlopeNorm(vmin=D_daily_trend_vmin, vcenter=0, vmax=D_daily_trend_vmax)
norm_r_trend = TwoSlopeNorm(vmin=R_daily_trend_vmin, vcenter=0, vmax=R_daily_trend_vmax)

# ========== 作图 ==========
#proj = ccrs.Robinson()  # 椭圆形
proj = ccrs.PlateCarree()  # 改为长方形投

fig, axes = plt.subplots(
    3, 2,
    figsize=(12, 10),
    subplot_kw={'projection': proj}
)
plt.subplots_adjust(wspace=0.04, hspace=0.006)
ax1, ax2, ax3, ax4, ax5, ax6 = axes.flat

lat_mask = (lat >= -60) & (lat <= 80)
lat_ticks = [-60, -30, 0, 30, 60]
# 对每个子图设置纬度标签
for i, ax in enumerate(axes.flat):
    # 设置纬度刻度
    ax.set_yticks(lat_ticks, crs=ccrs.PlateCarree())
    
    # 设置标签格式
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%d\u00B0'))
    
    # 根据子图位置决定标签位置（奇数列在左，偶数列在右）
    if i % 2 == 0:  # 左侧子图（0,2,4）
        ax.yaxis.set_label_position('left')
        ax.yaxis.tick_left()
    else:  # 右侧子图（1,3,5）
        ax.yaxis.set_label_position('right')
        ax.yaxis.tick_right()
    
    # 移除经度刻度
    ax.set_xticks([])
    
    
mean_clr = [
    "#D6D6D6",  # 原浅灰色（左端保持）
    "#EDE8E0",  # 新增：灰米白（平滑过渡）
    "#FFF8E6",  # 极浅米白
    "#FAEBD7",  # 新增：古典米白（柔和过渡）
    "#FFE4B5",  # 低饱和浅黄
    "#F5D7A1",  # 新增：柔沙黄（减少跳跃感）
    "#EAB080"   # 低饱和黄橙（右端保持）
]
cmap_mean = LinearSegmentedColormap.from_list("white_yellow_orange", mean_clr,N=256)

trend_clr = ["#9CB0C3", "#FFFFFF", "#EAB080"]
cmap_trend = LinearSegmentedColormap.from_list("blue2orange", trend_clr,N=256)

# ===== 子图 1: S mean =====    
p1 = ax1.scatter(
    lon[lat_mask], lat[lat_mask],
    c=S_daily_mean[lat_mask],
    cmap=cmap_mean,
    vmax=S_daily_mean_vmax,
    vmin=S_daily_mean_vmin,
    s=4,
    alpha=0.7,
    transform=ccrs.PlateCarree(),
    edgecolors='none'
)
ax1.coastlines(linewidths=0.5)
ax1.text(
    0.06, 1.05,          # 相对坐标 (x, y)，以子图左下角为 (0,0)，右上角为 (1,1)
    '(a) Multi-year mean of UI (ISD)',
    transform=ax1.transAxes,
    fontsize=10,
    fontweight='bold'
)
# colorbar for s mean
cb1 = fig.colorbar(
    p1,
    ax=ax1,
    orientation='horizontal',
    fraction=0.07,
    pad=0.03,                        # 增大间距（默认0.1）
    shrink=0.9,
    extend='both',      
    extendrect=False  
)

cb1.ax.text(
    #1.05, 0.5, r'($\times 10^{-3}$)', 
    1.05, 0.5, '',
    transform=cb1.ax.transAxes,
    va='center', ha='left',
    fontsize=7,
    fontweight='bold'
)

ax1.set_extent([-180, 180, -60, 80], crs=ccrs.PlateCarree())
# ===== 子图 2: S trend =====
p2 = ax2.scatter(
    lon[lat_mask], lat[lat_mask],
    c=S_daily_trend[lat_mask],
    cmap=cmap_trend,
    norm=norm_s_trend,
    alpha=0.7,
    s=4,
    transform=ccrs.PlateCarree()
)

# 显著性用星形边框
s_sig_mask = S_daily_p <= 0.05
# 组合两个掩码
s_combined_mask = s_sig_mask & lat_mask
ax2.scatter(
    lon[s_combined_mask], lat[s_combined_mask],
    c=S_daily_trend[s_combined_mask],  # 数据值映射颜色
    cmap=cmap_trend,
    norm=norm_s_trend,
    alpha=0.7,
    edgecolors='black',
    linewidths=0.3,    #默认1
    s=4,
    transform=ccrs.PlateCarree()
)

ax2.coastlines(linewidths=0.5)
ax2.text(
    0.06, 1.05,
    '(d) Trend of UI (ISD)',
    transform=ax2.transAxes,
    fontsize=10,
    fontweight='bold'
)
# colorbar for s Trend
cb2 = fig.colorbar(
    p2,
    ax=ax2,
    orientation='horizontal',
    fraction=0.07,
    pad=0.03,                        # 增大间距（默认0.1）
    shrink=0.9,
    extend='both',      
    extendrect=False  
)
#图例显著性点设置
sig_legend = mlines.Line2D(
    [], [],                         # 没有实际数据点
    color='black',                  # 边框颜色
    marker='o',                     # 圆形标记
    markersize=5,                   # 和 scatter 大小一致
    linewidth=0,                    # 不连线
    markerfacecolor='none',         # 填充透明
    label=r'$p \leq 0.05$'                  # 图例文本
)

# 把图例放在 ax2 左下角
ax2.legend(
    handles=[sig_legend],
    loc='center',                     # 基准位置为中心
    bbox_to_anchor=(0.16, 0.10),       # 相对子图的坐标 (x, y)
    fontsize=9,
    framealpha=0.001,
    frameon=False  # 可选：去掉图例边框
)

# S trend 手动添加右侧标签
cb2.ax.text(
    1.05, 0.5, r'($\times 10^{-3}$ y$^{-1}$)', 
    transform=cb2.ax.transAxes,
    va='center', ha='left',
    fontsize=7,
    fontweight='bold'
)
ax2.set_extent([-180, 180, -60, 80], crs=ccrs.PlateCarree())
# ===== 子图 3: D mean =====    
p3 = ax3.scatter(
    lon[lat_mask], lat[lat_mask],
    c=D_daily_mean[lat_mask],
    cmap=cmap_mean,
    vmax=D_daily_mean_vmax,
    vmin=D_daily_mean_vmin,
    s=4,
    alpha=0.7,
    transform=ccrs.PlateCarree(),
    edgecolors='none'
)
ax3.coastlines(linewidths=0.5)
ax3.text(
    0.06, 1.05,          # 相对坐标 (x, y)，以子图左下角为 (0,0)，右上角为 (1,1)
    '(b) Multi-year mean of RE (ISD)',
    transform=ax3.transAxes,
    fontsize=10,
    fontweight='bold'
)
# colorbar for s mean
cb3 = fig.colorbar(
    p3,
    ax=ax3,
    orientation='horizontal',
    fraction=0.07,
    pad=0.03,                        # 增大间距（默认0.1）
    shrink=0.9,
    extend='both',      
    extendrect=False  
)
ax3.set_extent([-180, 180, -60, 80], crs=ccrs.PlateCarree())
# ===== 子图 4: D trend =====
p4 = ax4.scatter(
    lon[lat_mask], lat[lat_mask],
    c=D_daily_trend[lat_mask],
    cmap=cmap_trend,
    norm=norm_d_trend,
    alpha=0.7,
    s=4,
    transform=ccrs.PlateCarree()
)

# 显著性用星形边框
d_sig_mask = D_daily_p <= 0.05
d_combined_mask = d_sig_mask & lat_mask
ax4.scatter(
    lon[d_combined_mask], lat[d_combined_mask],
    c=D_daily_trend[d_combined_mask],  # 数据值映射颜色
    cmap=cmap_trend,
    norm=norm_d_trend,
    alpha=0.7,
    edgecolors='black',
    linewidths=0.3,    #默认1
    s=4,
    transform=ccrs.PlateCarree()
)

ax4.coastlines(linewidths=0.5)
ax4.text(
    0.06, 1.05,
    '(e) Trend of RE (ISD)',
    transform=ax4.transAxes,
    fontsize=10,
    fontweight='bold'
)
# colorbar for D Trend
cb4 = fig.colorbar(
    p4,
    ax=ax4,
    orientation='horizontal',
    fraction=0.07,
    pad=0.03,                        # 增大间距（默认0.1）
    shrink=0.9,
    extend='both',      
    extendrect=False  
)

# 把图例放在 ax4 左下角
ax4.legend(
    handles=[sig_legend],
    loc='center',                     # 基准位置为中心
    bbox_to_anchor=(0.16, 0.1),       # 相对子图的坐标 (x, y)
    fontsize=9,
    framealpha=0.001,
    frameon=False  # 可选：去掉图例边框
)

# D trend 手动添加右侧标签
cb4.ax.text(
    1.05, 0.5, r'($\times 10^{-3}$ y$^{-1}$)', 
    transform=cb4.ax.transAxes,
    va='center', ha='left',
    fontsize=7,
    fontweight='bold'
)
ax4.set_extent([-180, 180, -60, 80], crs=ccrs.PlateCarree())
# ===== 子图 5: R mean =====  
p5 = ax5.scatter(
    lon[lat_mask], lat[lat_mask],
    c=R_daily_mean[lat_mask],
    cmap=cmap_mean,
    vmax=R_daily_mean_vmax,
    vmin=R_daily_mean_vmin,
    s=4,
    alpha=0.7,
    transform=ccrs.PlateCarree(),
    edgecolors='none'
)
ax5.coastlines(linewidths=0.5)
ax5.text(
    0.06, 1.05,          # 相对坐标 (x, y)，以子图左下角为 (0,0)，右上角为 (1,1)
    '(c) Multi-year mean of R/Rmax (ISD)',
    transform=ax5.transAxes,
    fontsize=10,
    fontweight='bold'
)
# colorbar for R mean
cb5 = fig.colorbar(
    p5,
    ax=ax5,
    orientation='horizontal',
    fraction=0.07,
    pad=0.03,                        # 增大间距（默认0.1）
    shrink=0.9,
    extend='both',      
    extendrect=False  
)

cb5.ax.text(
    #1.05, 0.5, r'($\times 10^{-3}$)', 
    1.05, 0.5, '', 
    transform=cb5.ax.transAxes,
    va='center', ha='left',
    fontsize=7,
    fontweight='bold'
)

ax5.set_extent([-180, 180, -60, 80], crs=ccrs.PlateCarree())
# ===== 子图 6: R trend =====
p6 = ax6.scatter(
    lon[lat_mask], lat[lat_mask],
    c=R_daily_trend[lat_mask],
    cmap=cmap_trend,
    norm=norm_r_trend,
    alpha=0.7,
    s=4,
    transform=ccrs.PlateCarree()
)

# 显著性用星形边框
r_sig_mask = R_daily_p <= 0.05
r_combined_mask = r_sig_mask & lat_mask  
ax6.scatter(
    lon[r_combined_mask], lat[r_combined_mask],
    c=R_daily_trend[r_combined_mask],  # 数据值映射颜色
    cmap=cmap_trend,
    norm=norm_r_trend,
    alpha=0.7,
    edgecolors='black',
    linewidths=0.3,    #默认1
    s=4,
    transform=ccrs.PlateCarree()
)

ax6.coastlines(linewidths=0.5)
ax6.text(
    0.06, 1.05,
    '(f) Trend of R/Rmax (ISD)',
    transform=ax6.transAxes,
    fontsize=10,
    fontweight='bold'
)
# colorbar for s Trend
cb6 = fig.colorbar(
    p6,
    ax=ax6,
    orientation='horizontal',
    fraction=0.07,
    pad=0.03,                        # 增大间距（默认0.1）
    shrink=0.9,
    extend='both',      
    extendrect=False  
)

# 把图例放在 ax6 左下角
ax6.legend(
    handles=[sig_legend],
    loc='center',                     # 基准位置为中心
    bbox_to_anchor=(0.16, 0.1),       # 相对子图的坐标 (x, y)
    fontsize=9,
    framealpha=0.001,
    frameon=False  # 可选：去掉图例边框
)

# R trend 手动添加右侧标签
cb6.ax.text(
    1.05, 0.5, r'($\times 10^{-3}$ y$^{-1}$)', 
    transform=cb6.ax.transAxes,
    va='center', ha='left',
    fontsize=7,
    fontweight='bold'
)
ax6.set_extent([-180, 180, -60, 80], crs=ccrs.PlateCarree())

plt.savefig("/data1/yyzhao/data/1980-2020/finally_result/picture/v5_figS5_square_6map_isd_3index_trend_monthly.png",
            dpi=300, bbox_inches='tight')
plt.close()
