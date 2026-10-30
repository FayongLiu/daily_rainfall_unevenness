# Code for plotting mean and trend by category, map


import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.colors import TwoSlopeNorm
import seaborn as sns
import time
import os
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.visualization import add_fignum, rename, get_alpha_label, cmap_cool, cmap_coolwarm, cool
from rainfall_ui.util.datainfo import CATEGORY_NAMES, CATEGORY_LS_80, CATEGORY_LS_50

args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr
CATEGORY_LS = CATEGORY_LS_80 if START_YEAR >= 1980 else CATEGORY_LS_50


# function to plot mean and trend by category
def plot_mean_trend_category_map(ds_ls, area_ds, land_ds, stat_ls, gauge_df, varname, gdf):
    ftsz = 10
    varname_lab = rename(varname)
    varname_mean = f'{varname}_mean'
    varname_trend = f'{varname}_trend'
    varname_ls = [varname_mean, varname_trend]
    clr = cool[5]
    cmap_mean = cmap_cool
    cmap_trend = cmap_coolwarm
    cmap_ls = [cmap_mean, cmap_trend]

    # load data
    if 'rain_day' in varname:
        trend_ds_ls = [ds[varname_trend] for ds in ds_ls]
        trend_df = gauge_df[varname_trend]
        lab_mean = f'Multi-year mean of {varname_lab} (day)'
        lab_trend = f'Trend of {varname_lab} (day yr$^-$$^1$)'
    elif 'STD_' in varname:
        trend_ds_ls = [ds[varname_trend] * 10 for ds in ds_ls]
        trend_df = gauge_df[varname_trend] * 10
        lab_mean = f'Multi-year mean of {varname_lab} (mm)'
        lab_trend = f'Trend of {varname_lab} (mm decade$^-$$^1$)'
    else:
        trend_ds_ls = [ds[varname_trend] * 1000 for ds in ds_ls]
        trend_df = gauge_df[varname_trend] * 1000
        if varname_lab == 'R/Rmax':
            lab_mean = 'Multi-year mean of $R$/$R$$_{max}$'
            lab_trend = 'Trend of $R$/$R$$_{max}$ (kyr$^-$$^1$)'
        else:
            lab_mean = f'Multi-year mean of {varname_lab}'
            lab_trend = f'Trend of {varname_lab} (kyr$^-$$^1$)'
    mean_ds_ls = [ds[varname_mean] for ds in ds_ls]
    mean_df = gauge_df[varname_mean]
    new_ds_ls = [mean_ds_ls, trend_ds_ls]
    df_ls = [mean_df, trend_df]
    label_ls = [lab_mean, lab_trend]

    # plot distribution
    fig, axes = plt.subplots(4, 2, figsize=(10, 9.5), dpi=300)
    axes = axes.flatten()
    plt.subplots_adjust(
        left=0.05,
        right=0.99,
        top=0.99,
        bottom=0.09,
        hspace=0.03,
        wspace=0.04
    )
    axes_mean_ls = [axes[0], axes[2], axes[4], axes[6]]
    axes_trend_ls = [axes[1], axes[3], axes[5], axes[7]]
    axes_ls = [axes_mean_ls, axes_trend_ls]

    notnan_mean = np.concatenate([var.values.flatten() for var in mean_ds_ls])
    notnan_mean = notnan_mean[~np.isnan(notnan_mean)]
    vmin_mean = np.percentile(notnan_mean, 5)
    vmax_mean = np.percentile(notnan_mean, 95)
    vcenter_mean = vmin_mean + vmax_mean / 2
    norm_mean = TwoSlopeNorm(vmin=vmin_mean, vcenter=vcenter_mean, vmax=vmax_mean)

    notnan_trend = np.concatenate([var.values.flatten() for var in trend_ds_ls])
    notnan_trend = notnan_trend[~np.isnan(notnan_trend)]
    vmin_trend = np.percentile(notnan_trend, 5)
    vmax_trend = np.percentile(notnan_trend, 95)
    vcenter_trend = 0
    norm_trend = TwoSlopeNorm(vmin=vmin_trend, vcenter=vcenter_trend, vmax=vmax_trend)
    norm_ls = [norm_mean, norm_trend]

    min_lon, max_lon = -180, 180
    min_lat, max_lat = -60, 90

    for i in range(2):
        cmap = cmap_ls[i]
        norm = norm_ls[i]
        axes_sub = axes_ls[i]
        sub_ds_ls = new_ds_ls[i]
        var_df = df_ls[i]
        label = label_ls[i]
        mean_ls = []
        std_ls = []
        for j in range(len(sub_ds_ls)):
            if j == 0:
                print(f'Plotting {varname_ls[i]}: {j+1}/{len(sub_ds_ls)}, gauge-based observations...')
                stat_trend_cols = ['non_sig', 'sig_inc', 'sig_dec']
            else:
                print(f'Plotting {varname_ls[i]}: {j+1}/{len(ds_ls)}, {CATEGORY_NAMES[j-1]}...')
                stat_trend_cols = ['non_sig_area', 'sig_inc_area', 'sig_dec_area']
            axname = axes_sub[j]
            var_ds = sub_ds_ls[j]
            # excluding the Antarctica
            var_ds = var_ds.sel(lat=slice(min_lat, max_lat))
            area_ds = area_ds.sel(lat=slice(min_lat, max_lat))
            # cal mean and std
            if j == 0:
                global_mean = var_df.mean().item()
                global_std = var_df.std().item()
            else:
                global_mean = var_ds.weighted(area_ds).mean(skipna=True).item()
                global_std = var_ds.weighted(area_ds).std(skipna=True).item()

            # plot the map
            # ================================================================================
            # add base map
            gdf = gdf.cx[min_lon:max_lon, min_lat:max_lat]
            gdf.plot(ax=axname, color='dimgray', linewidth=0.5)
            # plot the data
            land_ds = land_ds.sel(lat=slice(min_lat, max_lat))
            var_ds = var_ds.where(land_ds) # not show the small islands
            im = var_ds.plot(ax=axname, cmap=cmap, norm=norm, add_colorbar=False)
            axname.set_xlim(min_lon, max_lon)
            axname.set_ylim(min_lat, max_lat)
            axname.set_xticks([])
            axname.set_yticks([])
            axname.set_xlabel(None)
            axname.set_ylabel(None)
            axname.set_title('')
            
            # add annotation
            if varname == 'PRCP_ratio':
                txt = f'{global_mean:.3f}\u00b1{global_std:.2f}'
            else:
                txt = f'{global_mean:.2f}\u00b1{global_std:.2f}'
            if i == 0:
                axname.text(0.01, 0.01, txt, va='bottom', ha='left', fontsize=ftsz+1, transform=axname.transAxes)
            else:
                axname.text(0.99, 0.01, txt, va='bottom', ha='right', fontsize=ftsz+1, transform=axname.transAxes)

            mean_ls.append(global_mean)
            std_ls.append(global_std)
            fignum = get_alpha_label(i*4+j, with_parenthesis=False)
            add_fignum(axname, fignum, xoffset=0.01, yoffset=-0.1, ftsz=ftsz+2)
            ticks_y = np.array([-60, -30, 0, 30, 60])
            axname.set_yticks(ticks_y)
            axname.set_yticklabels([])
            ticks_x = np.arange(-120, 120.05, 60)
            axname.set_xticks(ticks_x)
            axname.set_xticklabels([])
            if i == 0:
                # add left yticks
                labels_y = [f'{abs(tick)}\xb0{"N" if tick > 0 else "S" if tick < 0 else " "}' for tick in ticks_y]
                axname.set_yticklabels(labels_y, fontsize=ftsz)
            if j == 3:
                # add bottom xticks
                labels_x = [f'{abs(int(tick))}\xb0{"E" if tick > 0 else "W" if tick < 0 else " "}' for tick in ticks_x]
                axname.set_xticklabels(labels_x, fontsize=ftsz)
        
            # plot significant trends stats
            # ================================================================================
            if i == 1:
                left = axname.get_position().x0 + 0.01
                bottom = axname.get_position().y0 + 0.025
                width = 0.25 * axname.get_position().width
                height = 0.3 * axname.get_position().height
                ax_add1 = fig.add_axes([left, bottom, width, height])
                # significant trends stats
                if j == 0:
                    # plot bar
                    stat_df = stat_ls[j].loc[varname, stat_trend_cols] * 100
                    x = np.arange(3)
                    y = stat_df.values
                    ax_add1.bar(x, y, color=clr, width=0.6, alpha=0.5)
                    y_text = y
                    y_loc = y
                else:
                    stat_df_ls = []
                    for stat_df in stat_ls[j]:
                        tempt_stat = stat_df.loc[varname, stat_trend_cols] * 100
                        tempt_stat = pd.DataFrame(tempt_stat)
                        tempt_stat.columns = ['percent']
                        tempt_stat['trend'] = tempt_stat.index
                        stat_df_ls.append(tempt_stat)
                    stat_df = pd.concat(stat_df_ls, axis=0)
                    y_text = stat_df.groupby('trend').mean()['percent'].values
                    y_text = [y_text[0], y_text[2], y_text[1]]
                    q1 = stat_df.groupby('trend')['percent'].quantile(0.25).values
                    q3 = stat_df.groupby('trend')['percent'].quantile(0.75).values
                    iqr = q3 - q1
                    y_loc = q3 + 1.5 * iqr
                    y_loc = [y_loc[0], y_loc[2], y_loc[1]]
                    # plot box
                    box_alp= 1.0
                    box_lw = 1.0
                    box_clr = clr
                    sns.boxplot(data=stat_df, x='trend', y='percent', color=box_clr, fill=None, ax=ax_add1, showmeans=True, showfliers=False, width=0.6,
                        boxprops={'alpha': box_alp, 'color': box_clr, 'linewidth': box_lw},
                        medianprops={'color': box_clr, 'linewidth': box_lw, 'alpha': box_alp},
                        whiskerprops={'color': box_clr, 'linewidth': box_lw, 'alpha': box_alp},
                        capprops={'color': box_clr, 'linewidth': box_lw,  'alpha': box_alp},
                        meanprops={'marker': 'o', 'markerfacecolor': 'none', 'markeredgecolor': box_clr,  'markeredgewidth': 1.0, 'markersize': 2},
                        flierprops={'marker': '+', 'markersize': 8, 'markeredgewidth': 1.0})
                ax_add1.set_xticks([0, 1, 2])
                ax_add1.set_xticklabels(['NS', '+', '-'], fontsize=ftsz)
                ax_add1.set_yticks([])
                ax_add1.set_ylabel('')
                ax_add1.set_xlabel('')
                # add text
                for k in range(3):
                    text = str(round(y_text[k])) + '%'
                    ax_add1.text(k, y_loc[k], text, va='bottom', ha='center', fontsize=ftsz)
                # remove border
                ax_add1.spines['right'].set_visible(False)
                ax_add1.spines['top'].set_visible(False)
                ax_add1.spines['left'].set_visible(False)

        # colorbar
        pos = axname.get_position()
        cbar_ax = fig.add_axes([pos.x0, pos.y0 - 0.05, pos.width, 0.015])
        cbar = fig.colorbar(im, cax=cbar_ax, orientation='horizontal', extend='both')
        cbar.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5, prune='both'))
        cbar.ax.tick_params(labelsize=ftsz)
        cbar.set_label(label, fontsize=ftsz)

        # save csv
        df = pd.DataFrame({
            'model': ['Guages'] + CATEGORY_NAMES,
            'mean': mean_ls,
            'std': std_ls
        })
        outpath =  rf'../fig_v4/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{varname_ls[i]}_categories.csv'
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        df.to_csv(outpath, index=False)
        print(f'Saving {outpath}')
    
    # save result
    outpath = rf'../fig_v4/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{varname}_mean_trend_categories_map.png'
    plt.savefig(outpath, dpi=300)
    print(f'Saving {outpath}')
    plt.close()

    return

