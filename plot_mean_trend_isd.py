# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import matplotlib.lines as mlines
import matplotlib.ticker as ticker
from scipy.stats import linregress, shapiro, levene, ttest_ind, ttest_rel, mannwhitneyu, wilcoxon
import geopandas as gpd
import seaborn as sns
from pre_isd_select_valid_station import START_YEAR, END_YEAR, TH_YEAR


# function to adjust x-y tick lables
def adjust_axis_label(axname):
    axname.set_xlim(-180.05, 180.05)
    axname.set_ylim(-61, 82)
    ticks_x = np.arange(-180, 180.001, 60)
    labels_x = [f'{abs(int(tick))}\xb0{"E" if tick > 0 else "W" if tick < 0 else " "}' for tick in ticks_x]
    labels_x[0], labels_x[-1] = ' ', ' '
    axname.set_xticks(ticks_x)
    axname.set_xticklabels(labels_x)
    ticks_y = np.array([-60, -30, 0, 30, 60])
    labels_y = [f'{abs(tick)}\xb0{"N" if tick > 0 else "S" if tick < 0 else " "}' for tick in ticks_y]
    axname.set_yticks(ticks_y)
    axname.set_yticklabels(labels_y)
    axname.set_xlabel(None)
    axname.set_ylabel(None)
    axname.set_title('')

    return axname


# function set fig num
def add_fignum(axname, txt, ftsz=12):
    xlim = axname.get_xlim()
    ylim = axname.get_ylim()
    xpos = xlim[0]
    ypos = ylim[1]
    axname.text(xpos, ypos, txt, va='bottom', ha='left', fontweight='bold', fontsize=ftsz)

    return axname


# def a function to test the difference between urban and rural
def significance_test(data1, data2, alpha=0.05):
    # normality test, null hypothesis, correspond to normal distribution
    norm1 = shapiro(data1).pvalue >= alpha
    norm2 = shapiro(data2).pvalue >= alpha
    # sample num test
    if len(data1) == len(data2):
        is_paired = True
    else:
        is_paired = False
    # if normal distribution, t test, if pair, paired t-test else independent samples t-test or Welch's t-test
    # else, if pair, Wilcoxon Signed-Rank test else Mann-Whitney u test
    # null hypothesis, no significant differences
    # default, two-tailed test
    if norm1 and norm2:
        if is_paired:
            # Paired samples t-test
            _, p_value = ttest_rel(data1, data2)
        else:
            # homogeneity of variance test, null hypothesis, homogeneity of variance
            equal_var = levene(data1, data2).pvalue >= alpha
            # if homogeneity of variance, independent samples t test, else, Welch's t test
            _, p_value = ttest_ind(data1, data2, equal_var=equal_var)
    else:
        if is_paired:
            # If data is not normally distributed and is paired, use Wilcoxon Signed-Rank test
            _, p_value = wilcoxon(data1, data2)
        else:
            # else use Mann-Whitney U test
            _, p_value = mannwhitneyu(data1, data2)

    return p_value


# function to plot distribution of isd
def plot_distribution_isd(fig, axname, df, gdf, varname, fignum, cbar_prop):
    """
    cbar_prop, [bottom off (float), height(float)]
    """
    # basic set
    mean_clr = [
        "#D6D6D6",
        "#EDE8E0",
        # "#FFFFFF",
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
    sz = 7
    alp = 0.7

    # load data
    lon = df['lon']
    lat = df['lat']

    if 'trend' in varname:
        if ('D_' in varname) or ('rain_day' in varname):
            var = df[varname]
            unit = 'yr$^{-1}$'
        else:
            var = df[varname] * 1000
            unit = 'kyr$^{-1}$'
        p_name = varname.replace('trend', 'p_value')
        p_value = df[p_name]
        cmap = cmap_trend
        edgecolors = ['dimgray' if p <= 0.05 else 'none' for p in p_value]
        linewidth = [0.3 if p <= 0.05 else 0 for p in p_value]
    else:
        var = df[varname]
        cmap = cmap_mean
        linewidth = 0
        edgecolors = 'none'
    # add base map
    min_lon, max_lon = -180, 180
    min_lat, max_lat = -70, 85
    gdf = gdf.cx[min_lon:max_lon, min_lat:max_lat]
    gdf.plot(ax=axname, color='dimgray', linewidth=0.5)
    # plot distribution
    var_1d = var.values.flatten()
    var_1d = var_1d[~np.isnan(var_1d)]
    vmin = np.percentile(var_1d, 5)
    vmax = np.percentile(var_1d, 95)
    vcenter = 0 if 'trend' in varname else (vmin + vmax) / 2
    norm = TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)
    scatter = axname.scatter(
        lon, lat,
        c=var,
        cmap=cmap,
        norm=norm,
        s=sz,
        alpha=alp,
        linewidth=linewidth,
        edgecolors=edgecolors
    )
    # colorbar
    ax_pos = axname.get_position()
    left_loc, bottom_loc = ax_pos.get_points()[0]
    right_loc, top_loc = ax_pos.get_points()[1]
    cbar_ax = fig.add_axes([left_loc + 0.05, bottom_loc - cbar_prop[0], right_loc - left_loc - 0.1, cbar_prop[1]])
    cbar = fig.colorbar(scatter, cax=cbar_ax, orientation='horizontal', extend='both')
    cbar.ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5))

    if 'trend' in varname:
        # add legend
        sig_legend = mlines.Line2D(
            [], [],
            color='dimgray',
            marker='o',
            markersize=sz - 2,
            linewidth=0,
            markerfacecolor='none',
            label=r'$p \leq 0.05$'
        )
        axname.legend(
            handles=[sig_legend],
            loc='lower left',
            bbox_to_anchor=(0, 0),
            frameon=False
        )
        axname.yaxis.tick_right()
        axname.yaxis.set_label_position("right")
        # add unit
        cbar.ax.text(1.06, 0.5, unit, va='center', ha='left', color='k', transform=cbar_ax.transAxes)
    axname = adjust_axis_label(axname)
    # add global mean and std
    global_mean = var.mean()
    global_std = var.std()
    new_fignum = f'{fignum}, {global_mean:.2f} \u00b1 {global_std:.2f}'
    axname = add_fignum(axname, new_fignum)

    return


