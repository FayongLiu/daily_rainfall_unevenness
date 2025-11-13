# -*- coding: utf-8 -*-
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib import ticker
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import time
import seaborn as sns
from scipy.stats import linregress
from plot_mean_trend_isd import adjust_axis_label, add_fignum, significance_test
from pre_GRID_cal_maximum_annual_prcp import model_ls
from pre_isd_select_valid_station import START_YEAR, END_YEAR, TH_YEAR


# function to plot distribution of grid-based dataset
def plot_distribution_GRID(fig, axname, ds, varname, fignum, cbar_prop):
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
            var = ds[varname]
            unit = 'yr$^{-1}$'
        else:
            var = ds[varname] * 1000
            unit = 'kyr$^{-1}$'
        p_name = varname.replace('trend', 'p_value')
        p_mask = ds[p_name]
        cmap = cmap_trend
    else:
        var = ds[varname]
        cmap = cmap_mean
    # plot distribution
    var_1d = var.values.flatten()
    var_1d = var_1d[~np.isnan(var_1d)]
    vmin = np.percentile(var_1d, 5)
    vmax = np.percentile(var_1d, 95)
    vcenter = 0 if 'trend' in varname else (vmin + vmax) / 2
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    im = var.plot(ax=axname, cmap=cmap, norm=norm, add_colorbar=False)
    # colorbar
    ax_pos = axname.get_position()
    left_loc, bottom_loc = ax_pos.get_points()[0]
    right_loc, top_loc = ax_pos.get_points()[1]
    cbar_ax = fig.add_axes([left_loc + 0.05, bottom_loc - cbar_prop[0], right_loc - left_loc - 0.1, cbar_prop[1]])
    cbar = fig.colorbar(im, cax=cbar_ax, orientation='horizontal', extend='both')
    cbar.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5))

    if 'trend' in varname:
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
        # add unit
        cbar.ax.text(1.06, 0.5, unit, va='center', ha='left', color='k', transform=cbar_ax.transAxes)
    axname = adjust_axis_label(axname)
    add_fignum(axname, fignum)

    return


# function to  calculate weighted std
def weighted_std(values, weights):
    average = np.average(values, weights=weights)
    variance = np.average((values - average) ** 2, weights=weights)

    return np.sqrt(variance)


# function to plot scatter between isd and grid-based data
def plot_scatter(axname, isd, grid, area, varname, fignum):
    isd_values = isd[varname].values
    grid_values = []
    area_values = []
    # find matched grid pairs
    for _, row in isd.iterrows():
        grid_value = grid[varname].sel(lon=row['lon'], lat=row['lat'], method='nearest')
        grid_values.append(grid_value.values)
        area_value = area['area'].sel(lon=row['lon'], lat=row['lat'], method='nearest')
        area_values.append(area_value.values)
    grid_values = np.array(grid_values)
    area_values = np.array(area_values)
    # mask nan values
    valid_mask = (~np.isnan(isd_values)) & (~np.isnan(grid_values)) & (~np.isnan(area_values))
    isd_valid = isd_values[valid_mask]
    grid_valid = grid_values[valid_mask]
    area_valid = area_values[valid_mask]
    # plot scatter
    if 'trend' in varname:
        if ('D_' in varname) or ('rain_day' in varname):
            unit = ' (yr$^{-1}$)'
        else:
            isd_valid = isd_valid * 1000
            grid_valid = grid_valid * 1000
            unit = ' (kyr$^{-1}$)'
    else:
        unit = ''
    axname.scatter(isd_valid, grid_valid, facecolor="#EAB080", s=10, alpha=0.8)
    axname.set_xlabel(f'ISD{unit}')
    dataname = fignum.split(' ')[1]
    if dataname == 'CMIP6':
        dataname = 'CMIP6 ensembles'
    axname.set_ylabel(f'{dataname}{unit}')
    axname.yaxis.set_label_position('right')
    axname.yaxis.tick_right()
    axname.yaxis.set_major_locator(ticker.MaxNLocator(nbins=4))
    axname.xaxis.set_major_locator(ticker.MaxNLocator(nbins=4))
    # calculate the Pearson coefficient
    r_value = np.corrcoef(isd_valid, grid_valid)[0, 1]
    # calculate mean and std
    mean = np.average(grid_valid, weights=area_valid)
    std = weighted_std(grid_valid, area_valid)
    # add text
    text = f'{dataname}: {mean:.2f} \u00b1 {std:.2f}\nn = {len(isd_valid)}, r = {r_value:.2f}'
    xlim = axname.get_xlim()
    ylim = axname.get_ylim()
    xloc = xlim[0] + 0.01 * (xlim[1] - xlim[0])
    yloc = ylim[1] - 0.05 * (ylim[1] - ylim[0])
    axname.text(xloc, yloc, text, va='top', ha='left')

    # significant test
    p_value_pair = significance_test(isd_valid, grid_valid)
    if p_value_pair <= 0.05:
        fignum = f'{fignum} *'
    add_fignum(axname, fignum)

    return


