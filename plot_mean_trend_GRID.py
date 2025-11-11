# -*- coding: utf-8 -*-
import pandas as pd
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib import ticker
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from plot_mean_trend_s_d_r_isd import adjust_axis_label, add_fignum, significance_test


# function to plot distribution of grid-based dataset
def plot_distribution_GRID(fig, axname, ds, varname, fignum):
    # basic set
    mean_clr = [
        #        "#D6D6D6",
        #        "#EDE8E0",
        "#FFFFFF",
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
    vmin = np.percentile(var_1d, 1)
    vmax = np.percentile(var_1d, 99)
    vcenter = 0 if 'trend' in varname else (vmin + vmax) / 2
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    im = var.plot(ax=axname, cmap=cmap, norm=norm, add_colorbar=False)
    # colorbar
    ax_pos = axname.get_position()
    left_loc, bottom_loc = ax_pos.get_points()[0]
    right_loc, top_loc = ax_pos.get_points()[1]
    cbar_ax = fig.add_axes([left_loc+0.05, bottom_loc - 0.04, right_loc - left_loc-0.1, 0.01])
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
    variance = np.average((values - average)**2, weights=weights)
    
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
        new_varname = 'UI'
    elif 'D_' in varname:
        new_varname = 'RE'
    elif 'PRCP_ratio_' in varname:
        new_varname = 'R/Rmax'
    elif 'rain_day_' in varname:
        new_varname = 'rainy days'
    else:
        print(f'Current varname: {varname}, no matched variable!')
    return new_varname


# function to plot mean and trend of GRID-based dataset
def plot_mean_trend_GRID(ds_ls, isd, area_ls, varname, global_ls=None):
    new_varname = rename(varname)
    if 'trend' in varname:
        fig = plt.figure(figsize=(9, 12), dpi=300)
        grid = GridSpec(4, 3, figure=fig, left=0.07, bottom=0.07, right=0.91, top=0.97, wspace=0.1, hspace=0.5)
        ax1 = plt.subplot(grid[0, 0:3])
        ax_ls1 = [plt.subplot(grid[i + 1, 0:2]) for i in range(3)]
        ax_ls2 = [plt.subplot(grid[i + 1, 2]) for i in range(3)]
        fignum_ls1 = [f'(b) Trend of {new_varname} (CRU-JRA)',
                      f'(c) Trend of {new_varname} (ERA5-Land)',
                      f'(d) Trend of {new_varname} (CMIP6 ensembles)']
        fignum_ls2 = ['(e) CRU-JRA vs. ISD',
                      '(f) ERA5-Land vs. ISD',
                      '(g) CMIP6 ensembles vs. ISD']
        outname = varname.replace('_trend', '')
        outname = f'trend_{outname}'
    else:
        fig = plt.figure(figsize=(9, 9), dpi=300)
        grid = GridSpec(3, 3, figure=fig, left=0.06, bottom=0.09, right=0.91, top=0.97, wspace=0.1, hspace=0.5)
        ax_ls1 = [plt.subplot(grid[i, 0:2]) for i in range(3)]
        ax_ls2 = [plt.subplot(grid[i, 2]) for i in range(3)]
        fignum_ls1 = [f'(a) Mean of {new_varname} (CRU-JRA)',
                      f'(b) Mean of {new_varname} (ERA5-Land)',
                      f'(c) Mean of {new_varname} (CMIP6 ensembles)']
        fignum_ls2 = ['(d) CRU-JRA vs. ISD',
                      '(e) ERA5-Land vs. ISD',
                      '(f) CMIP6 ensembles vs. ISD']
        outname = varname.replace('_mean', '')
        outname = f'mean_{outname}'

    for i in range(3):
        # plot distribution
        plot_distribution_GRID(fig, ax_ls1[i], ds_ls[i], varname, fignum_ls1[i])
        # plot scatter
        plot_scatter(ax_ls2[i], isd, ds_ls[i], area_ls[i], varname, fignum_ls2[i])

    # if trend, plot trend at global scale

    # save result
    outpath = rf'../fig/{outname}_grid.png'
    plt.savefig(outpath, dpi=300)
    print(f'Saving {outpath}')

    return


def main():
    # load data
    isd_path = r'../data/mean_trend/mean_trend_station_isd.csv'
    isd = pd.read_csv(isd_path)
    gridname_ls = ['CRU_JRA', 'ERA5_Land', 'CMIP6_ensembles']
    gridpath_ls = [rf'../data/mean_trend/mean_trend_grid_{gridname}.nc' for gridname in gridname_ls]
    ds_ls = [xr.open_dataset(gridpath) for gridpath in gridpath_ls]
    areapath_ls = [rf'../data/mask/area_mask_{gridname}.nc' for gridname in gridname_ls[:2]]
    area_ls = [xr.open_dataset(areapath) for areapath in areapath_ls]
    area_ls = [area_ls[0], area_ls[1], area_ls[0]]
    varnames = ['S', 'D', 'PRCP_ratio', 'rain_day', 'rain_day_0p1']
    varname_ls = []
    for i, varname in enumerate(varnames):
            for idx in ['mean', 'trend']:
                for period in ['', '_post_2000']:
                    if i <= 1:
                        for scale in ['daily', 'monthly']:
                            tempt = f'{varname}_{scale}_{idx}{period}'
                            varname_ls.append(tempt)
                    else:
                        tempt = f'{varname}_{idx}{period}'
                        varname_ls.append(tempt)

    plot_mean_trend_GRID(ds_ls, isd, area_ls, 'S_daily_trend', global_ls=None)

    return


if __name__ == "__main__":
    main()