# function to plot mean and trend of UI, RE, and R/Rmax in isd
def plot_mean_trend_isd(df, varname_ls, fignum_ls, gdf, outpath, cbar_prop):
    fig, axes = plt.subplots(4, 2, figsize=(12, 12), dpi=300)
    axes = axes.flatten()
    plt.subplots_adjust(
        left=0.06,
        right=0.94,
        top=0.98,
        bottom=0.04,
        hspace=0.35,
        wspace=0.08
    )
    for axname, varname, fignum in zip(axes[:-2], varname_ls, fignum_ls[:-2]):
        plot_distribution_isd(fig, axname, df, gdf, varname, fignum, cbar_prop)

    # add box
    mean = df[varname_ls[0]]
    trend = df[varname_ls[1]]
    p_name = varname_ls[1].replace('trend', 'p_value')
    p_value = df[p_name]
    mask_pos = (p_value <= 0.05) & (trend > 0)
    mask_neg = (p_value <= 0.05) & (trend < 0)
    mean_pos = mean[mask_pos]
    mean_neg = mean[mask_neg]

    box_data = [mean_neg.values, mean_pos.values]
    box_labels = ['Significant decrease', 'Significant increase']
    clr = ["#9CB0C3", "#EAB080"]
    alp = 0.7
    sz = 4
    axname = axes[-2]
    sns.boxplot(
        data=box_data,
        palette=clr,
        ax=axname,
        boxprops=dict(alpha=alp),
        flierprops=dict(marker='+', markersize=sz)
    )
    axname.set_ylabel("UI mean")
    axname.set_xticks([0, 1])
    axname.set_xticklabels(box_labels)
    ylim = axname.get_ylim()
    axname.set_ylim(ylim[0], ylim[1] + 0.05 * (ylim[1] - ylim[0]))
    ylim = axname.get_ylim()
    yloc = ylim[0] - 0.2 * (ylim[1] - ylim[0])
    for i in range(2):
        axname.text(i, yloc, f'(n = {len(box_data[i])})', ha='center', va='bottom', color='k')
    axname = add_fignum(axname, fignum_ls[-2])
    # add significant test
    p_value_pair = significance_test(box_data[0], box_data[1])
    text_pair = ['a', 'b'] if p_value_pair <= 0.05 else ['a', 'a']
    for i in range(2):
        y_loc = np.max(box_data[i]) + 0.01 * (ylim[1] - ylim[0])
        axname.text(i, y_loc, text_pair[i], ha='center', va='bottom', color='k')

    # add relationship between UI mean and UI trend
    ax8_mask = (~mean.isna()) & (~trend.isna())
    ax8_mean = mean[ax8_mask]
    ax8_trend = trend[ax8_mask] * 1000

    axname = axes[-1]
    sns.regplot(x=ax8_mean, y=ax8_trend, ci=95, marker='o', color=clr[0], ax=axname)
    slope, _, _, p_value, _ = linregress(ax8_mean, ax8_trend)
    axname.set_xlabel("UI mean")
    axname.set_ylabel("UI trend (kyr$^{-1}$)")
    # add reference line
    axname.axhline(0, color='dimgray', linestyle='-', linewidth=1.5)
    axname.axvline(0, color='dimgray', linestyle='-', linewidth=1.5)
    axname.yaxis.tick_right()
    axname.yaxis.set_label_position("right")
    # add slope and p value
    xlim = axname.get_xlim()
    ylim = axname.get_ylim()
    xloc = xlim[0] + 0.55 * (xlim[1] - xlim[0])
    yloc = ylim[0] + 0.05 * (ylim[1] - ylim[0])
    txt = f'Slope = {slope:.2f} kyr$^-$$^1$, $p$ = {p_value:.2f}'
    axname.text(xloc, yloc, txt, va='bottom', ha='left')
    axname = add_fignum(axname, fignum_ls[-1])

    # save result
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=300)
    print(f'Saving {outpath}')
    plt.close()

    return


