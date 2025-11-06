# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import xarray as xr
from matplotlib.patches import Patch
from scipy.stats import shapiro, ttest_rel, wilcoxon, levene, ttest_ind, mannwhitneyu
import cartopy.crs as ccrs
from matplotlib import ticker
from sklearn.metrics import r2_score

def significance_test(ref, test):
#csv文件与nc文件的显著性检验
    print("*" * 40)
    print(f"Original ref length: {len(ref)}, test length: {len(test)}")
    valid = ~np.isnan(ref) & ~np.isnan(test)
    ref = ref[valid]
    test = test[valid]
    print(f"Valid ref length: {len(ref)}, Valid test length: {len(test)}")
    #print(f"First 10 ref: {ref[:10]}")
    #print(f"First 10 test: {test[:10]}")
    diff = ref - test
    #print(f"Difference mean: {np.mean(diff):.6f}, std: {np.std(diff):.6f}, min: {np.min(diff):.6f}, max: {np.max(diff):.6f}")

    alpha = 0.05

    try:
        ref_shapiro = shapiro(ref).pvalue
    except Exception as e:
        ref_shapiro = np.nan
        #print(f"Shapiro error on ref: {e}")

    try:
        test_shapiro = shapiro(test).pvalue
    except Exception as e:
        test_shapiro = np.nan
        #print(f"Shapiro error on test: {e}")

    ref_norm = ref_shapiro >= alpha
    test_norm = test_shapiro >= alpha

    #print(f"Shapiro ref p-value: {ref_shapiro:.6f} -> normal: {ref_norm}")
    #print(f"Shapiro test p-value: {test_shapiro:.6f} -> normal: {test_norm}")

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
    print("*" * 40)
    return p_value


def find_nearest(array, value):
#找最近的数据点
    idx = (np.abs(array - value)).argmin()
    return idx

def extract_matched_values(nc_file, csv_file, var_name, dataset_name='', return_mask=False):

    nc_data = xr.open_dataset(nc_file)
    csv_df = pd.read_csv(csv_file)
    lons = nc_data['lon'].values
    lats = nc_data['lat'].values
    matched_values = []
    mask = np.zeros(nc_data[var_name].values.size, dtype=bool)

    for _, row in csv_df.iterrows():
        lon, lat = row['lon'], row['lat']
        lon_idx = find_nearest(lons, lon)
        lat_idx = find_nearest(lats, lat)
        value = nc_data[var_name].values[lat_idx, lon_idx]
        matched_values.append(value)
        flat_index = lat_idx * len(lons) + lon_idx
        if 0 <= flat_index < len(mask):
            mask[flat_index] = True

    print(f"FIG4 Dataset: {dataset_name if dataset_name else 'Unknown'}")
    print(f"  fig4 Number of matched grid points: {len(matched_values)}")

    nc_data.close()
    if return_mask:
        return np.array(matched_values), mask
    else:
        return np.array(matched_values)

def calculate_percentages(data, trend_var, pvalue_var):
    total = len(data)
    print(f"calculate_percentages: total valid samples = {total}")    
    if total == 0:
        return {
            'positive_significant': 0,
            'negative_significant': 0,
            'non_significant': 0
        }
    pos_sig = np.sum((data[trend_var] > 0) & (data[pvalue_var] <= 0.05))
    neg_sig = np.sum((data[trend_var] < 0) & (data[pvalue_var] <= 0.05))
    non_sig = np.sum(data[pvalue_var] > 0.05)
    return {
        'positive_significant': pos_sig / total * 100,
        'negative_significant': neg_sig / total * 100,
        'non_significant': non_sig / total * 100
    }

