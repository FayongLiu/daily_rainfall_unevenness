# -*- coding: utf-8 -*-
import os
import pandas as pd
import xarray as xr
import numpy as np
from scipy.stats import shapiro, ttest_rel, wilcoxon, levene, ttest_ind, mannwhitneyu
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from matplotlib import ticker
from matplotlib.colors import LinearSegmentedColormap
from sklearn.metrics import r2_score
import matplotlib.gridspec as gridspec
from matplotlib.colors import TwoSlopeNorm
from scipy.stats import linregress

def significance_test(ref, test):
#csv文件与nc文件的显著性检验
    print(f"Original ref length: {len(ref)}, test length: {len(test)}")
    valid = ~np.isnan(ref) & ~np.isnan(test)
    ref = ref[valid]
    test = test[valid]
    print(f"Valid ref length: {len(ref)}, Valid test length: {len(test)}")
    print(f"First 10 ref: {ref[:10]}")
    print(f"First 10 test: {test[:10]}")
    diff = ref - test
    print(f"Difference mean: {np.mean(diff):.6f}, std: {np.std(diff):.6f}, min: {np.min(diff):.6f}, max: {np.max(diff):.6f}")

    alpha = 0.05

    try:
        ref_shapiro = shapiro(ref).pvalue
    except Exception as e:
        ref_shapiro = np.nan
        print(f"Shapiro error on ref: {e}")

    try:
        test_shapiro = shapiro(test).pvalue
    except Exception as e:
        test_shapiro = np.nan
        print(f"Shapiro error on test: {e}")

    ref_norm = ref_shapiro >= alpha
    test_norm = test_shapiro >= alpha

    print(f"Shapiro ref p-value: {ref_shapiro:.6f} -> normal: {ref_norm}")
    print(f"Shapiro test p-value: {test_shapiro:.6f} -> normal: {test_norm}")

    is_paired = len(ref) == len(test)
    print(f"Is paired: {is_paired}")

    if is_paired:
        if ref_norm and test_norm:
            print("Using paired t-test")
            _, p_value = ttest_rel(ref, test)
        else:
            print("Using Wilcoxon signed-rank test")
            _, p_value = wilcoxon(ref, test)
    else:
        if ref_norm and test_norm:
            levene_p = levene(ref, test).pvalue
            equal_var = levene_p >= alpha
            print(f"Levene p-value: {levene_p:.6f} -> equal var: {equal_var}")
            print("Using independent t-test")
            _, p_value = ttest_ind(ref, test, equal_var=equal_var)
        else:
            print("Using Mann-Whitney U test")
            _, p_value = mannwhitneyu(ref, test)

    print(f"Calculated p-value: {p_value:.6f}")
    return p_value


def find_nearest(array, value):
#找最近的数据点
    idx = (np.abs(array - value)).argmin()
    return idx
    
def extract_matched_values(nc_data, csv_df, var_name, dataset_name=''):

    lons = nc_data['lon'].values
    lats = nc_data['lat'].values
    matched_values = []

    for _, row in csv_df.iterrows():
        lon = row['lon']
        lat = row['lat']
        lon_idx = find_nearest(lons, lon)
        lat_idx = find_nearest(lats, lat)
        value = nc_data[var_name].values[lat_idx, lon_idx]
        matched_values.append(value)

    matched_values = np.array(matched_values)

    # 打印统计信息
    print(f"fig3 Dataset: {dataset_name if dataset_name else 'Unknown'}")
    print(f"  fig3 Number of matched grid points: {len(matched_values)}")
    print(f"  fig3 Mean: {np.nanmean(matched_values):.8f}")
    print(f"  fig3 Std:  {np.nanstd(matched_values):.8f}")
    print(f"  fig3 Min:  {np.nanmin(matched_values):.8f}")
    print(f"  fig3 Max:  {np.nanmax(matched_values):.8f}")
    print("-" * 40)

    return matched_values
