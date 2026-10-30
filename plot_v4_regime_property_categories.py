# Code for plotting property of each regime
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.gridspec import GridSpec
import seaborn as sns
import time
import os
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.visualization import add_fignum, get_alpha_label
from rainfall_ui.util.datainfo import CATEGORY_NAMES

args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr


# function to plot regime property by category
def plot_regime_property_category(ds_ls, scale):

    color_ls = ['dimgray', '#83BCD7', '#E8B596']
    prop_ls = ['UI', '$R$/$R$$_{max}$', 'RE']
    ftsz = 10
    # load data
    regime_ds_ls = []
    regime_id_ls = [0, 1, 10, 11]
    # 0: --, 1: -+, 10: +-, 11: ++ 
    for ds in ds_ls:
        re_ds = ds[f'D_{scale}_trend']
        prcp_ds = ds['PRCP_ratio_trend']
        re_ds = xr.where(re_ds > 0, 1, re_ds)
        re_ds = xr.where(re_ds < 0, 0, re_ds)
        prcp_ds = xr.where(prcp_ds > 0, 1, prcp_ds)
        prcp_ds = xr.where(prcp_ds < 0, 0, prcp_ds)
        regime_ds = prcp_ds * 10 + re_ds
        regime_ds_ls.append(regime_ds)

    fig = plt.figure(figsize=(12, 8), dpi=300)
    grid = GridSpec(4, 3, figure=fig, left=0.08, bottom=0.03, right=0.99, top=0.99, wspace=0.25, hspace=0.2)
    ax_1_ls = [plt.subplot(grid[i, 0]) for i in range(4)]
    ax_2_ls = [plt.subplot(grid[i, 1]) for i in range(4)]
    ax_3_ls = [plt.subplot(grid[i, 2]) for i in range(4)]

    for i in range(len(ax_1_ls)):
        ax_box_ls = [ax_1_ls[i], ax_2_ls[i], ax_3_ls[i]]
        # get data for each category
        ds = ds_ls[i]
        ds = ds.sel(lat=slice(-60, 90))
        regime_ds = regime_ds_ls[i]
        regime_ds = regime_ds.sel(lat=slice(-60, 90))
        data_ls = []
        for regime_id in regime_id_ls:
            tempt_s_mean = ds[f'S_{scale}_mean'].where(regime_ds == regime_id).values.flatten()
            tempt_d_mean = ds[f'D_{scale}_mean'].where(regime_ds == regime_id).values.flatten()
            tempt_prcp_mean = ds['PRCP_ratio_mean'].where(regime_ds == regime_id).values.flatten()
            # remove nan values
            tempt_s_mean = tempt_s_mean[~np.isnan(tempt_s_mean)]
            tempt_d_mean = tempt_d_mean[~np.isnan(tempt_d_mean)]
            tempt_prcp_mean = tempt_prcp_mean[~np.isnan(tempt_prcp_mean)]
            temp_df = pd.DataFrame({
                f'S_{scale}_mean': tempt_s_mean,
                f'D_{scale}_mean': tempt_d_mean,
                'PRCP_ratio_mean': tempt_prcp_mean,
                'regime_id': regime_id
            })
            data_ls.append(temp_df)
        # boxplot
        df_long = pd.concat(data_ls, ignore_index=True)
        mean_df_d = df_long.groupby('regime_id')[f'D_{scale}_mean'].mean()
        std_df_d = df_long.groupby('regime_id')[f'D_{scale}_mean'].std()
        mean_df_prcp = df_long.groupby('regime_id')['PRCP_ratio_mean'].mean()
        std_df_prcp = df_long.groupby('regime_id')['PRCP_ratio_mean'].std()
        mean_df_s = df_long.groupby('regime_id')[f'S_{scale}_mean'].mean()
        std_df_s = df_long.groupby('regime_id')[f'S_{scale}_mean'].std()
        for j in range(len(ax_box_ls)):
            ax_box = ax_box_ls[j]
            if j == 0:
                prop_name = f'S_{scale}_mean'
                ylab = 'Multi-year mean of UI'
                mean_df = mean_df_s
                std_df = std_df_s
            elif j == 1:
                prop_name = 'PRCP_ratio_mean'
                ylab = 'Multi-year mean of $R$/$R$$_{max}$'
                mean_df = mean_df_prcp
                std_df = std_df_prcp
            else:
                prop_name = f'D_{scale}_mean'
                ylab = 'Multi-year mean of RE'
                mean_df = mean_df_d
                std_df = std_df_d
                
            box_alp= 1.0
            box_lw = 1.0
            box_clr = color_ls[j]
            sns.boxplot(
                data=df_long,
                x='regime_id',
                y=prop_name,
                color=box_clr,
                fill=None,
                ax=ax_box,
                showmeans=True,
                showfliers=False,
                width=0.4,
                legend=False,
                boxprops={
                    'alpha': box_alp,
                    'color': box_clr,
                    'linewidth': box_lw
                },
                medianprops={
                    'color': box_clr,
                    'linewidth': box_lw,
                    'alpha': box_alp
                },
                whiskerprops={
                    'color': box_clr,
                    'linewidth': box_lw,
                    'alpha': box_alp
                },
                capprops={
                    'color': box_clr,
                    'linewidth': box_lw,
                    'alpha': box_alp
                },
                meanprops={
                    'marker': 'o',
                    'markerfacecolor': 'none',
                    'markeredgecolor': box_clr,
                    'markeredgewidth': 1.0,
                    'markersize': 4
                }
            )
            ax_box.set_xticks(range(len(regime_id_ls)))
            ax_box.set_xticklabels(['--', '-+', '+-', '++'], fontsize=ftsz)
            ax_box.set_xlabel('')
            ax_box.set_ylabel(ylab, fontsize=ftsz)
            ax_box.yaxis.set_major_locator(ticker.MaxNLocator(nbins=4))
            fignum = get_alpha_label(i*3+j, with_parenthesis=False)
            add_fignum(ax_box, fignum, xoffset=0.01, yoffset=-0.11, ftsz=ftsz+2)

            # add annotation
            ylim = ax_box.get_ylim()
            ax_box.set_ylim(ylim[0]-0.05*(ylim[1] - ylim[0]), ylim[1])
            ylim = ax_box.get_ylim()
            for k, id in enumerate(regime_id_ls):
                if j == 1:
                    text = f'{mean_df.loc[id]:.3f}\u00b1{std_df.loc[id]:.3f}'
                    fz = ftsz - 2
                else:
                    text = f'{mean_df.loc[id]:.2f}\u00b1{std_df.loc[id]:.2f}'
                    fz = ftsz - 1
                ax_box.text(
                    k, ylim[0], text, va='bottom', ha='center', fontsize=fz, color=box_clr
                )

    # save
    outpath = rf'../fig_v4/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/regime_property_categories_{scale}.png'
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

    for scale in ['daily']:#, 'monthly']:
        plot_regime_property_category(ds_ls, scale)
    
    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")
    
    return


if __name__ == "__main__":
    
    main()

