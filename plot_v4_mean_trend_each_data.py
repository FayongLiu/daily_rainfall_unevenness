# Code for plotting mean and trend of each data


import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.colors import TwoSlopeNorm
import time
import os
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.visualization import add_fignum, rename, get_alpha_label, cmap_cool, cmap_coolwarm, cool
from rainfall_ui.util.datainfo import DATA_LS_80, DATA_LS_50, CMIP6_LS

args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr
DATA_LS = DATA_LS_80 if START_YEAR >= 1980 else DATA_LS_50


# function to plot mean and trend of each data
def plot_mean_trend_each_data(ds_ls, area_ds_ls, land_ds, stat_ls, station_df, varname, gdf):
    ftsz = 10
    lab_varname = rename(varname)
    cmap_mean = cmap_cool
    cmap_trend = cmap_coolwarm
    clr = cool[5]

    # load data
    if 'trend' in varname:
        if 'rain_day' in varname:
            var_ls = [ds[varname] for ds in ds_ls]
            var_df = station_df[varname]
            label = f'Trend of {lab_varname} (day yr$^-$$^1$)'
        elif 'STD_' in varname:
            var_ls = [ds[varname] * 10 for ds in ds_ls]
            var_df = station_df[varname] * 10
            label = f'Trend of {lab_varname} (mm decade$^-$$^1$)'
        else:
            var_ls = [ds[varname] * 1000 for ds in ds_ls]
            var_df = station_df[varname] * 1000
            label = f'Trend of {lab_varname} (kyr$^-$$^1$)'
        cmap = cmap_trend
    else:
        var_ls = [ds[varname] for ds in ds_ls]
        var_df= station_df[varname]
        if 'rain_day' in varname:
            label = f'Multi-year mean of {lab_varname} (day)'
        elif 'STD_' in varname:
            label = f'Multi-year mean of {lab_varname} (mm)'
        else:
            label = f'Multi-year mean of {lab_varname}'
        cmap = cmap_mean

    # plot distribution
    fig, axes = plt.subplots(7, 5, figsize=(19, 12), dpi=300)
    axes = axes.flatten()
    to_delete = [9, 4]
    for idx in to_delete:
        fig.delaxes(axes[idx])
    axes = np.delete(axes, to_delete)
    plt.subplots_adjust(
        left=0.03,
        right=0.99,
        top=0.99,
        bottom=0.02,
        hspace=0.1,
        wspace=0.05
    )
    var_1d = np.concatenate([var.values.flatten() for var in var_ls])
    var_1d = var_1d[~np.isnan(var_1d)]
    vmin = np.percentile(var_1d, 1)
    vmax = np.percentile(var_1d, 99)
    vcenter = 0 if 'trend' in varname else (vmin + vmax) / 2
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    mean_ls = []
    std_ls = []
    for i in range(len(ds_ls)):
        if i == 0:
            print(f'Plotting {i+1}/{len(ds_ls)}, gauge-based observations...')
            stat_cols = ['non_sig', 'sig_inc', 'sig_dec']
        else:
            print(f'Plotting {i+1}/{len(ds_ls)}, {DATA_LS_80[i-1]}...')
            stat_cols = ['non_sig_area', 'sig_inc_area', 'sig_dec_area']
        axname = axes[i]
        var = var_ls[i]
        area_ds = area_ds_ls[i]
        # excluding the Antarctica
        min_lon, max_lon, min_lat, max_lat = -180, 180, -60, 90
        var = var.sel(lat=slice(min_lat, max_lat))
        area_ds = area_ds.sel(lat=slice(min_lat, max_lat))
        # cal mean and std
        if i == 0:
            model_name = 'Guages'
            global_mean = var_df.mean().item()
            global_std = var_df.std().item()
        else:
            global_mean = var.weighted(area_ds).mean(skipna=True).item()
            global_std = var.weighted(area_ds).std(skipna=True).item()
            model_name = DATA_LS_80[i-1]
            if model_name in CMIP6_LS:
                model_name = model_name.split('_')[0]
            else:
                model_name = model_name.replace('_', '-')

        # add base map
        gdf = gdf.cx[min_lon:max_lon, min_lat:max_lat]
        gdf.plot(ax=axname, color='dimgray', linewidth=0.5)
        # plot the data
        land_ds = land_ds.sel(lat=slice(min_lat, max_lat))
        if model_name in ['Gauges', 'CPC', 'CRU-JRA']:
            var = var.where(land_ds) # not show the small islands
        elif model_name in ['GPCC', 'REGEN-LM']:
            tempt_land_ds = land_ds.copy()
            tempt_land_ds = tempt_land_ds.reindex(lat=var.lat, lon=var.lon, method='nearest')
            var = var.where(tempt_land_ds)
        im = var.plot(ax=axname, cmap=cmap, norm=norm, add_colorbar=False)
        axname.set_xlim(-180, 180)
        axname.set_ylim(-60, 90)
        axname.set_xticks([])
        axname.set_yticks([])
        axname.set_xlabel(None)
        axname.set_ylabel(None)
        axname.set_title('')

        # add annotation
        txt = f'{global_mean:.2f}\u00b1{global_std:.2f}'
        if '_mean' in varname:
            axname.text(0.01, 0.01, txt, va='bottom', ha='left', fontsize=ftsz+1, transform=axname.transAxes)
        else:
            axname.text(0.99, 0.01, txt, va='bottom', ha='right', fontsize=ftsz+1, transform=axname.transAxes)
        mean_ls.append(global_mean)
        std_ls.append(global_std)
        fignum = get_alpha_label(i, with_parenthesis=False)
        add_fignum(axname, fignum, xoffset=0.01, yoffset=-0.1, ftsz=ftsz+2)
        ticks_y = np.array([-60, -30, 0, 30, 60])
        axname.set_yticks(ticks_y)
        axname.set_yticklabels([])
        ticks_x = np.arange(-120, 120.05, 60)
        axname.set_xticks(ticks_x)
        axname.set_xticklabels([])

        if i in [0, 4, 8, 13, 18, 23, 28]:
            # add left yticks
            labels_y = [f'{abs(tick)}\xb0{"N" if tick > 0 else "S" if tick < 0 else " "}' for tick in ticks_y]
            axname.set_yticklabels(labels_y, fontsize=ftsz)
        if i in [28, 29, 30, 31, 32]:
            # add bottom xticks
            labels_x = [f'{abs(int(tick))}\xb0{"E" if tick > 0 else "W" if tick < 0 else " "}' for tick in ticks_x]
            axname.set_xticklabels(labels_x, fontsize=ftsz)

        # add stats significance
        if 'trend' in varname:
            new_varname = varname.replace('_trend', '')
            stat_df = stat_ls[i].loc[new_varname,stat_cols] * 100
            left = axname.get_position().x0 + 0.005
            bottom = axname.get_position().y0 + 0.02
            width = 0.2 * axname.get_position().width
            height = 0.25 * axname.get_position().height
            ax_stat = fig.add_axes([left, bottom, width, height])
            x = np.arange(3)
            y = stat_df.values
            ax_stat.bar(x, y, color=clr, width=0.6, alpha=0.5)
            ax_stat.set_xticks(x)
            ax_stat.set_xticklabels(['NS', '+', '-'], fontsize=ftsz)
            ax_stat.set_yticks([])

            # add text
            for j in range(3):
                text = str(round(y[j])) + '%'
                ax_stat.text(j, y[j], text, va='bottom', ha='center', fontsize=ftsz)
            # remove border
            ax_stat.spines['right'].set_visible(False)
            ax_stat.spines['top'].set_visible(False)
            ax_stat.spines['left'].set_visible(False)

    # colorbar
    cbar_ax = fig.add_axes([0.87, 0.74, 0.015, 0.224])
    cbar = fig.colorbar(im, cax=cbar_ax, orientation='vertical', extend='both')
    cbar.ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=4, prune='both'))
    cbar.set_label(label, fontsize=12)

    # save result
    outpath = rf'../fig_v4/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{varname}_each_data.png'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=300)
    print(f'Saving {outpath}')
    plt.close()

    # save csv
    df = pd.DataFrame({
        'model': ['Guages'] + DATA_LS_80,
        'mean': mean_ls,
        'std': std_ls
    })
    df.to_csv(outpath.replace('.png', '.csv'), index=False)
    print(f'Saving {outpath.replace(".png", ".csv")}')

    return