# ===============================================
# ====== 新增：空间平均时间序列相关函数 ======
# ===============================================
def calc_spatial_mean(file_path, is_nc=True):
    if is_nc:
        # 读取 NetCDF 文件
        ds = xr.open_dataset(file_path)        
        # 检查变量
        if 'S_daily' not in ds.variables:
            print(f"skip file because not find S daily : {os.path.basename(file_path)}")
            return None        
        # 提取变量并去除 NaN
        S_daily = ds['S_daily'].where(~np.isnan(ds['S_daily']), drop=True)        
        # 在空间维度上取平均，保留时间维度
        spatial_mean = S_daily.mean(dim=['lon', 'lat'], skipna=True)        
        # 单位换算
        spatial_mean = spatial_mean * 1000        
        return spatial_mean
    else:
        # 若是 CSV 文件夹
        csv_files = sorted([f for f in os.listdir(file_path) if f.endswith('.csv')])
        all_data = []

        for f in csv_files:
            df = pd.read_csv(os.path.join(file_path, f))
            if not {'year', 'S_daily'}.issubset(df.columns):
                print(f"file:{f} dont has column: {required_cols}")
                continue
            # 去除 NaN 并计算每年平均
            yearly_mean = df.dropna(subset=['S_daily']).groupby('year')['S_daily'].mean()
            # 单位换算
            yearly_mean = yearly_mean * 1000
            all_data.append(yearly_mean)
        if not all_data:
            return None        
        # 合并多个文件的结果
        combined_df = pd.concat(all_data, axis=1)
        return combined_df.mean(axis=1, skipna=True)

def process_nc_folder(folder_path):
    nc_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.nc')])
    results = {}
    for f in nc_files:
        try:
            result = calc_spatial_mean(os.path.join(folder_path, f), is_nc=True)
            if result is not None:
                results[f] = result
        except Exception as e:
            print(f"skip {f}: {e}")
    return results

#导入文件
# ====== 第一套（原数据）======
csv_file = "/data1/yyzhao/data/1980-2020/finally_result/data/v3_station_d_s/mean_trend/d_s_r_mean_trend.csv"
era5_file = "/data1/yyzhao/data/1980-2020/finally_result/data/ERA5_s_d_r_mean_slope_noarea.nc"
cru_file = "/data1/yyzhao/data/1980-2020/finally_result/data/CRU_s_d_r_mean_slope_noarea.nc"
cmip6_file = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_s_d_r_all_models_mean_slope_noarea.nc"
# === 原始数据读取（用于下方6个子图） ===
df = pd.read_csv(csv_file)
era5_ds = xr.open_dataset(era5_file)
cru_ds = xr.open_dataset(cru_file)
cmip6_ds = xr.open_dataset(cmip6_file)
# 提取匹配值
era5_matched = extract_matched_values(era5_ds, df, 'S_daily_trend', dataset_name='ERA5')
cru_matched = extract_matched_values(cru_ds, df, 'S_daily_trend', dataset_name='CRU')
cmip6_matched = extract_matched_values(cmip6_ds, df, 'S_daily_trend', dataset_name='CMIP6')
# 统一掩膜：三套nc数据+csv同时去掉NaN 散点图
mask_all = (~np.isnan(df['S_daily_trend']) &
            ~np.isnan(era5_matched) &
            ~np.isnan(cru_matched) &
            ~np.isnan(cmip6_matched))
print("\nMask check before filtering:")
print(f"  CSV original count:   {len(df['S_daily_trend'])}")
print(f"  ERA5 matched count:   {len(era5_matched)}")
print(f"  CRU matched count:    {len(cru_matched)}")
print(f"  CMIP6 matched count:  {len(cmip6_matched)}")
print("\nMask check after filtering:")
print(f" Mask True count: {np.sum(mask_all)}")

csv_valid = df['S_daily_trend'].values[mask_all]
era5_valid = era5_matched[mask_all]
cru_valid = cru_matched[mask_all]
cmip6_valid = cmip6_matched[mask_all]


print(f"  CSV valid count: {len(csv_valid)}")
print(f"  ERA5 valid count: {len(era5_valid)}")
print(f"  CRU valid count: {len(cru_valid)}")
print(f"  CMIP6 valid count: {len(cmip6_valid)}")

# Check consistency
print(f"\nAll datasets have the same length: {len(csv_valid) == len(era5_valid) == len(cru_valid) == len(cmip6_valid)}")
# 显著性检验（仍用原始数据）

print("\nERA5 vs CSV significance_test:")
era5_pvalue = significance_test(df['S_daily_trend'].values, era5_matched)
print("\nCRU vs CSV significance_test:")
cru_pvalue = significance_test(df['S_daily_trend'].values, cru_matched)
print("\nCMIP6 vs CSV significance_test:")
cmip6_pvalue = significance_test(df['S_daily_trend'].values, cmip6_matched)