# ----------------- 单个NC文件 -----------------
def process_data(csv_file, other_file):
    csv_data = pd.read_csv(csv_file)
    is_nc = str(other_file).endswith(".nc")

    results = {
        'S_daily': {'percentages': None, 'test_p': None},
        'D_daily': {'percentages': None, 'test_p': None},
        'PRCP_ratio': {'percentages': None, 'test_p': None}
    }

    # ---- 情况 1: CSV 对 CSV ----
    if not is_nc:
        data = pd.read_csv(other_file)
        var_mapping = {
            'S_daily': ('S_daily_trend', 'S_daily_p_value'),
            'D_daily': ('D_daily_trend', 'D_daily_p_value'),
            'PRCP_ratio': ('PRCP_ratio_trend', 'PRCP_ratio_p_value')
        }

        for key, (trend_var, pvalue_var) in var_mapping.items():
            if trend_var in data.columns and pvalue_var in data.columns:
                valid_data = data.dropna(subset=[trend_var, pvalue_var])
                percentages = calculate_percentages(valid_data, trend_var, pvalue_var)
                results[key]['percentages'] = percentages
        return results

    # ---- 情况 2: CSV 对 NC ----
    else:
        nc_data = xr.open_dataset(other_file)
        var_mapping = {
            'S_daily': ('S_daily_trend', 'S_daily_p_value', 'S_daily_trend'),
            'D_daily': ('D_daily_trend', 'D_daily_p_value', 'D_daily_trend'),
            'PRCP_ratio': ('R_ratio_slope', 'R_ratio_p_values', 'R_ratio_slope')
        }

        for key, (trend_var, pvalue_var, dataset_name) in var_mapping.items():
            try:
                if key == 'PRCP_ratio':
                    csv_vals = csv_data['PRCP_ratio_trend'].values
                else:
                    csv_vals = csv_data[trend_var].values
            except Exception:
                csv_vals = np.array([])

            try:
                nc_vals, mask = extract_matched_values(other_file, csv_file, trend_var, dataset_name=dataset_name, return_mask=True)
            except Exception as e:
                print(f"Warning extracting {trend_var} from {other_file}: {e}")
                nc_vals, mask = np.array([]), np.zeros(0, dtype=bool)

            # 计算显著性检验
            p_val = significance_test(csv_vals, nc_vals)

            # 使用匹配点计算百分比
            if trend_var in nc_data.variables and pvalue_var in nc_data.variables and mask.any():
                trend_vals = nc_data[trend_var].values.flatten()[mask]
                pvals_vals = nc_data[pvalue_var].values.flatten()[mask]

                mask_valid = (~np.isnan(trend_vals)) & (~np.isnan(pvals_vals))
                df_local = pd.DataFrame({
                    trend_var: trend_vals[mask_valid],
                    pvalue_var: pvals_vals[mask_valid]
                })
                percentages = calculate_percentages(df_local, trend_var, pvalue_var)
            else:
                percentages = {'positive_significant': 0, 'negative_significant': 0, 'non_significant': 0}

            results[key]['percentages'] = percentages
            results[key]['test_p'] = p_val

        nc_data.close()
        return results


def process_cmip6_data(csv_file, folder_s, folder_d, folder_r):
    var_mapping = {
        'S_daily': ('S_daily_trend', 'S_daily_p_value', folder_s, 'S_daily_trend'),
        'D_daily': ('D_daily_trend', 'D_daily_p_value', folder_d, 'D_daily_trend'),
        'PRCP_ratio': ('R_ratio_trend', 'R_ratio_p_values', folder_r, 'R_ratio_trend')
    }

    all_results = {
        'S_daily': {'percentages': [], 'test_p': []},
        'D_daily': {'percentages': [], 'test_p': []},
        'PRCP_ratio': {'percentages': [], 'test_p': []}
    }

    csv_data = pd.read_csv(csv_file)

    for key, (trend_var, pvalue_var, folder_path, dataset_name) in var_mapping.items():
        nc_files = list(Path(folder_path).glob("*.nc"))
        print(f"\nProcessing {key}: Found {len(nc_files)} files in {folder_path}")

        for nc_file in nc_files:
            print(f"  Processing file: {nc_file.name}")
            try:
                ds = xr.open_dataset(nc_file)
            except Exception as e:
                print(f"  Failed to open {nc_file.name}: {e}")
                continue

            if trend_var not in ds or pvalue_var not in ds:
                print(f"  Warning: {trend_var} or {pvalue_var} not found in {nc_file.name}, skipped.")
                ds.close()
                continue

            # 1. 匹配点提取
            try:
                nc_matched_vals, mask = extract_matched_values(nc_file, csv_file, trend_var, dataset_name=dataset_name, return_mask=True)
            except Exception as e:
                print(f"  Warning extracting matched values for {nc_file.name}: {e}")
                nc_matched_vals, mask = np.array([]), np.zeros(0, dtype=bool)

            # 2. 计算显著性检验
            try:
                if key == 'PRCP_ratio':
                    csv_vals = csv_data['PRCP_ratio_trend'].values
                else:
                    csv_vals = csv_data[trend_var].values
            except Exception:
                csv_vals = np.array([])

            p_val = significance_test(csv_vals, nc_matched_vals)
            all_results[key]['test_p'].append(p_val)

            # 3. 使用匹配点计算百分比
            if mask.any():
                trend_vals = ds[trend_var].values.flatten()[mask]
                pvals_vals = ds[pvalue_var].values.flatten()[mask]
                mask_valid = (~np.isnan(trend_vals)) & (~np.isnan(pvals_vals))

                df_local = pd.DataFrame({
                    trend_var: trend_vals[mask_valid],
                    pvalue_var: pvals_vals[mask_valid]
                })
                percentages = calculate_percentages(df_local, trend_var, pvalue_var)
            else:
                percentages = {'positive_significant': 0, 'negative_significant': 0, 'non_significant': 0}

            all_results[key]['percentages'].append(percentages)
            ds.close()

    return all_results
    
