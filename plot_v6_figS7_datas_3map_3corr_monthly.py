# -*- coding: utf-8 -*-
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


#导入文件
csv_file = "/data1/yyzhao/data/1980-2020/finally_result/data/v3_station_d_s/mean_trend/d_s_r_mean_trend.csv"
era5_file = "/data1/yyzhao/data/1980-2020/finally_result/data/ERA5_s_d_r_mean_slope_noarea.nc"
cru_file = "/data1/yyzhao/data/1980-2020/finally_result/data/CRU_s_d_r_mean_slope_noarea.nc"
cmip6_file = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_s_d_r_all_models_mean_slope_noarea.nc"

#读取csv文件变量
df = pd.read_csv(csv_file)
csv_lon = df['lon']
csv_lat = df['lat']

csv_s_mean = df['S_monthly_mean']
#读取era5文件变量
era5_ds = xr.open_dataset(era5_file)
era5_lon = era5_ds['lon']
era5_lat = era5_ds['lat']
era5_s_mean = era5_ds['S_monthly_mean']
#读取cru文件变量
cru_ds = xr.open_dataset(cru_file)
cru_lon = cru_ds['lon']
cru_lat = cru_ds['lat']
cru_s_mean = cru_ds['S_monthly_mean']
#读取cmip6文件变量
cmip6_ds = xr.open_dataset(cmip6_file)
cmip6_lon = cmip6_ds['lon']
cmip6_lat = cmip6_ds['lat']
cmip6_s_mean = cmip6_ds['S_monthly_mean']

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
    print(f"FIG2 Dataset: {dataset_name if dataset_name else 'Unknown'}")
    print(f"  fig2 Number of matched grid points: {len(matched_values)}")
    print(f"  fig2 Mean: {np.nanmean(matched_values):.4f}")
    print(f"  fig2 Std:  {np.nanstd(matched_values):.4f}")
    print(f"  fig2 Min:  {np.nanmin(matched_values):.4f}")
    print(f"  fig2 Max:  {np.nanmax(matched_values):.4f}")
    print("-" * 40)

    return matched_values