# ====== 第二套（新的 slope 数据）======
new_csv_file = "/data1/yyzhao/data/1980-2020/finally_result/data/v3_station_d_s/"
new_era5 = "/data1/yyzhao/data/1980-2020/finally_result/data/ERA5_s_d_noarea.nc"
new_cru = "/data1/yyzhao/data/1980-2020/finally_result/data/CRU_s_d_noarea.nc"
new_input_folder = "/data1/yyzhao/data/1980-2020/CMIP6/s/concat_s/"
# === 1. 计算三种数据的空间平均 ===
csv_mean_new = calc_spatial_mean(new_csv_file, is_nc=False)
cru_mean_new = calc_spatial_mean(new_cru, is_nc=True)
era5_mean_new = calc_spatial_mean(new_era5, is_nc=True)
cmip6_results_new = process_nc_folder(new_input_folder)
# === 2. 转为 Series ===
cru_series = pd.Series(cru_mean_new.values, index=cru_mean_new['time'].values)
era5_series = pd.Series(era5_mean_new.values, index=era5_mean_new['time'].values)
# === 3. CMIP6 多文件合并 ===
first_key = next(iter(cmip6_results_new))
ref_time = cmip6_results_new[first_key].time.values
ref_len = len(ref_time)

valid_results = {}
skipped_files = []
for name, data in cmip6_results_new.items():
    if len(data.time) != ref_len or not np.allclose(data.time.values, ref_time):
        print(f"skip file (time not match): {name}")
        skipped_files.append(name)
        continue
    valid_results[name] = data

if not valid_results:
    raise ValueError("no valid CMIP6 files found")

cmip6_df_new = pd.DataFrame({name: d.values for name, d in valid_results.items()},
                        index=ref_time)
cmip6_mean_new = cmip6_df_new.mean(axis=1, skipna=True)
print(f"succeed: {len(valid_results)}, skip: {len(skipped_files)}")
#__________________________________________________________________

#new fig 

proj = ccrs.PlateCarree()
fig = plt.figure(figsize=(12, 13))
#新图
ax1 = fig.add_axes([0.12, 0.80 , 0.76, 0.20])
#旧图
ax2 = fig.add_axes([0.01, 0.54 , 0.64, 0.21], projection=proj)
ax3 = fig.add_axes([0.60, 0.565 , 0.28, 0.185])
ax4 = fig.add_axes([0.01, 0.29 , 0.64, 0.21], projection=proj)
ax5 = fig.add_axes([0.60, 0.315 , 0.28, 0.185])
ax6 = fig.add_axes([0.01, 0.04 , 0.64, 0.21], projection=proj)
ax7 = fig.add_axes([0.60, 0.065 , 0.28, 0.185])

map_axes = [ax2, ax4, ax6]
scatter_axes = [ax3, ax5, ax7]

trend_clr = ["#9CB0C3", "#FFFFFF", "#EAB080"]
cmap_trend = LinearSegmentedColormap.from_list("blue2orange", trend_clr,N=256)

lat_ticks = [-60, -30, 0, 30, 60]

for i, (name, ds, nc_valid, p_value) in enumerate(zip(
    ['CRU-JRA', 'ERA5-Land', 'CMIP6 ensembles'],
    [cru_ds, era5_ds, cmip6_ds],
    [cru_valid, era5_valid, cmip6_valid],
    [cru_pvalue, era5_pvalue, cmip6_pvalue]
)):
    # 左列：空间分布图
    ax_map = map_axes[i]
    data = ds['S_daily_trend'].values * 1000
    S_daily_p = ds['S_daily_p_value'].values
    data_1d = data.flatten()
    data_1d = data_1d[~np.isnan(data_1d)]
    vmax = np.percentile(data_1d, 90)
    norm_trend = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
    p = ax_map.pcolormesh(
        ds.lon,
        ds.lat,
        data,
        cmap=cmap_trend,
        norm=norm_trend,
        transform=ccrs.PlateCarree()
    )

    significance_mask = (S_daily_p > 0.05) | np.isnan(S_daily_p)
    ax_map.contourf(
        ds.lon, ds.lat,
        significance_mask,
        hatches=[4*'.', ''],
        colors='none',
        transform=ccrs.PlateCarree()
    )

    ax_map.coastlines(linewidths=0.5)
    ax_map.set_extent([-180, 180, -60, 80], crs=ccrs.PlateCarree())
    ax_map.set_yticks(lat_ticks, crs=ccrs.PlateCarree())
    ax_map.yaxis.set_label_position('left')
    ax_map.yaxis.tick_left()
    ax_map.yaxis.set_major_formatter(ticker.FormatStrFormatter('%d\u00B0'))

    ax_map.text(
        0.04, 1.05,
        f'({chr(98+i)}) Trend of UI ({name})',
        transform=ax_map.transAxes,
        fontsize=12,
        fontweight='bold'
    )

    cb2 = fig.colorbar(
        p,
        ax=ax_map,
        orientation='horizontal',
        fraction=0.07,
        pad=0.04,
        extend='both',
        extendrect=False
    )
    cb2.ax.text(
        1.06, 0.5, r'(kyr$^{-1}$)',
        transform=cb2.ax.transAxes,
        va='center', ha='left',
        fontsize=8,
        fontweight='bold'
    )

    # 右列：散点图，直接用统一掩膜后的数据
    ax_scatter = scatter_axes[i]

    r_squared = np.corrcoef(csv_valid, nc_valid)[0, 1]

    ax_scatter.scatter(csv_valid, nc_valid, facecolor="#EAB080",  s=10, alpha=0.8)

    ax_scatter.set_xlabel('ISD')
    ax_scatter.set_ylabel(name)
    ax_scatter.yaxis.set_label_position('right')
    ax_scatter.yaxis.tick_right()

    ax_scatter.text(0.95, 0.05,
                   f'r = {r_squared:.2f}',
                   transform=ax_scatter.transAxes,
                   fontsize=10, fontweight='bold',
                   va='bottom', ha='right')

    significance = ''
    if p_value <= 0.05:
        significance = '*'

    ax_scatter.text(0.04, 1.09,
                   f'({chr(101 + i)}) {name} vs ISD {significance}',
                   transform=ax_scatter.transAxes,
                   fontsize=12, fontweight='bold',
                   va='top', ha='left')