# function to rename varname
def rename(varname):
    if 'S_' in varname:
        title_varname = 'UI'
    elif 'D_' in varname:
        title_varname = 'RE'
    elif 'PRCP_ratio_' in varname:
        title_varname = 'R/Rmax'
    elif 'rain_day_' in varname:
        title_varname = 'rainy days'
    else:
        print(f'Current varname: {varname}, no matched variable!')
    return title_varname


# function to plot mean and trend of GRID-based dataset
def plot_mean_trend_GRID(ds_ls, isd, area_ls, varname, global_ls=None, is_global_average=1):
    title_varname = rename(varname)
    if 'trend' in varname:
        fig = plt.figure(figsize=(9, 12), dpi=300)
        grid = GridSpec(4, 3, figure=fig, left=0.08, bottom=0.07, right=0.91, top=0.98, wspace=0.1, hspace=0.5)
        ax_global = plt.subplot(grid[0, 0:3])
        ax_ls1 = [plt.subplot(grid[i + 1, 0:2]) for i in range(3)]
        ax_ls2 = [plt.subplot(grid[i + 1, 2]) for i in range(3)]
        fignum_ls1 = [f'(b) Trend of {title_varname} (CRU-JRA)',
                      f'(c) Trend of {title_varname} (ERA5-Land)',
                      f'(d) Trend of {title_varname} (CMIP6 ensembles)']
        fignum_ls2 = ['(e) CRU-JRA vs. ISD',
                      '(f) ERA5-Land vs. ISD',
                      '(g) CMIP6 ensembles vs. ISD']
        outname = varname.replace('_trend', '')
        outname = f'trend_{outname}'
        cbar_prop = [0.04, 0.01]
    else:
        fig = plt.figure(figsize=(9, 9), dpi=300)
        grid = GridSpec(3, 3, figure=fig, left=0.06, bottom=0.08, right=0.91, top=0.97, wspace=0.1, hspace=0.5)
        ax_ls1 = [plt.subplot(grid[i, 0:2]) for i in range(3)]
        ax_ls2 = [plt.subplot(grid[i, 2]) for i in range(3)]
        fignum_ls1 = [f'(a) Mean of {title_varname} (CRU-JRA)',
                      f'(b) Mean of {title_varname} (ERA5-Land)',
                      f'(c) Mean of {title_varname} (CMIP6 ensembles)']
        fignum_ls2 = ['(d) CRU-JRA vs. ISD',
                      '(e) ERA5-Land vs. ISD',
                      '(f) CMIP6 ensembles vs. ISD']
        outname = varname.replace('_mean', '')
        outname = f'mean_{outname}'
        cbar_prop = [0.05, 0.012]

    for i in range(3):
        # plot distribution
        plot_distribution_GRID(fig, ax_ls1[i], ds_ls[i], varname, fignum_ls1[i], cbar_prop)
        # plot scatter
        plot_scatter(ax_ls2[i], isd, ds_ls[i], area_ls[i], varname, fignum_ls2[i])

    # if trend, plot trend at global scale
    if global_ls is not None:
        clr_ls = ['#EAB080', '#7C9D97', '#9CB0C3', '#C9C9C9']
        dataname_ls = ['ISD', 'CRU-JRA', 'ERA5-Land', 'CMIP6 ensembles']
        df_varname = varname.replace('_trend', '')
        if not is_global_average:
            df_varname = f'{df_varname}_station'
        slope_ls = []
        p_ls = []
        for i, df in enumerate(global_ls):
            axname = ax_global
            if i <= 3:
                if i == 0:
                    df_varname = varname.replace('_trend', '')
                axname.plot(df['year'].values, df[df_varname].values, linestyle='-', linewidth=1.5, color=clr_ls[i], alpha=0.8)
                sns.regplot(x=df['year'].values, y=df[df_varname].values, ci=95, marker='o', color=clr_ls[i], ax=axname)
                slope, _, _, p_value, _ = linregress(df['year'].values, df[df_varname].values)
                slope_ls.append(slope)
                p_ls.append(p_value)
            else:
                axname.plot(df['year'].values, df[df_varname].values, linestyle='--', linewidth=1.5, color=clr_ls[-1], alpha=0.5)
        axname.set_ylabel('Global averaged UI')
        axname.set_xlabel('')
        axname.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5))
        # adjust location
        pos = axname.get_position()
        offset = 0.03
        new_pos = [pos.x0, pos.y0 - offset, pos.width, pos.height + offset]
        axname.set_position(new_pos)
        # add slope and p value
        xlim = axname.get_xlim()
        ylim = axname.get_ylim()
        xloc = xlim[0] + 0.55 * (xlim[1] - xlim[0])
        for i in range(4):
            yloc = ylim[0] + 0.12 * (ylim[1] - ylim[0]) + 0.08 * i * (ylim[1] - ylim[0])
            txt = f'{dataname_ls[i]}: slope = {slope_ls[i]*1000:.2f} kyr$^-$$^1$, $p$ = {p_ls[i]:.2f}'
            axname.text(xloc, yloc, txt, color=clr_ls[i], va='bottom', ha='left')
        add_fignum(axname, '(a) Changes in global averaged UI')

    # save result
    averaged_name = '' if is_global_average else '_averaged_by_stations'
    outpath = rf'../fig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{outname}_grid{averaged_name}.png'
    plt.savefig(outpath, dpi=300)
    print(f'Saving {outpath}')
    plt.close()

    return