def main():

    t1 = time.time()
    shp = r'/data4/dataset/lucc_boundary_map/global_coastline_110m/global_coastline_110m.shp'
    gdf = gpd.read_file(shp)

    station_nc_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.nc'
    station_csv_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.csv'
    station_stats_path = rf'../data/stats_sig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.csv'
    station_nc = xr.open_dataset(station_nc_path)
    station_csv = pd.read_csv(station_csv_path)
    station_stat = pd.read_csv(station_stats_path, index_col=0)
    ds_ls = [station_nc]
    stat_ls = [station_stat]

    input_path_area = r'../data/mask/area_mask_CRU_JRA.nc'
    area_ds = xr.open_dataset(input_path_area)['area']
    land_path = r'../data/mask/land_mask_ref.nc'
    land_ds = xr.open_dataset(land_path)['land']
    input_dir_data = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/'
    input_dir_stat = rf'../data/stats_sig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/'
    for i, model in enumerate(CATEGORY_NAMES):
        tempt_ds = xr.open_dataset(os.path.join(input_dir_data, f'grid_{model}_ensembles.nc'))
        ds_ls.append(tempt_ds)
        tempt_stat_ls = []
        category_ls = CATEGORY_LS[i]
        for sub_model in category_ls:
            tempt_stat = pd.read_csv(os.path.join(input_dir_stat, f'{sub_model}.csv'), index_col=0)
            tempt_stat_ls.append(tempt_stat)
        stat_ls.append(tempt_stat_ls)

    if START_YEAR == 1980:
        varnames = ['S_daily', 'PRCP_ratio', 'D_daily', 'S_monthly']#, 'D_monthly', 'rain_day']#, 'STD_daily_orig', 'STD_daily_detr']
    else:
        varnames = ['S_daily']
    for varname in varnames:
        plot_mean_trend_category_map(ds_ls, area_ds, land_ds, stat_ls, station_csv, varname, gdf)
    
    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")
    
    return


if __name__ == "__main__":
    
    main()

