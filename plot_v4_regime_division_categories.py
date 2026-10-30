# Code for plotting regime division by category


import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.gridspec import GridSpec
from matplotlib.colors import to_rgba
import time
import os
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.visualization import add_fignum, get_alpha_label
from rainfall_ui.util.datainfo import CATEGORY_NAMES, CATEGORY_NAMES_FULL, REGIONS, CATEGORY_LS_80, CATEGORY_LS_50

args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr
CATEGORY_LS = CATEGORY_LS_80 if START_YEAR >= 1980 else CATEGORY_LS_50


# function to plot regime division by category
def plot_regime_division_category(ds_ls, area_ds, land_ds, scale, gdf):

    color_ls = ['#F5DAC7', '#E8B596', '#ABD5E3', '#83BCD7']
    ftsz = 10
    # load data
    regime_ds_ls = []
    regime_id_ls = [0, 1, 10, 11]
    # 11, ++, 10, +-, 1, -+, 0, --
    for ds in ds_ls:
        re_ds = ds[f'D_{scale}_trend']
        prcp_ds = ds['PRCP_ratio_trend']
        re_ds = xr.where(re_ds > 0, 1, re_ds)
        re_ds = xr.where(re_ds < 0, 0, re_ds)
        prcp_ds = xr.where(prcp_ds > 0, 1, prcp_ds)
        prcp_ds = xr.where(prcp_ds < 0, 0, prcp_ds)
        regime_ds = prcp_ds * 10 + re_ds
        regime_ds_ls.append(regime_ds)

    # plot distribution
    fig = plt.figure(figsize=(11, 10), dpi=300)
    grid = GridSpec(8, 4, figure=fig, left=0.05, bottom=0.021, right=0.99, top=0.98, wspace=0.1, hspace=0.5)
    ax_map_ls = [plt.subplot(grid[2*i:2*(i+1), 0:2]) for i in range(4)]
    ax_bar_ls = []
    for i in range(4):
        tempt_bar_ls = [plt.subplot(grid[j, k]) for j in range(2*i, 2*(i+1)) for k in range(2, 4)]
        ax_bar_ls.append(tempt_bar_ls)
    alpha = 1.0
    color_ls_rgba = [to_rgba(c, alpha=alpha) for c in color_ls]
    cmap = ListedColormap(color_ls_rgba)
    boundaries = [regime_id_ls[0] - 0.5] + [i + 0.5 for i in regime_id_ls]
    norm = BoundaryNorm(boundaries, len(regime_id_ls))
    for i in range(len(regime_ds_ls)):
        axname = ax_map_ls[i]
        var = regime_ds_ls[i]
        # add base map
        min_lon, max_lon, min_lat, max_lat = -180, 180, -60, 90
        gdf = gdf.cx[min_lon:max_lon, min_lat:max_lat]
        gdf.plot(ax=axname, color='dimgray', linewidth=0.5)
        # excluding the Antarctica
        var = var.sel(lat=slice(min_lat, max_lat))
        area_ds = area_ds.sel(lat=slice(min_lat, max_lat))
        land_ds = land_ds.sel(lat=slice(min_lat, max_lat))
        var = var.where(land_ds)
        im = var.plot(ax=axname, cmap=cmap, norm=norm, add_colorbar=False)
        axname.set_xlim(min_lon, max_lon)
        axname.set_ylim(min_lat, max_lat)
        axname.set_xticks([])
        axname.set_yticks([])
        axname.set_xlabel(None)
        axname.set_ylabel(None)
        axname.set_title('')
        if i == 0:
            model_name = 'Guages'
        else:
            model_name = CATEGORY_NAMES_FULL[i-1]
        fignum = get_alpha_label(i, with_parenthesis=False)
        add_fignum(axname, fignum, ftsz=ftsz+2)
        ticks_y = np.array([-60, -30, 0, 30, 60])
        axname.set_yticks(ticks_y)
        axname.set_yticklabels([])
        ticks_x = np.arange(-120, 120.05, 60)
        axname.set_xticks(ticks_x)
        axname.set_xticklabels([])

        # add left yticks
        labels_y = [f'{abs(tick)}\xb0{"N" if tick > 0 else "S" if tick < 0 else " "}' for tick in ticks_y]
        axname.set_yticklabels(labels_y, fontsize=ftsz)
        if i == 3:
            # add bottom xticks
            labels_x = [f'{abs(int(tick))}\xb0{"E" if tick > 0 else "W" if tick < 0 else " "}' for tick in ticks_x]
            axname.set_xticklabels(labels_x, fontsize=ftsz)

        # add bar of global statistics
        left = axname.get_position().x0 + 0.005
        bottom = axname.get_position().y0 + 0.03
        width = 0.25 * axname.get_position().width
        height = 0.25 * axname.get_position().height
        ax_stat = fig.add_axes([left, bottom, width, height])
        ds_mask = xr.where(np.isnan(var), np.nan, 1)
        total_area = ds_mask.weighted(area_ds).sum(skipna=True).item()
        glob_stat_ls = []
        for value in regime_id_ls:
            value_ds = ds_mask.where(var == value)
            value_area_pct = value_ds.weighted(area_ds).sum(skipna=True).item() / total_area
            glob_stat_ls.append(value_area_pct)
        x = np.arange(len(glob_stat_ls))
        y = np.array(glob_stat_ls) * 100
        ax_stat.bar(x, y, color=color_ls, width=0.6)
        y_text = y
        y_loc = y
        ax_stat.set_xticks([0, 1, 2, 3])
        ax_stat.set_xticklabels(['--', '-+', '+-', '++'], fontsize=ftsz)
        ax_stat.set_yticks([])
        ax_stat.set_ylabel('')
        ax_stat.set_xlabel('')
        # add text
        for j in range(len(y)):
            text = str(round(y_text[j])) + '%'
            ax_stat.text(j, y_loc[j], text, va='bottom', ha='center', fontsize=ftsz-1)
        # remove border
        ax_stat.spines['right'].set_visible(False)
        ax_stat.spines['top'].set_visible(False)
        ax_stat.spines['left'].set_visible(False)

        # cal regional statistics
        tempt_region_stats = {}
        for region, (min_lon_r, max_lon_r, min_lat_r, max_lat_r) in REGIONS.items():
            tempt_df = var.copy()
            tempt_df = tempt_df.sel(lat=slice(min_lat_r, max_lat_r), lon=slice(min_lon_r, max_lon_r))
            tempt_area = area_ds.copy()
            tempt_area = tempt_area.sel(lat=slice(min_lat_r, max_lat_r), lon=slice(min_lon_r, max_lon_r))
            ds_mask = xr.where(np.isnan(tempt_df), np.nan, 1)
            total_area = ds_mask.weighted(tempt_area).sum(skipna=True).item()
            stat_ls = []
            for value in regime_id_ls:
                value_ds = ds_mask.where(tempt_df == value)
                try:
                    value_area_pct = value_ds.weighted(tempt_area).sum(skipna=True).item() / total_area
                except:
                    value_area_pct = 0.0
                stat_ls.append(value_area_pct)
                tempt_region_stats[region] = stat_ls

        # save csv
        tempt_region_stats['global'] = glob_stat_ls
        df = pd.DataFrame(tempt_region_stats, index=['--', '-+', '+-', '++'])
        outpath = rf'../data/regime_division_stats/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/regime_division_stats_{model_name}_{scale}.csv'
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        df.to_csv(outpath, index=True)
        print(f'Saving {outpath}')

        # add bar of regional statistics
        for j, (region, (min_lon_r, max_lon_r, min_lat_r, max_lat_r)) in enumerate(REGIONS.items()):
            ax_bar = ax_bar_ls[i][j]
            stat_ls = tempt_region_stats[region]
            x = np.arange(len(stat_ls))
            y = np.array(stat_ls) * 100
            ax_bar.bar(x, y, color=color_ls, width=0.5)
            y_text = y
            y_loc = y
            ax_bar.set_xticks([0, 1, 2, 3])
            ax_bar.set_xticklabels(['--', '-+', '+-', '++'], fontsize=ftsz)
            ax_bar.set_yticks([])
            ax_bar.set_ylabel('')
            ax_bar.set_xlabel('')
            # add text
            for k in range(len(y)):
                text = str(round(y_text[k])) + '%'
                ax_bar.text(k, y_loc[k], text, va='bottom', ha='center', fontsize=ftsz)
            # remove border
            ax_bar.spines['right'].set_visible(False)
            ax_bar.spines['top'].set_visible(False)
            ax_bar.spines['left'].set_visible(False)
            if j in [0, 1]:
                ylim = ax_bar.get_ylim()
                ax_bar.set_ylim(ylim[0], 1.35 * (ylim[1] - ylim[0]))
                ax_bar.set_xticklabels([])
                pos = ax_bar.get_position()
                ax_bar.set_position([pos.x0, pos.y0-0.02, pos.width, pos.height+0.02])
            # add annotation, region name
            ax_bar.text(0.01, 0.96, region, va='top', ha='left', fontsize=ftsz, transform=ax_bar.transAxes)
            if j == 0:
                fig_num = get_alpha_label(i+4, with_parenthesis=False)
                add_fignum(ax_bar, fig_num, ftsz=ftsz+2)

    # colorbar
    cbar_ax = fig.add_axes([0.23, 0.793, 0.18, 0.01])
    cbar = fig.colorbar(im, cax=cbar_ax, orientation='horizontal')#, extend='both')
    cbar.set_ticks([0, 1, 6, 11])
    cbar.set_ticklabels(['--', '-+', '+-', '++'], fontsize=ftsz)
    cbar.ax.set_xticks([], minor=True)

    # save result
    outpath = rf'../fig_v4/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/regime_division_categories_{scale}.png'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=300)
    print(f'Saving {outpath}')
    plt.close()

    return

def main():

    t1 = time.time()
    shp = r'/data4/dataset/lucc_boundary_map/global_coastline_110m/global_coastline_110m.shp'
    gdf = gpd.read_file(shp)
    land_path = r'../data/mask/land_mask_ref.nc'
    land_ds = xr.open_dataset(land_path)['land']

    station_nc_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.nc'
    station_nc = xr.open_dataset(station_nc_path)
    ds_ls = [station_nc]

    input_path_area = r'../data/mask/area_mask_CRU_JRA.nc'
    area_ds = xr.open_dataset(input_path_area)['area']
    input_dir_data = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/'
    for model in CATEGORY_NAMES:
        tempt_ds = xr.open_dataset(os.path.join(input_dir_data, f'grid_{model}_ensembles.nc'))
        ds_ls.append(tempt_ds)

    for scale in ['daily']:#, 'monthly']:
        plot_regime_division_category(ds_ls, area_ds, land_ds, scale, gdf)
    
    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")
    
    return


if __name__ == "__main__":
    
    main()

