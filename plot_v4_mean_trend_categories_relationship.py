# Code for plotting mean and trend by category, relationship between mean and trend


import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
import statsmodels.api as sm
import time
import os
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.visualization import add_fignum, rename, get_alpha_label, cool
from rainfall_ui.util.datainfo import CATEGORY_NAMES, CATEGORY_LS_80, CATEGORY_LS_50

args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr
CATEGORY_LS = CATEGORY_LS_80 if START_YEAR >= 1980 else CATEGORY_LS_50


# function to plot mean and trend by category
def plot_mean_trend_category_relationship(ds_ls, gauge_df, varname, bins=20):
    ftsz = 10
    varname_lab = rename(varname)
    varname_mean = f'{varname}_mean'
    varname_trend = f'{varname}_trend'
    clr_scatter = cool[0]
    clr_bin = cool[3]
    clr_line = cool[4]
    
    # load data
    if 'rain_day' in varname:
        trend_ds_ls = [ds[varname_trend] for ds in ds_ls]
        trend_df = gauge_df[varname_trend]
        lab_mean = f'Multi-year mean of {varname_lab} (day)'
        lab_trend = f'Trend of {varname_lab} (day yr$^-$$^1$)'
        unit_slope = 'yr$^-$$^1$'
    elif 'STD_' in varname:
        trend_ds_ls = [ds[varname_trend] * 10 for ds in ds_ls]
        trend_df = gauge_df[varname_trend] * 10
        lab_mean = f'Multi-year mean of {varname_lab} (mm)'
        lab_trend = f'Trend of {varname_lab} (mm decade$^-$$^1$)'
        unit_slope = 'decade$^-$$^1$'
    else:
        trend_ds_ls = [ds[varname_trend] * 1000 for ds in ds_ls]
        trend_df = gauge_df[varname_trend] * 1000
        if varname_lab == 'R/Rmax':
            lab_mean = 'Multi-year mean of $R$/$R$$_{max}$'
            lab_trend = 'Trend of $R$/$R$$_{max}$ (kyr$^-$$^1$)'
        else:
            lab_mean = f'Multi-year mean of {varname_lab}'
            lab_trend = f'Trend of {varname_lab} (kyr$^-$$^1$)'
        unit_slope = 'kyr$^-$$^1$'
    mean_ds_ls = [ds[varname_mean] for ds in ds_ls]
    mean_df = gauge_df[varname_mean]
    new_ds_ls = [mean_ds_ls, trend_ds_ls]
    df_ls = [mean_df, trend_df]

    # plot distribution
    fig, axes = plt.subplots(2, 2, figsize=(8, 8), dpi=300)
    axes = axes.flatten()
    plt.subplots_adjust(
        left=0.1,
        right=0.99,
        top=0.99,
        bottom=0.06,
        hspace=0.2,
        wspace=0.25
    )

    for i in range(4):
        axname = axes[i]
        if i == 0:
            mean_value = df_ls[0]
            trend_value = df_ls[1]
        else:
            mean_value = new_ds_ls[0][i].sel(lat=slice(-60, 90)).values.flatten()
            trend_value = new_ds_ls[1][i].sel(lat=slice(-60, 90)).values.flatten()
        # remove nan values
        if varname in ['S_daily', 'PRCP_ratio']:
            valid_mask = ~np.isnan(mean_value) & ~np.isnan(trend_value)
        elif varname == 'S_monthly':
            valid_mask = ~np.isnan(mean_value) & ~np.isnan(trend_value)
        else:
            valid_mask = ~np.isnan(mean_value) & ~np.isnan(trend_value)
        
        mean_value = mean_value[valid_mask]
        trend_value = trend_value[valid_mask]

        # weighted least squares
        q = min(bins, len(pd.qcut(mean_value, bins, duplicates='drop').unique()))
        df = pd.DataFrame({'x': mean_value, 'y': trend_value})
        df['bin'] = pd.qcut(df['x'], q=q, duplicates='drop')
        binned = (
            df.groupby('bin', observed=True)
            .agg(
                x_median=('x', 'median'),
                y_median=('y', 'median'),
                x_q25=('x', lambda s: s.quantile(0.25)),
                x_q75=('x', lambda s: s.quantile(0.75)),
                y_q25=('y', lambda s: s.quantile(0.25)),
                y_q75=('y', lambda s: s.quantile(0.75)),
                n=('y', 'size'),
            )
            .reset_index(drop=True)
        )
        X_b = sm.add_constant(binned['x_median'])
        wls_b = sm.WLS(binned['y_median'], X_b, weights=binned['n']).fit(cov_type='HC3')
        slope = wls_b.params['x_median']
        p_value = wls_b.pvalues['x_median']

        # scatter
        axname.scatter(mean_value, trend_value, s=3, color=clr_scatter, alpha=0.1, edgecolors='none', rasterized=True)
        # box median, 25%, 75% for each bin
        err = axname.errorbar(binned['x_median'], binned['y_median'], yerr=[binned['y_median'] - binned['y_q25'], binned['y_q75'] - binned['y_median']],
              fmt='none', ecolor=clr_bin, elinewidth=1.0, capsize=2)
        median = axname.scatter(binned['x_median'], binned['y_median'], s=20, facecolor=clr_bin, edgecolor='white', linewidth=1.0)
        # regression line for binned WLS
        x_grid = np.linspace(mean_value.min(), mean_value.max(), 200)
        y_grid = wls_b.params['const'] + slope * x_grid
        wls, = axname.plot(x_grid, y_grid, color=clr_line, linewidth=2.0, linestyle='--', alpha=0.9)

        # set axis
        xlim_max = binned['x_median'].max() + 0.1 * (binned['x_median'].max() - binned['x_median'].min())
        ylim_min = binned['y_q25'].min() - 0.1 * (binned['y_q75'].max() - binned['y_q25'].min())
        ylim_max = binned['y_q75'].max() + 0.1 * (binned['y_q25'].max() - binned['y_q25'].min())
        axname.set_xlim(0, xlim_max)
        axname.set_ylim(ylim_min, ylim_max)

        axname.spines['top'].set_visible(False)
        axname.spines['right'].set_visible(False)

        # add ticks
        axname.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5, prune='both'))
        axname.yaxis.set_major_locator(ticker.MaxNLocator(nbins=5, prune='both'))
        axname.set_xlabel(lab_mean, fontsize=ftsz)
        axname.set_ylabel(lab_trend, fontsize=ftsz)
        axname.tick_params(axis='both', which='major', labelsize=ftsz)
        # add slope and p value
        if p_value < 0.01:
            txt = f'n = {len(mean_value)}\nSlope = {slope:.2f} {unit_slope}\n$P$ < 0.01'
        else:
            txt = f'n = {len(mean_value)}\nSlope = {slope:.2f} {unit_slope}\n$P$ = {p_value:.2f}'
        if varname == 'D_daily':
            axname.text(0.02, 0.01, txt, va='bottom', ha='left', transform=axname.transAxes, fontsize=ftsz, color=clr_line)
        elif varname == 'S_daily':
            if i in [0, 1, 2]:
                axname.text(0.02, 0.01, txt, va='bottom', ha='left', transform=axname.transAxes, fontsize=ftsz, color=clr_line)
            else:
                axname.text(0.02, 0.85, txt, va='bottom', ha='left', transform=axname.transAxes, fontsize=ftsz, color=clr_line)
        else:
            if i in [0, 2, 3]:
                axname.text(0.02, 0.01, txt, va='bottom', ha='left', transform=axname.transAxes, fontsize=ftsz, color=clr_line)
            else:
                axname.text(0.55, 0.01, txt, va='bottom', ha='left', transform=axname.transAxes, fontsize=ftsz, color=clr_line)

        fignum = get_alpha_label(i, with_parenthesis=False)
        add_fignum(axname, fignum, xoffset=-0.2, yoffset=-0.05, ftsz=ftsz+2)

        if i == 0:
            axname.legend(
                handles=[median, err, wls],
                labels=[f'Binned median (q={bins})', 'Binned 25%-75%', 'Binned WLS'],
                loc='upper left',
                fontsize=ftsz,
                frameon=False,
                ncol=1
            )
    
    # save result
    outpath = rf'../fig_v4/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{varname}_mean_trend_categories_relationship_{bins}.png'
    plt.savefig(outpath, dpi=300)
    print(f'Saving {outpath}')
    plt.close()

    return

def main():

    t1 = time.time()

    station_nc_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.nc'
    station_csv_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.csv'
    station_nc = xr.open_dataset(station_nc_path)
    station_csv = pd.read_csv(station_csv_path)
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
        if varname == 'S_daily':
            for bins in [10, 20, 30]:
                plot_mean_trend_category_relationship(ds_ls, station_csv, varname, bins=bins)
        else:
            plot_mean_trend_category_relationship(ds_ls, station_csv, varname)
    
    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")
    
    return


if __name__ == "__main__":
    
    main()

