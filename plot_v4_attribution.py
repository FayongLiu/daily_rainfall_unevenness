# Code for plotting attribution of UI to Re and R/Rmax


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
from rainfall_ui.util.visualization import add_fignum, cmap_cool, cmap_coolwarm, cool
from rainfall_ui.util.datainfo import REGIONS, CATEGORY_NAMES

args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr


# function to plot mean and trend by category
def plot_attribution_station(in_ds, area_ds, land_ds, scale, data_name, gdf, station_df=None):

    cmap_rel = cmap_cool
    cmap_abs = cmap_coolwarm
    clr = cool[4]
    ftsz = 10

    ds_ls = [[in_ds[f'ConRRmax_rel_{scale}'], in_ds[f'ConRE_rel_{scale}'], in_ds[f'ConInter_rel_{scale}']],
             [in_ds[f'ConRRmax_abs_{scale}'], in_ds[f'ConRE_abs_{scale}'], in_ds[f'ConInter_abs_{scale}']]
             ]
    if station_df is not None:
        df_ls = [[station_df[f'ConRRmax_rel_{scale}'], station_df[f'ConRE_rel_{scale}'], station_df[f'ConInter_rel_{scale}']],
                 [station_df[f'ConRRmax_abs_{scale}'], station_df[f'ConRE_abs_{scale}'], station_df[f'ConInter_abs_{scale}']]
                ]
    # fignum_ls = [['(a) Relative contribution of $R$/$R$$_{max}$', 
    #               '(b) Relative contribution of RE', 
    #               '(c) Relative contribution of interaction'],
    #              ['(d) Absolute contribution of $R$/$R$$_{max}$', 
    #               '(e) Absolute contribution of RE', 
    #               '(f) Absolute contribution of interaction']
    #              ]
    fignum_ls1 = [['a', 'c', 'e'], ['g', 'i', 'k']]
    fignum_ls2 = [['b', 'd', 'f'], ['h', 'j', 'l']]
    fig, axes = plt.subplots(3, 2, figsize=(10, 10.5), dpi=300)
    plt.subplots_adjust(
        left=0.05,
        right=0.99,
        top=0.99,
        bottom=0.185,
        hspace=0.48,
        wspace=0.04
    )

    for i in range(2):
        sub_ds_ls = ds_ls[i]
        sub_fignum_ls1 = fignum_ls1[i]
        sub_fignum_ls2 = fignum_ls2[i]
        if station_df is not None:
            sub_df_ls = df_ls[i]
        if i == 1:
            sub_ds_ls = [ds * 1000 for ds in sub_ds_ls]
            if station_df is not None:
                sub_df_ls = [df * 1000 for df in sub_df_ls]
            label = 'kyr$^-$$^1$'
            cmap = cmap_abs
        else:
            sub_ds_ls = [ds * 100 for ds in sub_ds_ls]
            if station_df is not None:
                sub_df_ls = [df * 100 for df in sub_df_ls]
            label = '%'
            cmap = cmap_rel

        var_1d = np.concatenate([var.values.flatten() for var in sub_ds_ls])
        var_1d = var_1d[~np.isnan(var_1d)]
        vmin = np.percentile(var_1d, 5)
        vmax = np.percentile(var_1d, 95)
        vcenter = 0 if i == 1 else (vmin + vmax) / 2
        norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
        for j in range(len(sub_ds_ls)):
            axname = axes[j, i]
            var = sub_ds_ls[j]
            if station_df is not None:
                var_df = sub_df_ls[j]

            # add base map
            min_lon, max_lon, min_lat, max_lat = -180, 180, -60, 90
            gdf = gdf.cx[min_lon:max_lon, min_lat:max_lat]
            gdf.plot(ax=axname, color='dimgray', linewidth=0.5)
            # excluding the Antarctica
            var = var.sel(lat=slice(min_lat, max_lat))
            area_ds = area_ds.sel(lat=slice(min_lat, max_lat))
            # cal mean and std
            if station_df is not None:
                global_mean = var_df.mean().item()
                global_std = var_df.std().item()
            else:
                global_mean = var.weighted(area_ds).mean().item()
                global_std = var.weighted(area_ds).std().item()
            # not show small islands
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
            
            fignum = f'{sub_fignum_ls1[j]}'
            add_fignum(axname, fignum, xoffset=0.01, yoffset=-0.09, ftsz=ftsz+2)
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
            if j == 2:
                # add bottom xticks
                labels_x = [f'{abs(int(tick))}\xb0{"E" if tick > 0 else "W" if tick < 0 else " "}' for tick in ticks_x]
                axname.set_xticklabels(labels_x, fontsize=ftsz)
        
            # add box
            left = axname.get_position().x0 + 0.055
            if j == 2:
                bottom = axname.get_position().y0 - 0.09
            else:
                bottom = axname.get_position().y0 - 0.07
            width = 0.76 * axname.get_position().width
            height = 0.3 * axname.get_position().height
            ax_box = fig.add_axes([left, bottom, width, height])
            for spine in ax_box.spines.values():
                spine.set_linewidth(0.8)
            varname = var.name
            if station_df is not None:
                gauge_df = pd.DataFrame(var_df.copy(), columns=[varname])
            else:
                var_valid = var.values.flatten()
                var_valid = var_valid[~np.isnan(var_valid)]
                gauge_df = pd.DataFrame(var_valid, columns=[varname])
                mean_ls = [global_mean]
                std_ls = [global_std]
            gauge_df['Region'] = 'Globe'
            df_long = [gauge_df]
            for region, (min_lon_r, max_lon_r, min_lat_r, max_lat_r) in REGIONS.items():
                if station_df is not None:
                    tempt_df = pd.DataFrame(var_df.copy(), columns=[varname])
                    tempt_df['lon'] = station_df['lon']
                    tempt_df['lat'] = station_df['lat']
                    tempt_df['Region'] = region
                    tempt_df = tempt_df[
                        (tempt_df['lon'] >= min_lon_r) & 
                        (tempt_df['lon'] <= max_lon_r) & 
                        (tempt_df['lat'] >= min_lat_r) & 
                        (tempt_df['lat'] <= max_lat_r)
                    ].loc[:, [varname, 'Region']]
                else:
                    tempt_ds = var.sel(lon=slice(min_lon_r, max_lon_r), lat=slice(min_lat_r, max_lat_r))
                    tempt_area = area_ds.sel(lon=slice(min_lon_r, max_lon_r), lat=slice(min_lat_r, max_lat_r))
                    region_mean = tempt_ds.weighted(tempt_area).mean().item()
                    region_std = tempt_ds.weighted(tempt_area).std().item()
                    mean_ls.append(region_mean)
                    std_ls.append(region_std)
                    tempt_valid = tempt_ds.values.flatten()
                    tempt_valid = tempt_valid[~np.isnan(tempt_valid)]
                    tempt_df = pd.DataFrame(tempt_valid, columns=[varname])
                    tempt_df['Region'] = region
                df_long.append(tempt_df)
            df_long = pd.concat(df_long, axis=0).reset_index(drop=True)
            if station_df is not None:
                mean_df = df_long.groupby('Region').mean()
                std_df = df_long.groupby('Region').std()
            else:
                mean_df = pd.DataFrame({varname: mean_ls})
                std_df = pd.DataFrame({varname: std_ls})
                mean_df.index = ['Globe'] + list(REGIONS.keys())
                std_df.index = ['Globe'] + list(REGIONS.keys())

            box_alp= 1.0
            box_lw = 0.8
            sns.boxplot(
                data=df_long,
                x='Region',
                y=varname,
                color=clr,
                fill=None,
                ax=ax_box,
                showmeans=True,
                showfliers=False,
                width=0.4,
                boxprops={
                    'alpha': box_alp,
                    'color': clr,
                    'linewidth': box_lw
                },
                medianprops={
                    'color': clr,
                    'linewidth': box_lw,
                    'alpha': box_alp
                },
                whiskerprops={
                    'color': clr,
                    'linewidth': box_lw,
                    'alpha': box_alp
                },
                capprops={
                    'color': clr,
                    'linewidth': box_lw,
                    'alpha': box_alp
                },
                meanprops={
                    'marker': 'o',
                    'markerfacecolor': 'none',
                    'markeredgecolor': clr,
                    'markeredgewidth': 1.0,
                    'markersize': 3
                }
            )
            ax_box.set_xlabel('')
            ax_box.set_ylabel(label, fontsize=ftsz-1)
            ax_box.yaxis.set_major_locator(ticker.MaxNLocator(nbins=3, prune='both'))
            ax_box.set_xticks(ax_box.get_xticks())
            ax_box.set_yticks(ax_box.get_yticks())
            ax_box.set_xticklabels(ax_box.get_xticklabels(), fontsize=ftsz-1)
            ax_box.set_yticklabels(ax_box.get_yticklabels(), fontsize=ftsz-0.5)
            # add annotation
            ylim = ax_box.get_ylim()
            for k, region in enumerate(['Globe'] + list(REGIONS.keys())):
                if i == 1:
                    if abs(mean_df.loc[region].values[0]) < 0.009:
                        text = f'{mean_df.loc[region].values[0]:.3f}\u00b1{std_df.loc[region].values[0]:.1f}'
                    elif abs(mean_df.loc[region].values[0]) < 0.09:
                        text = f'{mean_df.loc[region].values[0]:.2f}\u00b1{std_df.loc[region].values[0]:.1f}'
                    else:
                        text = f'{mean_df.loc[region].values[0]:.1f}\u00b1{std_df.loc[region].values[0]:.1f}'
                else:
                    text = f'{mean_df.loc[region].values[0]:.0f}\u00b1{std_df.loc[region].values[0]:.0f}'
                ax_box.text(
                    k, ylim[0]-0.6*(ylim[1]-ylim[0]), text, va='bottom', ha='center', fontsize=ftsz-0.5, color=clr
                )
            fignum = f'{sub_fignum_ls2[j]}'
            add_fignum(ax_box, fignum, xoffset=0.01, yoffset=-0.3, ftsz=ftsz+2)

        # colorbar
        position = axname.get_position()
        left = position.x0
        width = position.width
        height = 0.015
        bottom = position.y0 - 0.145
        cbar_ax = fig.add_axes([left, bottom, width, height])
        cbar = fig.colorbar(im, cax=cbar_ax, orientation='horizontal', extend='both')
        cbar.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=4, prune='both'))
        cbar.set_label(label, fontsize=ftsz)

    # save result
    outpath = rf'../fig_v4/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/attribution_{scale}_{data_name}.png'
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

    station_csv_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station_attribution.csv'
    station_df = pd.read_csv(station_csv_path)
    input_path_area = r'../data/mask/area_mask_CRU_JRA.nc'
    area_ds = xr.open_dataset(input_path_area)['area']
    if START_YEAR == 1980:
        data_names = ['station'] + CATEGORY_NAMES
    else:
        data_names = ['station']
    for data_name in data_names:
        if data_name == 'station':
            nc_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station_attribution.nc'
        else:
            nc_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/grid_{data_name}_ensembles_attribution.nc'
            station_df = None
        in_ds = xr.open_dataset(nc_path)
        for scale in ['daily']:#, 'monthly']:
            plot_attribution_station(in_ds, area_ds, land_ds, scale, data_name, gdf, station_df)
    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")
    
    return


if __name__ == "__main__":
    
    main()

