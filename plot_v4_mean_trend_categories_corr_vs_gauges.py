# Code for plotting mean and trend by category, vs. gauges


import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker
import time
import os
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.visualization import add_fignum, rename, get_alpha_label, format_tick, cool
from rainfall_ui.util.datainfo import CATEGORY_NAMES, CATEGORY_LS_80, CATEGORY_LS_50

args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr
CATEGORY_LS = CATEGORY_LS_80 if START_YEAR >= 1980 else CATEGORY_LS_50


# function to plot mean and trend by category
def plot_mean_trend_category_vs_gauges(ds_ls, varname):
    ftsz = 10
    varname_lab = rename(varname)
    varname_mean = f'{varname}_mean'
    varname_trend = f'{varname}_trend'
    clr = cool[5]

    # load data
    if 'rain_day' in varname:
        trend_ds_ls = [ds[varname_trend] for ds in ds_ls]
        lab_mean = f'mean of {varname_lab} (day)'
        lab_trend = f'trend of {varname_lab} (day yr$^-$$^1$)'
    elif 'STD_' in varname:
        trend_ds_ls = [ds[varname_trend] * 10 for ds in ds_ls]
        lab_mean = f'mean of {varname_lab} (mm)'
        lab_trend = f'trend of {varname_lab} (mm decade$^-$$^1$)'
    else:
        trend_ds_ls = [ds[varname_trend] * 1000 for ds in ds_ls]
        if varname_lab == 'R/Rmax':
            lab_mean = 'Multi-year mean of $R$/$R$$_{max}$'
            lab_trend = 'Trend of $R$/$R$$_{max}$ (kyr$^-$$^1$)'
        else:
            lab_mean = f'Multi-year mean of {varname_lab}'
            lab_trend = f'Trend of {varname_lab} (kyr$^-$$^1$)'
    mean_ds_ls = [ds[varname_mean] for ds in ds_ls]
    new_ds_ls = [mean_ds_ls, trend_ds_ls]
    label_ls = [lab_mean, lab_trend]

    # plot distribution
    fig, axes = plt.subplots(3, 2, figsize=(8, 11), dpi=300)
    axes = axes.flatten()
    plt.subplots_adjust(
        left=0.08,
        right=0.99,
        top=0.99,
        bottom=0.04,
        hspace=0.15,
        wspace=0.2
    )
    axes_mean_ls = [axes[0], axes[2], axes[4]]
    axes_trend_ls = [axes[1], axes[3], axes[5]]
    axes_ls = [axes_mean_ls, axes_trend_ls]

    for i in range(2):
        axes_sub = axes_ls[i]
        sub_ds_ls = new_ds_ls[i]
        lab = label_ls[i]
        for j in range(1, len(sub_ds_ls)):
            axname = axes_sub[j-1]
            var_ds = sub_ds_ls[j]
            # excluding the Antarctica
            var_ds = var_ds.sel(lat=slice(-60, 90))

            # Plot scatter between gauges and grids
            # load data
            gauges = sub_ds_ls[0].sel(lat=slice(-60, 90))
            grids = xr.where(np.isnan(gauges), np.nan, var_ds)
            gauges_flat = gauges.values.flatten()
            grids_flat = grids.values.flatten()
            if varname in ['S_daily', 'PRCP_ratio']:
                valid_mask = ~np.isnan(gauges_flat) & ~np.isnan(grids_flat)
            elif varname == 'S_monthly':
                valid_mask = ~np.isnan(gauges_flat) & ~np.isnan(grids_flat)
            else:
                valid_mask = ~np.isnan(gauges_flat) & ~np.isnan(grids_flat)
            gauges_valid = gauges_flat[valid_mask]
            grids_valid = grids_flat[valid_mask]
            # plot scatter
            axname.scatter(gauges_valid, grids_valid, s=20, alpha=0.5, edgecolors='none', facecolor=clr)
            corr = np.corrcoef(gauges_valid, grids_valid)[0, 1]
            bias = np.mean(grids_valid - gauges_valid)
            if abs(bias) < 0.009:
                stats_text = f'n = {len(gauges_valid)}\nr = {corr:.2f}\nbias = {bias:.3f}'
            else:
                stats_text = f'n = {len(gauges_valid)}\nr = {corr:.2f}\nbias = {bias:.2f}'
            axname.text(0.7, 0.02, stats_text, transform=axname.transAxes, va='bottom', ha='left', fontsize=ftsz, color=clr)
            if varname == 'S_daily':
                if i == 0:
                    axname.set_xlim(-0.05, 0.5)
                    axname.set_ylim(-0.05, 0.6)
                else:
                    axname.set_xlim(-5, 5)
            elif varname == 'PRCP_ratio':
                if i == 0:
                    axname.set_xlim(-0.05, 0.3)
                    axname.set_ylim(-0.05, 0.5)
                else:
                    axname.set_xlim(-3, 3)
            axname.xaxis.set_major_locator(ticker.MaxNLocator(nbins=4, prune='both'))
            axname.yaxis.set_major_locator(ticker.MaxNLocator(nbins=4, prune='both'))
            xticks = axname.get_xticks()
            yticks = axname.get_yticks()
            decal = 1
            xticks_lab = [format_tick(tick, decal) for tick in xticks]
            yticks_lab = [format_tick(tick, decal) for tick in yticks]
            axname.set_xticks(xticks)
            axname.set_yticks(yticks)
            axname.set_xticklabels(xticks_lab, fontsize=ftsz)
            axname.set_yticklabels(yticks_lab, fontsize=ftsz)
            axname.set_xlabel(f'Guages {lab}', fontsize=ftsz)
            axname.set_ylabel(f'Gridded {lab}', fontsize=ftsz)
            fignum = get_alpha_label(i*3+j-1, with_parenthesis=False)
            add_fignum(axname, fignum, xoffset=0.02, yoffset=-0.07, ftsz=ftsz+2)
    
    # save result
    outpath = rf'../fig_v4/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{varname}_mean_trend_categories_vs_gauges.png'
    plt.savefig(outpath, dpi=300)
    print(f'Saving {outpath}')
    plt.close()

    return

def main():

    t1 = time.time()

    station_nc_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.nc'
    station_nc = xr.open_dataset(station_nc_path)
    ds_ls = [station_nc]

    input_dir_data = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/'
    for model in CATEGORY_NAMES:
        tempt_ds = xr.open_dataset(os.path.join(input_dir_data, f'grid_{model}_ensembles.nc'))
        ds_ls.append(tempt_ds)

    if START_YEAR == 1980:
        varnames = ['S_daily', 'PRCP_ratio', 'D_daily']#, 'S_monthly']#, 'D_monthly', 'rain_day']#, 'STD_daily_orig', 'STD_daily_detr']
    else:
        varnames = ['S_daily']
    for varname in varnames:
        plot_mean_trend_category_vs_gauges(ds_ls, varname)
    
    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")
    
    return


if __name__ == "__main__":
    
    main()