#…………………………………………新图………………………………
new_colors = {
    'ISD': '#e41a1c',
    'CRU-JRA': '#377eb8',
    'ERA5-Land': '#4daf4a',
    'CMIP6 ensembles': '#ff7f00'
}

new_datasets = {
    'ISD': csv_mean_new,
    'CRU-JRA': cru_series,
    'ERA5-Land': era5_series
}

text_positions = {
    'ISD': 0.43,
    'CRU-JRA': 0.36,
    'ERA5-Land': 0.29
}

for label, data in new_datasets.items():
    x = np.array(data.index)
    y = np.array(data.values)

    ax1.scatter(x, y, color=new_colors[label], alpha=0.6, s=18,edgecolors='none', zorder=2,label=f"{label}")

    # === 线性回归 ===
    slope, intercept, r, p, sd = linregress(x, y)
    y_fit = slope * x + intercept
    
    print("+++++++++++++++++++++++++")
    print(f"{label}: {slope:.2f} and {sd:.5f}")
    print("+++++++++++++++++++++++++")
    ax1.plot(x, y_fit, color=new_colors[label], lw=2, zorder=3)
    ax1.text(
        0.03, text_positions[label],
        f"{label}: slope={slope:.2f}/kyr, $p$={p:.2f}",
        transform=ax1.transAxes,
        fontsize=10,fontweight='bold',
        color=new_colors[label],
        ha='left', va='top'
    )

ax1.set_xlabel("Year")
ax1.set_ylabel("Global averaged UI")


x_common = cmip6_mean_new.index
for col in cmip6_df_new.columns:
    ax1.scatter(x_common, cmip6_df_new[col], color='#ffcc99', alpha=0.4, s=10, zorder=1) #淡黄色多多透明

ax1.scatter(x_common, cmip6_mean_new, color=new_colors['CMIP6 ensembles'], alpha=0.6,edgecolors='none', zorder=2,
            s=18, label="CMIP6 ensembles") #集合的点

slope_true, intercept, r, p, sd_cmip6 = linregress(x_common, cmip6_mean_new)
y_fit = slope_true * x_common + intercept
ax1.plot(x_common, y_fit, color=new_colors['CMIP6 ensembles'], lw=2, zorder=3)

print("+++++++++++++++++++++++++")
print(f"CMIP6 ensembles: {slope_true:.2f} and {sd_cmip6:.5f}")
print("+++++++++++++++++++++++++")
    
ax1.text(
    0.03, 0.22,
    f"CMIP6 ensembles: slope={slope_true:.2f}/kyr, $p$={p:.2f}",
    transform=ax1.transAxes,
    fontsize=10,fontweight='bold',
    color=new_colors['CMIP6 ensembles'],
    ha='left', va='top'
)

#ax1.legend(frameon=False, fontsize=9,
           #loc='upper right', bbox_to_anchor=(0.985, 0.43),
           #bbox_transform=ax1.transAxes)

ax1.text(
    0.04, 1.05,
    f'(a) Time series of global averaged UI',
    transform=ax1.transAxes,
    fontsize=12,
    fontweight='bold'
)
               
plt.savefig("/data1/yyzhao/data/1980-2020/finally_result/picture/v6_fig3_square_datas_3map_3corr_trend.png",
        dpi=300, bbox_inches='tight')
plt.close()
