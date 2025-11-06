# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib import gridspec
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import gaussian_kde
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import TwoSlopeNorm
import matplotlib.ticker as ticker
import matplotlib.lines as mlines
from scipy.stats import linregress

csv_file = "/data1/yyzhao/data/1980-2020/finally_result/data/v3_station_d_s/mean_trend/d_s_r_mean_trend.csv"

# ========== 读取 ==========
df = pd.read_csv(csv_file)

lon = df['lon']
lat = df['lat']

#S=ui;D=re;R = R/Rmax input
S_daily_mean = df['S_daily_mean']
S_daily_trend = df['S_daily_trend']* 1000
S_daily_p = df['S_daily_p_value']

D_daily_mean = df['D_daily_mean']
D_daily_trend = df['D_daily_trend']
D_daily_p = df['D_daily_p_value']

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
print('++++++++++++++++++++++++++++')
print(f"S Trend range: {S_daily_trend_1d.min():.5f} ~ {S_daily_trend_1d.max():.5f}")
print('++++++++++++++++++++++++++++')
print(f"D Trend range: {D_daily_trend_1d.min():.5f} ~ {D_daily_trend_1d.max():.5f}")
print(f"R Trend range: {R_daily_trend_1d.min():.5f} ~ {R_daily_trend_1d.max():.5f}")

print(f"every var mean and std:")
print(f"S Mean: {S_daily_mean_1d.mean():.5f} and {S_daily_mean_1d.std():.5f}")
print(f"D Mean: {D_daily_mean_1d.mean():.5f} and {D_daily_mean_1d.std():.5f}")
print(f"R Mean: {R_daily_mean_1d.mean():.5f} and {R_daily_mean_1d.std():.5f}")
print(f"S Trend: {S_daily_trend_1d.mean():.5f} and {S_daily_trend_1d.std():.5f}")
print(f"D Trend: {D_daily_trend_1d.mean():.5f} and {D_daily_trend_1d.std():.5f}")
print(f"R Trend: {R_daily_trend_1d.mean():.5f} and {R_daily_trend_1d.std():.5f}")

norm_s_trend = TwoSlopeNorm(vmin=S_daily_trend_vmin, vcenter=0, vmax=S_daily_trend_vmax)
norm_d_trend = TwoSlopeNorm(vmin=D_daily_trend_vmin, vcenter=0, vmax=D_daily_trend_vmax)
norm_r_trend = TwoSlopeNorm(vmin=R_daily_trend_vmin, vcenter=0, vmax=R_daily_trend_vmax)

# ========== 作图 ==========

proj = ccrs.PlateCarree()

fig = plt.figure(figsize=(12, 14))

gs = gridspec.GridSpec(
    5, 2,               # 多一行空白
    figure=fig,
    height_ratios=[1, 1, 1, 0.24, 0.7],  # 第4行是“空隙”
)
axes_map = [fig.add_subplot(gs[i, j], projection=proj) for i in range(3) for j in range(2)]
ax1, ax2, ax3, ax4, ax5, ax6 = axes_map
ax7 = fig.add_subplot(gs[4, 0])
ax8 = fig.add_subplot(gs[4, 1])

# === 调整整体间距 ===
plt.subplots_adjust(wspace=0.04, hspace=0.0003)

lat_mask = (lat >= -60) & (lat <= 80)
lat_ticks = [-60, -30, 0, 30, 60]
# 对每个子图设置纬度标签（仅前6个地图子图）
for i, ax in enumerate(axes_map):
    if i <= 5:  # 仅对子图 0~5（即前6个地图）执行
        # 设置纬度刻度
        ax.set_yticks(lat_ticks, crs=ccrs.PlateCarree())

        # 设置标签格式（纬度°符号）
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%d\u00B0'))

        # 根据子图位置决定标签位置（偶数：左侧；奇数：右侧）
        if i % 2 == 0:  # 左侧子图（0, 2, 4）
            ax.yaxis.set_label_position('left')
            ax.yaxis.tick_left()
        else:  # 右侧子图（1, 3, 5）
            ax.yaxis.set_label_position('right')
            ax.yaxis.tick_right()

        # 移除经度刻度
        ax.set_xticks([])
    else:
        # 子图编号 > 6（非地图子图）不做任何地图坐标设置
        continue
    
    
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
    f'(a) Multi-year mean of UI (ISD), {S_daily_mean_1d.mean():.2f} \u00B1 {S_daily_mean_1d.std():.2f}',
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
    1.05, 0.5, r'(kyr$^{-1}$)', 
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
    1.05, 0.5, '(yr$^{-1}$)', 
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
    1.05, 0.5, r'(kyr$^{-1}$)', 
    transform=cb6.ax.transAxes,
    va='center', ha='left',
    fontsize=7,
    fontweight='bold'
)
ax6.set_extent([-180, 180, -60, 80], crs=ccrs.PlateCarree())

