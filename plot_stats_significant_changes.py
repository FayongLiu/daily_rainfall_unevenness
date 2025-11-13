# -*- coding: utf-8 -*-
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import os
import pandas as pd
import time
from plot_mean_trend_isd import add_fignum
from pre_isd_select_valid_station import START_YEAR, END_YEAR, TH_YEAR
from pre_GRID_cal_maximum_annual_prcp import model_ls


# function to plot statistics of significant changes in each panel
def plot_stats(axname, isd, cru, era, cmip, fignum):
    width = 0.2
    x = np.arange(3)
    clr_ls = ['#EAB080', '#7C9D97', '#9CB0C3', '#C9C9C9']
    center_ls = np.array([-3 * width / 2, -width / 2, width / 2, 3 * width / 2])
    data_ls = [isd, cru, era, cmip]
    alp = 0.8
    for i in range(len(clr_ls)):
        if i <= 2:
            axname.bar(x + center_ls[i], data_ls[i], width=width, color=clr_ls[i], alpha=alp)
            for j in range(3):
                text = str(round(data_ls[i][j], 1))
                axname.text(j + center_ls[i], data_ls[i][j], text, va='bottom', ha='center')
        else:
            sns.boxplot(
                data=data_ls[i],
                color=clr_ls[i],
                width=width,
                ax=axname,
                positions=x + center_ls[i],
                flierprops=dict(marker='+', markersize=5, alpha=alp)
            )
            for j in range(3):
                text = str(round(np.mean(data_ls[i][j]), 1))
                axname.text(j + center_ls[i], np.max(data_ls[i][j]), text, va='bottom', ha='center')
    axname.set_xlim(-0.5, 2.5)
    ylim = axname.get_ylim()
    axname.set_ylim(ylim[0], ylim[1] + 0.05*(ylim[1]-ylim[0]))
    axname.set_xticks([0, 1, 2])
    axname.set_xticklabels(['Significant increase', 'Significant decrease', 'Non-significant'])
    axname.set_xlabel('')
    axname.set_ylabel('Percentage (%)')
    labels = ['ISD', 'CRU-JRA', 'ERA5-Land', 'CMIP6 ensembles']
    handles = [Patch(color=clr_ls[i], label=labels[i]) for i in range(4)]
    axname.legend(handles=handles, loc='upper left', frameon=False, ncol=1)
    axname = add_fignum(axname, fignum)

    return


# function to plot statistics of significant changes in combined figure
def plot_stats_combined(df_ls, varname_ls, fignum_ls, key):
    for col in range(2):
        num_panel = len(fignum_ls)
        fig, axes = plt.subplots(num_panel, 1, figsize=(8, 3 * num_panel), dpi=300)
        if num_panel == 3:
            plt.subplots_adjust(
                left=0.09,
                right=0.98,
                top=0.97,
                bottom=0.04,
                hspace=0.25,
                wspace=0
            )
            axes = axes.flatten()
        elif num_panel == 1:
            plt.subplots_adjust(
                left=0.08,
                right=0.98,
                top=0.98,
                bottom=0.1,
                hspace=0,
                wspace=0
            )
            axes = [axes]
            
        area_key_ls = ['_grid_count', '_area_weighted']
        isd_col_ls = ['sig_inc', 'sig_dec', 'non_sig']
        grid_col_ls = [['sig_inc_count', 'sig_dec_count', 'non_sig_count'],
                       ['sig_inc_area', 'sig_dec_area', 'non_sig_area']]
                       
        for i, axname in enumerate(axes):
            isd = df_ls[0].loc[varname_ls[i], isd_col_ls].values * 100
            cru = df_ls[1].loc[varname_ls[i], grid_col_ls[col]].values * 100
            era = df_ls[2].loc[varname_ls[i], grid_col_ls[col]].values * 100
            cmip = [[], [], []]
            for cmip_df in df_ls[3:]:
                for j in range(3):
                    cmip[j].append(cmip_df.loc[varname_ls[i], grid_col_ls[col][j]] * 100)
            plot_stats(axname, isd, cru, era, cmip, fignum_ls[i])
            
        # save result
        outpath = rf'../fig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/stats_{key}{area_key_ls[col]}.png'
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        plt.savefig(outpath, dpi=300)
        plt.close()
        print(f'Saving {outpath}')

    return


def main():
    dataname_ls = ['isd', 'CRU_JRA', 'ERA5_Land'] + model_ls
    df_ls = [pd.read_csv(rf'../data/stats_sig/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{data_name}.csv', index_col=0) for
             data_name in dataname_ls]
    # daily scale
    varname_ls = ['S_daily', 'D_daily', 'PRCP_ratio']
    fignum_ls = ['(a) Daily UI', '(b) Daily RE', '(c) Daily R/Rmax']
    key = 'S_D_PRCP_ratio_daily'
    plot_stats_combined(df_ls, varname_ls, fignum_ls, key)

    # monthly scale
    varname_ls = [varname.replace('daily', 'monthly') for varname in varname_ls]
    fignum_ls = [fignum.replace('Daily', 'Monthly') for fignum in fignum_ls]
    key = 'S_D_PRCP_ratio_monthly'
    plot_stats_combined(df_ls, varname_ls, fignum_ls, key)

    # rainy days
    key_ls = ['rain_day', 'rain_day_0p1']
    for key in key_ls:
        varname_ls = [key]
        fignum_ls = ['']
        plot_stats_combined(df_ls, varname_ls, fignum_ls, key)

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