def main():
    # load data
    # at each station or grid
    isd_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station_isd.csv'
    isd = pd.read_csv(isd_path)
    gridname_ls = ['CRU_JRA', 'ERA5_Land', 'CMIP6_ensembles']
    gridpath_ls = [rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/grid_{gridname}.nc' for gridname in gridname_ls]
    ds_ls = [xr.open_dataset(gridpath) for gridpath in gridpath_ls]
    areapath_ls = [rf'../data/mask/area_mask_{gridname}.nc' for gridname in gridname_ls[:2]]
    area_ls = [xr.open_dataset(areapath) for areapath in areapath_ls]
    area_ls = [area_ls[0], area_ls[1], area_ls[0]]
    # at global scael
    globalname_ls = ['isd', 'CRU_JRA', 'ERA5_Land', 'CMIP6_ensembles'] + model_ls
    globalpath_ls = [rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/global_{globalname}.csv' for globalname in globalname_ls]
    global_ls = [pd.read_csv(globalpath) for globalpath in globalpath_ls]

    varnames = ['S', 'D', 'PRCP_ratio', 'rain_day', 'rain_day_0p1']
    varname_ls = []
    # for i, varname in enumerate(varnames):
    #     for idx in ['mean', 'trend']:
    #         for period in ['', '_post_2000']:
    #             if i <= 1:
    #                 for scale in ['daily', 'monthly']:
    #                     tempt = f'{varname}_{scale}_{idx}{period}'
    #                     varname_ls.append(tempt)
    #             else:
    #                 tempt = f'{varname}_{idx}{period}'
    #                 varname_ls.append(tempt)
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
        if 'trend' in varname:
            for is_global_average in range(2):
                plot_mean_trend_GRID(ds_ls, isd, area_ls, varname, global_ls, is_global_average)
        else:
            plot_mean_trend_GRID(ds_ls, isd, area_ls, varname)

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