def main():

    t1 = time.time()
    shp = r'/data4/dataset/lucc_boundary_map/global_coastline_110m/global_coastline_110m.shp'
    gdf = gpd.read_file(shp)
    land_path = r'../data/mask/land_mask_ref.nc'
    land_ds = xr.open_dataset(land_path)['land']

    station_nc_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.nc'
    station_csv_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.csv'
    station_stats_path = rf'../data/stats_sig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.csv'
    station_nc = xr.open_dataset(station_nc_path)
    station_csv = pd.read_csv(station_csv_path)
    station_stat = pd.read_csv(station_stats_path, index_col=0)
    ds_ls = [station_nc]
    stat_ls = [station_stat]

    input_dir_data = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/'
    input_dir_area = r'../data/mask/'
    input_dir_stat = rf'../data/stats_sig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/'
    for i, model in enumerate(DATA_LS_80):
        tempt_ds = xr.open_dataset(os.path.join(input_dir_data, f'grid_{model}.nc'))
        tempt_area = xr.open_dataset(os.path.join(input_dir_area, f'area_mask_{model}.nc'))
        tempt_stat = pd.read_csv(os.path.join(input_dir_stat, f'{model}.csv'), index_col=0)
        ds_ls.append(tempt_ds)
        stat_ls.append(tempt_stat)
        if i == 0:
            area_ls = [tempt_area['area'], tempt_area['area']]
        else:
            area_ls.append(tempt_area['area'])
    varname_ls = ['S_daily_mean', 'S_daily_trend']
    for varname in varname_ls:
        plot_mean_trend_each_data(ds_ls, area_ls, land_ds, stat_ls, station_csv, varname, gdf)
    
    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")
    
    return


if __name__ == "__main__":
    
    main()