def cmip6_star(pvals_list):
# --- 计算CMIP6星号标注 ---
    n = len(pvals_list)
    if n == 0:
        return ''
    count_005 = sum(p <= 0.05 for p in pvals_list)
    threshold = max(3, int(0.8 * n)) 
    if count_005 >= threshold:
        return '*'
    else:
        return ''
#-------------------   

#*************画图
def plot_trend_analysis(csv_file, cru_file, era5_file, cmip6_results, output_path):

    # ===================== 数据准备 =====================
    datasets = []    
    csv_results = process_data(csv_file, csv_file)
    datasets.append((csv_results, "ISD"))    

    cru_results = process_data(csv_file, cru_file)
    datasets.append((cru_results, "CRU"))

    era5_results = process_data(csv_file, era5_file)
    datasets.append((era5_results, "ERA5"))

    # ===================== 画图设置 =====================
    fig = plt.figure(figsize=(9, 15))
    gs = fig.add_gridspec(3, 1, hspace=0.22)
    axes = [
        fig.add_subplot(gs[0, 0]),  # (a) S_daily
        fig.add_subplot(gs[1, 0]),  # (b) D_daily
        fig.add_subplot(gs[2, 0]),  # (c) PRCP_ratio
    ]

    categories = ['Significant increase', 'Significant decrease', 'Non-significant']
    colors = ['#D6D6D6', '#9CB0C3', '#7C9D97', '#EAB080']  # ISD, CRU, ERA5, CMIP6
    labels = ['ISD', 'CRU-JRA', 'ERA5-Land', 'CMIP6']

    bar_width = 0.33  
    x = np.arange(len(categories)) * 1.7

    plot_vars = [
        ('S_daily', 'Daily UI'),
        ('D_daily', 'Daily RE'),
        ('PRCP_ratio', 'R/Rmax')
    ]

    # ===================== 绘图循环 =====================
    for ax_idx, (var_name, title) in enumerate(plot_vars):
        ax = axes[ax_idx]
        ax.text(0.02, 1.03, f'({chr(97 + ax_idx)}) {title}', transform=ax.transAxes, 
                fontsize=14, fontweight='bold')
        ax.set_ylabel('Percentage (%)')
        ax.set_ylim(0, 115)

        # ========== 绘制 ISD、CRU、ERA5 三个柱状图 ==========
        labels_with_stars = labels[:]  # 复制图例标签
        for idx, (dataset, label) in enumerate(zip(datasets, labels[:-1])):  
            results_dict, _ = dataset
            if var_name in results_dict:
                data = results_dict[var_name]
                percentages = data['percentages']
                pval = data['test_p']

                # 三类值
                values = [
                    percentages['positive_significant'],
                    percentages['negative_significant'],
                    percentages['non_significant']
                ]

                # 显著性星号
                star = ''
                if pval is not None and not np.isnan(pval):
                    star = '*' if pval <= 0.05 else ''

                labels_with_stars[idx] = label + (' ' + star if star else '')

                # 绘柱状图
                bar_pos = x + idx * bar_width
                bars = ax.bar(bar_pos, values, width=bar_width,
                              label=labels_with_stars[idx], color=colors[idx], alpha=0.8)
                # 数值标签
                for bar, val in zip(bars, values):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
                            f'{val:.1f}%', ha='center', va='bottom', fontsize=9)

        # ========== 绘制 CMIP6 箱线图 ==========

        cmip6_data = cmip6_results[var_name]
        cmip6_percentages_list = cmip6_data['percentages']
        
        # 将每个模型的百分比拆分成三个列表，用于画箱线图
        cmip6_data_percentages = [
            [p['positive_significant'] for p in cmip6_percentages_list],
            [p['negative_significant'] for p in cmip6_percentages_list],
            [p['non_significant'] for p in cmip6_percentages_list],
        ]
        positions = x + 3 * bar_width + 0.05
        bp = ax.boxplot(cmip6_data_percentages, positions=positions, widths=bar_width,
                        patch_artist=True,
                        medianprops=dict(color='black', linestyle='--', linewidth=1))
        for box in bp['boxes']:
            box.set(facecolor='none', edgecolor=colors[3], linewidth=1.5)
        for whisker in bp['whiskers']:
            whisker.set(color=colors[3], linewidth=1.5)
        for cap in bp['caps']:
            cap.set(color=colors[3], linewidth=1.5)
        for flier in bp['fliers']:
            flier.set(markeredgecolor=colors[3])

        # 中位数标注
        for i, data in enumerate(cmip6_data_percentages):
            median = np.median(data)
            if median > 80:
                y_offset, va = -14, 'top'
            elif 1 < median < 1.5:
                y_offset, va = 5, 'bottom'
            elif 1.5 < median < 3:
                y_offset, va = 8.5, 'bottom'
            elif 2 < median < 3:
                y_offset, va = 6, 'bottom'
            elif 4 < median < 5:
                y_offset, va = 13, 'bottom'
            elif 7 < median < 8:
                y_offset, va = 9, 'bottom'
            elif 6 < median < 7:
                y_offset, va = 13, 'bottom'

            else:
                y_offset, va = 0, 'bottom'
            ax.text(positions[i], median + y_offset, f'{median:.1f}%',
                    ha='center', va=va, fontsize=9)

        # 使用外部定义的 cmip6_star()
        cmip6_pvals = cmip6_data['test_p']
        star_cmip6 = cmip6_star(cmip6_pvals)  

        cmip6_label = labels[-1] + (' ' + star_cmip6 if star_cmip6 else '')

        # 图例
        legend_handles = [
            Patch(facecolor=colors[0], label=labels_with_stars[0]),
            Patch(facecolor=colors[1], label=labels_with_stars[1]),
            Patch(facecolor=colors[2], label=labels_with_stars[2]),
            Patch(facecolor='none', edgecolor=colors[3], label=cmip6_label, linewidth=1.5)
        ]
        ax.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(0.02, 0.98),
                  fontsize=10, frameon=False)

        # 坐标轴设置
        ax.set_xticks(x + 1.5 * bar_width)
        ax.set_xticklabels(categories)

    #plt.savefig(output_path, dpi=300)
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Plot saved to: {output_path}")
        
# 使用示例
def main():
    csv_file = "/data1/yyzhao/data/1980-2020/finally_result/data/v3_station_d_s/mean_trend/d_s_r_mean_trend.csv"
    cru_file = "/data1/yyzhao/data/1980-2020/finally_result/data/CRU_s_d_r_mean_slope_noarea.nc"
    era5_file = "/data1/yyzhao/data/1980-2020/finally_result/data/ERA5_s_d_r_mean_slope_noarea.nc"
    folder_s = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_s_resample_mean_slope_noarea/"
    folder_d = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_d_resample_mean_slope_noarea/"
    folder_r = "/data1/yyzhao/data/1980-2020/finally_result/data/CMIP6_r_resample_mean_slope_noarea/"

    output_path = "/data1/yyzhao/data/1980-2020/finally_result/picture/v6_fig4_3bar_regional_daily_grids.png"
    
    cmip6_results = process_cmip6_data(csv_file, folder_s, folder_d, folder_r)
    plot_trend_analysis(csv_file, cru_file, era5_file, cmip6_results, output_path)

if __name__ == '__main__':
    main()