# ===== 子图 7: 箱型图（S_daily_mean 分布比较） =====
# 定义掩码
mask_pos = (S_daily_p <= 0.05) & (S_daily_trend > 0)
mask_neg = (S_daily_p <= 0.05) & (S_daily_trend < 0)
# 提取对应的 S_daily_mean
S_mean_pos = S_daily_mean[mask_pos]
S_mean_neg = S_daily_mean[mask_neg]

print("+++++++++++++++++++++++++")
print(f"S_mean_pos: {S_mean_pos.mean():.5f} and {S_mean_pos.std():.5f}")
print(f"S_mean_neg: {S_mean_neg.mean():.5f} and {S_mean_neg.std():.5f}")
print("+++++++++++++++++++++++++")
# 组合数据
data_box = [S_mean_pos, S_mean_neg]
labels_box = ['Significant increase', 'Significant decrease']
p7 = ax7.boxplot(
    data_box,
    tick_labels=labels_box,
    patch_artist=True,
    boxprops=dict(facecolor='none', edgecolor="#EAB080", linewidth=1.5),
    medianprops=dict(color='black', linestyle='--', linewidth=1),
    whiskerprops=dict(color="#EAB080", linewidth=1.5),
    capprops=dict(color="#EAB080", linewidth=1.5),
    flierprops=dict(marker='o', color="#EAB080", alpha=0.7, markersize=3)
    #flierprops=dict(marker='o', markerfacecolor="#EAB080", alpha=0.7, markersize=3)
)
# 子图标题
ax7.text(
   0.06, 1.05,
    '(g) UI mean in different regions',
    transform=ax7.transAxes,
    fontsize=10,
    fontweight='bold'
)
# Y轴标签
ax7.set_ylabel("UI mean", fontsize=9)
# 添加每类的样本数量
ax7.text(
    0.05, 0.87,
    f"The number of significantly increasing UIs = {len(S_mean_pos)}",
    transform=ax7.transAxes,
    fontsize=9,
    color="#EAB080",
    fontweight='bold'
)
ax7.text(
    0.05, 0.80,
    f"The number of significantly decreasing UIs = {len(S_mean_neg)}",
    transform=ax7.transAxes,
    fontsize=9,
    color="#EAB080",
    fontweight='bold'
)
# 调整箱型图范围
ax7.set_ylim(
    np.nanmin(np.concatenate([S_mean_pos, S_mean_neg])) * 0.5,
    np.nanmax(np.concatenate([S_mean_pos, S_mean_neg])) * 1.3
)

# ===== 子图 8: 线性回归 =====
ax8_mask = (~S_daily_mean.isna()) & (~S_daily_trend.isna())
ax8_S_daily_mean = S_daily_mean[ax8_mask]
ax8_S_daily_trend = S_daily_trend[ax8_mask]

slope, intercept, r_value, p_value, std_err = linregress(ax8_S_daily_mean, ax8_S_daily_trend)
line_x = np.linspace(ax8_S_daily_mean.min(), ax8_S_daily_mean.max(), 5000)
line_y = intercept + slope * line_x

ax8.scatter(
    ax8_S_daily_mean, ax8_S_daily_trend,
    color='gray', alpha=0.6, s=20, edgecolors='none', zorder=2
)

ax8.plot(line_x, line_y, color="#EAB080", lw=1.3, zorder=3)

ax8.text(
    0.05, 0.85,
    f"Slope = {slope:.2f}/kyr, $p$ = {p_value:.2f}",
    transform=ax8.transAxes,
    color="#EAB080", fontsize=10, fontweight='bold'
)

ax8.axhline(0, color='gray', linestyle='--', linewidth=1, zorder=1)
ax8.axvline(0, color='gray', linestyle='--', linewidth=1, zorder=1)

ax8.set_xlabel("UI mean", fontsize=11)
ax8.set_ylabel("UI trend", fontsize=11)
ax8.yaxis.tick_right()                # 将刻度移到右侧
ax8.yaxis.set_label_position("right") # 将标签移到右侧

nx_min = np.percentile(ax8_S_daily_mean, 1)
nx_max = np.percentile(ax8_S_daily_mean, 99)
ny_min = np.percentile(ax8_S_daily_trend, 1)
ny_max = np.percentile(ax8_S_daily_trend, 99)
nx_range = nx_max - nx_min
ny_range = ny_max - ny_min

ax8.set_xlim(nx_min - 0.3*nx_range, nx_max + 0.8*nx_range)
ax8.set_ylim(ny_min - 1.3*ny_range, ny_max + 1.3*ny_range)

ax8.text(
    0.06, 1.05, 
    "(h) Relationship between UI mean and UI trend",
    transform=ax8.transAxes,
    fontsize=10,
    fontweight='bold'

)

plt.savefig("/data1/yyzhao/data/1980-2020/finally_result/picture/v6_fig1_6map_2fig_isd_mean_trend.png",
            dpi=300, bbox_inches='tight')
plt.close()