def plot_comparison(csv_valid, nc_valids, p_values):
#画图
    # 设置投影
    proj = ccrs.PlateCarree()
    fig = plt.figure(figsize=(12, 10))
    #gs = gridspec.GridSpec(3, 2, figure=fig, width_ratios=[1,1])
    ax1 = fig.add_axes([0.05, 0.74 , 0.65, 0.3], projection=proj)  # [left(x), bottom(y), width, height]
    ax2 = fig.add_axes([0.67, 0.78 , 0.3, 0.26])
    ax3 = fig.add_axes([0.05, 0.39 , 0.65, 0.3], projection=proj)
    ax4 = fig.add_axes([0.67, 0.43 , 0.3, 0.26])
    ax5 = fig.add_axes([0.05, 0.04 , 0.65, 0.3], projection=proj)
    ax6 = fig.add_axes([0.67, 0.08 , 0.3, 0.26])
    map_axes = [ax1, ax3, ax5]
    scatter_axes = [ax2, ax4, ax6]
    
    
    # 设置颜色映射
    mean_clr = [
        "#D6D6D6", "#EDE8E0", "#FFF8E6", "#FAEBD7",
        "#FFE4B5", "#F5D7A1", "#EAB080"
    ]
    cmap_mean = LinearSegmentedColormap.from_list("white_yellow_orange", mean_clr, N=256)
    
    # 设置纬度范围和刻度
    lat_ticks = [-60, -30, 0, 30, 60]
    
    # 遍历每个数据集进行绘图
                                              
    for i, (name, ds, nc_valid, p_value) in enumerate(zip(
        ['CRU-JRA', 'ERA5-Land', 'CMIP6 ensembles'],
        [cru_ds, era5_ds, cmip6_ds],
        nc_valids,
        p_values
    )):

        # 左列：空间分布图
        ax_map = map_axes[i]
        data = ds['S_monthly_mean'].values
        
        # 计算数据范围（去除NaN值）
        data_1d = data.flatten()
        data_1d = data_1d[~np.isnan(data_1d)]
        vmin = np.percentile(data_1d, 10)
        vmax = np.percentile(data_1d, 90)
        
        # 绘制地图
        p = ax_map.pcolormesh(
            ds.lon,
            ds.lat,
            data,
            cmap=cmap_mean,
            vmax=vmax,
            vmin=vmin,
            transform=ccrs.PlateCarree()
        )
        
        ax_map.coastlines(linewidths=0.5)
        ax_map.set_extent([-180, 180, -60, 80], crs=ccrs.PlateCarree())
        ax_map.set_yticks(lat_ticks, crs=ccrs.PlateCarree())
        ax_map.yaxis.set_label_position('left')
        ax_map.yaxis.tick_left()
        ax_map.yaxis.set_major_formatter(ticker.FormatStrFormatter('%d\u00B0'))
        
        # 添加标题
        ax_map.text(
            0.04, 1.04,
            f'({chr(97+i)}) Multi-year mean of UI ({name})',
            transform=ax_map.transAxes,
            fontsize=12,
            fontweight='bold'
        )
        
        # 添加colorbar
        fig.colorbar(
            p,
            ax=ax_map,
            orientation='horizontal',
            fraction=0.05,
            pad=0.07,
            extend='both',
            extendrect=False
        )
        
        # 右列：散点图
        ax_scatter = scatter_axes[i]
        
        valid_csv = csv_valid
        valid_nc = nc_valid

        # 计算R2
        #r_squared = r2_score(valid_csv, valid_nc)
        #r_squared = max(r_squared, 0)
        # 计算R相关系数
        r_squared = np.corrcoef(valid_csv, valid_nc)[0, 1]
        # 绘制散点图
        ax_scatter.scatter(valid_csv, valid_nc, facecolor="#EAB080",  s=10, alpha=0.8)
        
        ax_scatter.set_xlabel('ISD')
        ax_scatter.set_ylabel(name) 
        ax_scatter.yaxis.set_label_position('right')
        ax_scatter.yaxis.tick_right()
        
        # 添加1:1线
        #min_val = min(min(valid_csv), min(valid_nc))
        #max_val = max(max(valid_csv), max(valid_nc))
        #line = ax_scatter.plot([min_val, max_val], [min_val, max_val],
                             #color='black', linestyle='--', linewidth=1,
                             #label='1:1 Line')[0]
        # 添加R2值
        ax_scatter.text(0.95, 0.05,
                       f'r = {r_squared:.2f}',
                       transform=ax_scatter.transAxes,
                       fontsize=10, fontweight='bold',
                       va='bottom', ha='right')
        
        # 添加显著性标记
        significance = ''
        if p_value <= 0.05:
            significance = '*'
        
        # 添加标题
        ax_scatter.text(0.04, 1.09,
                       f'({chr(100 + i)}) {name} vs ISD {significance}',
                       transform=ax_scatter.transAxes,
                       fontsize=12, fontweight='bold',
                       va='top', ha='left')
        
        # 添加图例
        #ax_scatter.legend(
            #handles=[line],
            #loc='upper right',
            #frameon=True,
            #facecolor='white',   # 填充背景白色
            #edgecolor='white',   # 边框白色
            #framealpha=1.0       # 完全不透明
        #)

    plt.savefig("/data1/yyzhao/data/1980-2020/finally_result/picture/v5_figS7_square_datas_3map_3corr_mean_monthly.png",
            dpi=300, bbox_inches='tight')
    
    return fig


def main():
    # 提取匹配值
    era5_matched = extract_matched_values(era5_ds, df, 'S_monthly_mean', dataset_name='ERA5')
    cru_matched = extract_matched_values(cru_ds, df, 'S_monthly_mean', dataset_name='CRU')
    cmip6_matched = extract_matched_values(cmip6_ds, df, 'S_monthly_mean', dataset_name='CMIP6')

    # 统一掩膜：三套nc数据+csv同时去掉NaN
    mask_all = (~np.isnan(df['S_monthly_mean']) &
                ~np.isnan(era5_matched) &
                ~np.isnan(cru_matched) &
                ~np.isnan(cmip6_matched))
    print("\nMask check before filtering:")
    print(f"  CSV original count:   {len(df['S_monthly_mean'])}")
    print(f"  ERA5 matched count:   {len(era5_matched)}")
    print(f"  CRU matched count:    {len(cru_matched)}")
    print(f"  CMIP6 matched count:  {len(cmip6_matched)}")

    print("\nMask check after filtering:")
    print(f" Mask True count: {np.sum(mask_all)}")

    csv_valid = df['S_monthly_mean'].values[mask_all]
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
    era5_pvalue = significance_test(df['S_monthly_mean'].values, era5_matched)

    print("\nCRU vs CSV significance_test:")
    cru_pvalue = significance_test(df['S_monthly_mean'].values, cru_matched)

    print("\nCMIP6 vs CSV significance_test:")
    cmip6_pvalue = significance_test(df['S_monthly_mean'].values, cmip6_matched)

    # 绘图（传统一掩膜后的数据）
    p_values = [cru_pvalue, era5_pvalue, cmip6_pvalue]
    fig = plot_comparison(csv_valid, [cru_valid, era5_valid, cmip6_valid], p_values)

    return era5_pvalue, cru_pvalue, cmip6_pvalue

if __name__ == '__main__':
    main()
