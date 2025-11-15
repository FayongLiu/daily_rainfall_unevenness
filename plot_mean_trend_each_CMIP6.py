# -*- coding: utf-8 -*-
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import time
import os
from plot_mean_trend_isd import add_fignum
from pre_GRID_cal_maximum_annual_prcp import model_ls
from pre_isd_select_valid_station import START_YEAR, END_YEAR, TH_YEAR
from plot_mean_trend_GRID import rename


# function to plot each CMIP6 model
def plot_cmip6(ds_ls, area_ds, station_ds, varname):
    lab_varname = rename(varname)
    # basic set
    mean_clr = [
        "#D6D6D6",
        "#EDE8E0",
        "#FFF8E6",
        "#FAEBD7",
        "#FFE4B5",
        "#F5D7A1",
        "#EAB080",
        "#DD7836"
    ]
    cmap_mean = LinearSegmentedColormap.from_list("white_yellow_orange", mean_clr, N=256)
    trend_clr = ["#455a64", "#FFFFFF", "#DD7836"]
    cmap_trend = LinearSegmentedColormap.from_list("blue2orange", trend_clr, N=256)

    # load data
    if 'trend' in varname:
        if ('D_' in varname) or ('rain_day' in varname):
            var_ls = [ds[varname] for ds in ds_ls]
            label = f'Trend of {lab_varname} (yr$^-$$^1$)'
        else:
            var_ls = [ds[varname] * 1000 for ds in ds_ls]
            label = f'Trend of {lab_varname} (kyr$^-$$^1$)'
        p_name = varname.replace('trend', 'p_value')
        p_mask_ls = [ds[p_name] for ds in ds_ls]
        cmap = cmap_trend
        outname = varname.replace('_trend', '')
        outname = f'trend_{outname}'
    else:
        var_ls = [ds[varname] for ds in ds_ls]
        label = f'Multi-year mean of {lab_varname}'
        cmap = cmap_mean
        outname = varname.replace('_mean', '')
        outname = f'mean_{outname}'

    # plot distribution
    fig, axes = plt.subplots(5, 5, figsize=(20, 12), dpi=300)
    axes = axes.flatten()
    plt.subplots_adjust(
        left=0.03,
        right=0.935,
        top=0.98,
        bottom=0.03,
        hspace=0.2,
        wspace=0.04
    )
    var_1d = np.concatenate([var.values.flatten() for var in var_ls])
    var_1d = var_1d[~np.isnan(var_1d)]
    vmin = np.percentile(var_1d, 5)
    vmax = np.percentile(var_1d, 95)
    vcenter = 0 if 'trend' in varname else (vmin + vmax) / 2
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    for i in range(len(ds_ls)):
        axname = axes[i]
        var = var_ls[i]
        im = var.plot(ax=axname, cmap=cmap, norm=norm, add_colorbar=False)
        if 'trend' in varname:
            p_mask = p_mask_ls[i]
            # add p_values
            da = xr.where((p_mask >= 0) & (p_mask < 0.05), 1, np.nan)
            da.plot.contourf(
                ax=axname,
                levels=[0.99, 1.01],
                hatches=[4 * '.', ''],
                colors='none',
                extend='neither',
                add_colorbar=False,
                add_labels=False,
                alpha=0.001
            )
        axname.set_xlim(-180.05, 180.05)
        axname.set_ylim(-61, 82)
        axname.set_xticks([])
        axname.set_yticks([])
        axname.set_xlabel(None)
        axname.set_ylabel(None)
        axname.set_title('')
        # cal mean and std
        var_station = var.where(station_ds)
        global_mean = var_station.weighted(area_ds).mean(skipna=True).item()
        global_std = var_station.weighted(area_ds).std(skipna=True).item()
        model_name = model_ls[i].split('_')[0]
        fignum = f'{model_name}, {global_mean:.2f} \u00b1 {global_std:.2f}'
        add_fignum(axname, fignum)
        if i in [0, 5, 10, 15, 20]:
            # add left yticks
            ticks_y = np.array([-60, -30, 0, 30, 60])
            labels_y = [f'{abs(tick)}\xb0{"N" if tick > 0 else "S" if tick < 0 else " "}' for tick in ticks_y]
            axname.set_yticks(ticks_y)
            axname.set_yticklabels(labels_y)
        if i in [20, 21, 22, 23, 24]:
            # add bottom xticks
            ticks_x = np.arange(-180, 180.001, 60)
            labels_x = [f'{abs(int(tick))}\xb0{"E" if tick > 0 else "W" if tick < 0 else " "}' for tick in ticks_x]
            labels_x[0], labels_x[-1] = ' ', ' '
            axname.set_xticks(ticks_x)
            axname.set_xticklabels(labels_x)
    # colorbar
    cbar_ax = fig.add_axes([0.945, 0.2, 0.015, 0.6])
    cbar = fig.colorbar(im, cax=cbar_ax, orientation='vertical', extend='both')
    cbar.ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=5))
    cbar.set_label(label, fontsize=12)

    # save result
    outpath = rf'../fig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{outname}_CMIP6_stations.png'
    plt.savefig(outpath, dpi=300)
    print(f'Saving {outpath}')
    plt.close()

    return

def main():
    cmip6_dir = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/'
    ds_ls = [xr.open_dataset(os.path.join(cmip6_dir, f'grid_{model}.nc')) for model in model_ls]
    area_path = rf'../data/mask/area_mask_CRU_JRA.nc'
    area_ds = xr.open_dataset(area_path)['area']
    station_path = rf'../data/mask/station_mask_{START_YEAR}_{END_YEAR}_gte{TH_YEAR}_CRU_JRA.nc'
    station_ds = xr.open_dataset(station_path)['station']
    varnames = ['S', 'D', 'PRCP_ratio', 'rain_day']
    varname_ls = []
    for i, varname in enumerate(varnames):
        for idx in ['mean', 'trend']:
            if i <= 1:
                for scale in ['daily', 'monthly']:
                    tempt = f'{varname}_{scale}_{idx}'
                    varname_ls.append(tempt)
            else:
                tempt = f'{varname}_{idx}'
                varname_ls.append(tempt)
    for varname in varname_ls:
        plot_cmip6(ds_ls, area_ds, station_ds, varname)

    return


if __name__ == "__main__":
    t1 = time.time()
    main()
    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")