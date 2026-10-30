# Code for plotting D and PRCP ratio relationship
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib import ticker
import statsmodels.api as sm
import time
import os
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.visualization import add_fignum, get_alpha_label, cool
from rainfall_ui.util.datainfo import CATEGORY_NAMES, CATEGORY_LS_80, CATEGORY_LS_50

args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr
CATEGORY_LS = CATEGORY_LS_80 if START_YEAR >= 1980 else CATEGORY_LS_50


# function to plot regime division by category
def plot_D_PRCP_ratio_category(ds_ls, gauge_df, scale, bins=20):

    clr_scatter = cool[0]
    clr_bin = cool[3]
    clr_line = cool[4]
    ftsz = 10
    fig = plt.figure(figsize=(8, 8), dpi=300)
    grid = GridSpec(2, 2, figure=fig, left=0.09, bottom=0.06, right=0.99, top=0.99, wspace=0.26, hspace=0.2)
    ax_ls = [plt.subplot(grid[i, j]) for i in range(2) for j in range(2)]
    for i in range(len(ds_ls)):
        ds = ds_ls[i]
        ds = ds.sel(lat=slice(-60, 90))
        axname = ax_ls[i]
        if i == 0:
            x = gauge_df['PRCP_ratio_trend'].values.flatten() * 1000
            y = gauge_df[f'D_{scale}_trend'].values.flatten() * 1000
        else:
            x = ds['PRCP_ratio_trend'].values.flatten() * 1000
            y = ds[f'D_{scale}_trend'].values.flatten() * 1000
        valid_mask = ~np.isnan(x) & ~np.isnan(y)
        x = x[valid_mask]
        y = y[valid_mask]
        # weighted least squares
        q = min(bins, len(pd.qcut(x, bins, duplicates='drop').unique()))
        df = pd.DataFrame({'x': x, 'y': y})
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
        axname.scatter(x, y, s=3, color=clr_scatter, alpha=0.1, edgecolors='none', rasterized=True)
        # box median, 25%, 75% for each bin
        err = axname.errorbar(binned['x_median'], binned['y_median'], yerr=[binned['y_median'] - binned['y_q25'], binned['y_q75'] - binned['y_median']], 
                              fmt='none', ecolor=clr_bin, elinewidth=1.0, capsize=2)
        median = axname.scatter(binned['x_median'], binned['y_median'], s=20, facecolor=clr_bin, edgecolor='white', linewidth=1.0)
        # regression line for binned WLS
        x_grid = np.linspace(x.min(), x.max(), 200)
        y_grid = wls_b.params['const'] + slope * x_grid
        wls, = axname.plot(x_grid, y_grid, color=clr_line, linewidth=2.0, linestyle='--', alpha=0.9)

        # set axis
        xlim_min = binned['x_median'].min() - 0.1 * (binned['x_median'].max() - binned['x_median'].min())
        xlim_max = binned['x_median'].max() + 0.1 * (binned['x_median'].max() - binned['x_median'].min())
        ylim_min = binned['y_q25'].min() - 0.1 * (binned['y_q75'].max() - binned['y_q25'].min())
        ylim_max = binned['y_q75'].max() + 0.1 * (binned['y_q25'].max() - binned['y_q25'].min())
        axname.set_xlim(xlim_min, xlim_max)
        axname.set_ylim(ylim_min, ylim_max)

        axname.spines['top'].set_visible(False)
        axname.spines['right'].set_visible(False)

        # add ticks
        axname.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5, prune='both'))
        axname.yaxis.set_major_locator(ticker.MaxNLocator(nbins=5, prune='both'))
        axname.set_ylabel('Trend of RE (kyr$^{-1}$)', fontsize=ftsz)
        axname.set_xlabel('Trend of $R$/$R$$_{max}$ (kyr$^{-1}$)', fontsize=ftsz)
        axname.tick_params(axis='both', which='major', labelsize=ftsz)
        # add slope and p value
        if p_value < 0.01:
            txt = f'n = {len(x)}\nSlope = {slope:.2f} \n$P$ < 0.01'
        else:
            txt = f'n = {len(x)}\nSlope = {slope:.2f} \n$P$ = {p_value:.2f}'
        axname.text(0.02, 0.01, txt, va='bottom', ha='left', transform=axname.transAxes, fontsize=ftsz, color=clr_line)

        fignum = get_alpha_label(i, with_parenthesis=False)
        add_fignum(axname, fignum, xoffset=-0.2, yoffset=-0.05, ftsz=ftsz+2)

        if i == 0:
            axname.legend(
                handles=[median, err, wls],
                labels=[f'Binned median (q={bins})', 'Binned 25%-75%', 'Binned WLS'],
                loc='upper left',
                bbox_to_anchor=(0.42, 1.05),
                fontsize=ftsz-1,
                frameon=False,
                ncol=1
            )

    # save result
    outpath = rf'../fig_v4/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/D_PRCP_ratio_ralationship_categories_{scale}_{bins}.png'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
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

    for scale in ['daily']:#, 'monthly']:
        for bins in [10, 20, 30]:
            plot_D_PRCP_ratio_category(ds_ls, station_csv, scale, bins)
    
    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")
    
    return


if __name__ == "__main__":
    
    main()