# function to plot mean and trend of rain days in isd
def plot_mean_trend_rain_day_isd(df, varname_ls, fignum_ls, gdf, outpath, cbar_prop):
    if len(varname_ls) == 4:
        fig, axes = plt.subplots(2, 2, figsize=(12, 6), dpi=300)
        axes = axes.flatten()
        plt.subplots_adjust(
            left=0.06,
            right=0.94,
            top=0.98,
            bottom=0.1,
            hspace=0.3,
            wspace=0.08
        )
    elif len(varname_ls) == 2:
        fig, axes = plt.subplots(2, 1, figsize=(6, 6), dpi=300)
        axes = axes.flatten()
        plt.subplots_adjust(
            left=0.09,
            right=0.98,
            top=0.97,
            bottom=0.1,
            hspace=0.35,
            wspace=0
        )
    for axname, varname, fignum in zip(axes, varname_ls, fignum_ls):
        plot_distribution_isd(fig, axname, df, gdf, varname, fignum, cbar_prop)
    if len(varname_ls) == 2:
        axes[1].yaxis.tick_left()
        axes[1].yaxis.set_label_position("left")

    # save result
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=300)
    print(f'Saving {outpath}')
    plt.close()

    return


def main():
    # load data
    CSV_PATH = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station_isd.csv'
    df = pd.read_csv(CSV_PATH)
    shp = r'../data/global_coastline_110m/global_coastline_110m.shp'
    gdf = gpd.read_file(shp)

    # daily scale
    varname_ls = ['S_daily_mean', 'S_daily_trend',
                  'D_daily_mean', 'D_daily_trend',
                  'PRCP_ratio_mean', 'PRCP_ratio_trend']
    fignum_ls = ['(a) Multi-year mean of UI (ISD)', '(d) Trend of UI (ISD)',
                 '(b) Multi-year mean of RE (ISD)', '(e) Trend of RE (ISD)',
                 '(c) Multi-year mean of R/Rmax (ISD)', '(f) Trend of R/Rmax (ISD)',
                 '(g) UI mean in different regions (ISD)', '(h) Relationship between UI mean and UI trend (ISD)']
    outpath = rf'../fig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/mean_trend_S_D_PRCP_ratio_daily_isd.png'
    cbar_prop = [0.03, 0.01]
    plot_mean_trend_isd(df, varname_ls, fignum_ls, gdf, outpath, cbar_prop)

    # monthly scale
    varname_ls_monthly = [varname.replace('daily', 'monthly') for varname in varname_ls]
    outpath = rf'../fig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/mean_trend_S_D_PRCP_ratio_monthly_isd.png'
    plot_mean_trend_isd(df, varname_ls_monthly, fignum_ls, gdf, outpath, cbar_prop)

    # # 2000-2020, daily scale
    # varname_ls_2000 = [f'{varname}_post_2000' for varname in varname_ls]
    # outpath = r'../fig/mean_trend_S_D_PRCP_ratio_daily_post_2000_isd.png.png'
    # plot_mean_trend_isd(df, varname_ls_2000, fignum_ls, gdf, outpath, cbar_prop)

    # plot rainy days
    # daily scale, rainy day, > 0 mm
    varname_ls = ['rain_day_mean', 'rain_day_trend']
    fignum_ls = ['(a) Mean rainy days (ISD)',
                 '(b) Trend of rainy days (ISD)']
    outpath = rf'../fig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/mean_trend_rain_day_isd.png'
    cbar_prop = [0.06, 0.02]
    plot_mean_trend_rain_day_isd(df, varname_ls, fignum_ls, gdf, outpath, cbar_prop)

    # daily scale, rainy day, > 0.1 mm
    varname_ls = ['rain_day_0p1_mean', 'rain_day_0p1_trend']
    outpath = rf'../fig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/mean_trend_rain_day_0p1_isd.png'
    plot_mean_trend_rain_day_isd(df, varname_ls, fignum_ls, gdf, outpath, cbar_prop)
    # varname_ls = ['rain_day_mean', 'rain_day_trend',
    #               'rain_day_mean_post_2000', 'rain_day_trend_post_2000']
    # fignum_ls = ['(a) Mean rainy days (ISD, 1980-2020)',
    #              '(c) Trend of rainy days (ISD, 1980-2020)',
    #              '(b) Mean rainy days (ISD, 2000-2020)',
    #              '(d) Trend of rainy days (ISD, 2000-2020)', ]
    # outpath = r'../fig/mean_trend_rain_day_isd.png'
    # cbar_prop = [0.06, 0.02]
    # plot_mean_trend_rain_day_isd(df, varname_ls, fignum_ls, gdf, outpath, cbar_prop)
    #
    # # daily scale, rainy day, > 0.1 mm
    # varname_ls = ['rain_day_0p1_mean', 'rain_day_0p1_trend',
    #               'rain_day_0p1_mean_post_2000', 'rain_day_0p1_trend_post_2000']
    # outpath = r'../fig/mean_trend_rain_day_0p1_isd.png'
    # plot_mean_trend_rain_day_isd(df, varname_ls, fignum_ls, gdf, outpath, cbar_prop)

    return


if __name__ == "__main__":
    main()