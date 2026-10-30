# Code for plotting global and regional series by category

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
import time
import seaborn as sns
import pymannkendall as mk
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.visualization import add_fignum, rename, get_alpha_label, cool, warm
from rainfall_ui.util.datainfo import (REGIONS, CATEGORY_NAMES, CATEGORY_NAMES_FULL, DATA_LS_80, DATA_LS_50)


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr
DATA_LS = DATA_LS_80 if START_YEAR >= 1980 else DATA_LS_50


# function to plot global and regional series by category
def plot_global_regional_series_categories(df_ls, data_name_ls, varname, axname, fignum):
    ''' df_ls: list of dataframes in order of 
        [Guages, Gauge-based, Satellite-based, Reanalysis, CMIP6 ensembles]
    '''
    ftsz_in = 10
    new_varname = rename(varname)

    clr_ls = [cool[5], cool[3], warm[4], warm[3]]
    clr_dict = {}
    for data_name in data_name_ls:
        if data_name == 'station':
            clr_dict[data_name] = clr_ls[0]
        elif data_name == 'Gauge-based':
            clr_dict[data_name] = clr_ls[1]
        elif data_name == 'Reanalysis':
            clr_dict[data_name] = clr_ls[2]
        elif data_name == 'CMIP6':
            clr_dict[data_name] = clr_ls[3]
        else:
            raise ValueError(f'Unknown data name: {data_name}')
    alp = 0.7
    if fignum == 'a':
        y0 = 0.32
    elif fignum == 'b':
        y0 = 0.4
    elif fignum == 'c':
        y0 = 0.41
    elif fignum == 'd':
        y0 = 0.35
    elif fignum == 'e':
        y0 = -0.18
    for i, (df, data_name) in enumerate(zip(df_ls, data_name_ls)):
        clr = clr_dict[data_name]
        if data_name == 'station':
            lab = 'Gauges'
        else:
            idx = CATEGORY_NAMES.index(data_name)
            lab = CATEGORY_NAMES_FULL[idx]
        if (data_name == 'Gauge-based') & (START_YEAR == 1980):
            df = df[(df['year'] >= 1982) & (df['year'] <= 2016)]
        axname.plot(df['year'].values, df[varname].values, linestyle='-', linewidth=1.5, color=clr, alpha=alp, label=lab)
        sns.regplot(x=df['year'].values, y=df[varname].values, ci=95, scatter=False, color=clr, ax=axname, line_kws=dict(linewidth=1.5))
        result = mk.original_test(df[varname].values)
        slope = result.slope
        p_value = result.p
        if 'rain_day' in varname:
            ylab = 'Rainy days (day)'
            slope_unit = 'day yr$^{-1}$'
        elif 'STD_' in varname:
            slope = slope * 10
            ylab = 'Rainfall variability (mm)'
            slope_unit = 'mm decade$^{-1}$'
        else:
            slope = slope * 1000
            ylab = new_varname
            slope_unit = 'kyr$^{-1}$'
        # add annotation
        if p_value < 0.01:
            text = f'Slope = {slope:.2f} ({slope_unit}), $P$ < 0.01'
        else:
            text = f'Slope = {slope:.2f} ({slope_unit}), $P$ = {p_value:.2f}'
        x = 0.02
        y_idx = i
        ha = 'left'
        if fignum == 'e':
            if i < 2:
                x = 0.49
                y_idx = i
                ha = 'right'
            else:
                x = 0.5
                y_idx = i - 2
                ha = 'left'
        axname.text(x, y0 - 0.07 * y_idx, text, transform=axname.transAxes, va='bottom', ha=ha, color=clr, alpha=alp, fontsize=ftsz_in)
    axname.set_ylabel(ylab, fontsize=ftsz_in)
    axname.set_xlabel('', fontsize=ftsz_in)
    axname.set_xlim([START_YEAR-1, END_YEAR+1])
    axname.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5))
    axname.yaxis.set_major_locator(ticker.MaxNLocator(nbins=5))
    axname.tick_params(axis='both', which='major', labelsize=ftsz_in)
    add_fignum(axname, fignum, xoffset=0.02, yoffset=-0.08, ftsz=ftsz_in+2)
    if fignum == 'c':
        axname.legend(bbox_to_anchor=[0.55, 0.51], loc='upper left', ncols=1, frameon=False, fontsize=ftsz_in)
    # if fignum == 'a':
    #     if varname == 'S_daily':
    #         if START_YEAR >= 1980:
    #             axname.legend(bbox_to_anchor=[0.01, 0.71], loc='upper left', ncols=2, frameon=False)
    #         else:
    #             axname.legend(bbox_to_anchor=[0.01, 0.5], loc='upper left', ncols=2, frameon=False)
    #     elif varname == 'S_monthly':
    #         axname.legend(bbox_to_anchor=[0.01, 0.85], loc='upper left', ncols=2, frameon=False)
    #     elif varname == 'D_daily':
    #         axname.legend(bbox_to_anchor=[0.01, 0.4], loc='upper left', ncols=2, frameon=False)
    #     elif varname == 'D_monthly':
    #         axname.legend(bbox_to_anchor=[0.01, 0.6], loc='upper left', ncols=2, frameon=False)
    #     elif varname == 'PRCP_ratio':
    #         axname.legend(bbox_to_anchor=[0.01, 0.86], loc='upper left', ncols=2, frameon=False)
    #     elif varname == 'rain_day':
    #         axname.legend(bbox_to_anchor=[0.01, 0.9], loc='upper left', ncols=2, frameon=False)
    #     else:
    #         raise ValueError(f'Unknown varname: {varname}')

    return axname


def main():

    t1 = time.time()

    ftsz_out = 10
    varname_ls = ['S_daily']
    for varname in varname_ls:
        print(f'Plotting {varname}...')
        fig, axes = plt.subplots(3, 2, figsize=(10, 10), dpi=300)
        axes = axes.flatten()
        plt.subplots_adjust(
            left=0.07,
            right=0.99,
            top=0.99,
            bottom=0.07,
            hspace=0.15,
            wspace=0.2
        )
        if 'rain_day' in varname:
            slope_lab = 'Trend of rainy days (day yr$^{-1}$)'
        elif 'STD_' in varname:
            slope_lab = 'Trend of rainfall variability (mm decade$^{-1}$)'
        else:
            new_varname = rename(varname)
            slope_lab = 'Trend of ' + new_varname + ' (kyr$^{-1}$)'

        data_name_ls = ['station'] + CATEGORY_NAMES
        for i, region in enumerate(['global'] + list(REGIONS.keys())):
            df_ls = []
            for data_name in data_name_ls:
                if region == 'global':
                    if data_name in CATEGORY_NAMES:
                        tempt_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/global_{data_name}_ensembles.csv'
                    else:
                        tempt_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/global_{data_name}.csv'
                else:
                    if data_name in CATEGORY_NAMES:
                        tempt_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/region_{region.replace(" ", "_")}_{data_name}_ensembles.csv'
                    else:
                        tempt_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/region_{region.replace(" ", "_")}_{data_name}.csv'
                tempt_df = pd.read_csv(tempt_path)
                df_ls.append(tempt_df)
            
            axname = axes[i]
            # if region == 'global':
            #     fignum = f'(a) Globe'
            # else:
            #     fignum = f'{get_alpha_label(i)} {region}'
            fignum = get_alpha_label(i, with_parenthesis=False)
            axname = plot_global_regional_series_categories(df_ls, data_name_ls, varname, axname, fignum)

        # plot box
        ax_trend_box = axes[-1]
        clr_trend = 'darkgray'
        box_trend_path = rf'../data/global_regional_slopes_means/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{varname}_global_regional_slopes_each_data.csv'
        box_trend_df = pd.read_csv(box_trend_path, index_col=0)
        box_trend_df = box_trend_df.iloc[1:, :] # remove station
        data_trend_list = []
        for i, col in enumerate(box_trend_df.columns):
            for val in box_trend_df[col].dropna():
                data_trend_list.append({'Region': col, 'Slope': val})
        df_trend_long = pd.DataFrame(data_trend_list)
        trend_mean_df = df_trend_long.groupby('Region')['Slope'].mean()
        trend_std_df = df_trend_long.groupby('Region')['Slope'].std()

        # add refline
        ax_trend_box.axhline(0, color=clr_trend, linestyle="--", linewidth=1.5)

        x0 = np.arange(len(trend_mean_df))
        order = ['global', 'North America', 'Europe', 'Asia', 'Australia']
        data_slope = [df_trend_long.loc[df_trend_long['Region'] == r, 'Slope'].values for r in order]
        ax_trend_box.boxplot(
            data_slope, 
            positions=x0, 
            widths=0.5,
            patch_artist=False, 
            boxprops={'color': clr_trend, 'linewidth': 1.5},
            medianprops={'color': clr_trend, 'linewidth': 1.5},
            whiskerprops={'color': clr_trend, 'linewidth': 1.5},
            capprops={'color': clr_trend, 'linewidth': 1.5},
            showfliers=False,
            showmeans=True,
            meanprops={
                'marker': 'o',
                'markerfacecolor': 'none',
                'markeredgecolor': clr_trend,
                'markeredgewidth': 1.5,
                'markersize': 4
            }
        )
        # set ticks
        ax_trend_box.set_xlim(-0.5, 4.5)
        ax_trend_box.set_xticks(range(len(REGIONS.keys())+1))
        ax_trend_box.set_xticklabels(['Globe'] + list(REGIONS.keys()), fontsize=ftsz_out)
        ax_trend_box.set_xlabel('', fontsize=ftsz_out)
        ax_trend_box.set_ylim(-0.8, 0.8)
        ax_trend_box.set_ylabel(slope_lab, fontsize=ftsz_out)
        ax_trend_box.yaxis.set_major_locator(ticker.MaxNLocator(nbins=5))
        ax_trend_box.tick_params(axis='both', which='major', labelsize=ftsz_out)

        # add_fignum(ax_box, '(f) Comparison among globe/regions')
        add_fignum(ax_trend_box, 'f', xoffset=0.02, yoffset=-0.08, ftsz=ftsz_out+2)

        # add annotation
        ylim = ax_trend_box.get_ylim()
        for k, region in enumerate(['global'] + list(REGIONS.keys())):
            text = f'{trend_mean_df.loc[region]:.2f}\u00b1{trend_std_df.loc[region]:.2f}'
            ax_trend_box.text(
                k, ylim[0]-0.3, text, va='bottom', ha='center', fontsize=ftsz_out, color='darkgray'
            )
        ax_trend_box.text(0.02, 0.08, f'n = {len(box_trend_df)} gridded datasets', va='top', ha='left', 
                          transform=ax_trend_box.transAxes, fontsize=ftsz_out+1, color='darkgray')

        # # add legend
        # handles, labels = axname.get_legend_handles_labels()
        # ax_trend_box.legend(handles, labels, bbox_to_anchor=[0.005, 0.46], loc='upper left', ncols=1, frameon=False, fontsize=ftsz_out)

        outpath = rf'../fig_v4/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{varname}_global_regional_series_categories.png'
        plt.savefig(outpath, dpi=300)
        print(f'Saving {outpath}')
        plt.close()
    
    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")

    return


if __name__ == "__main__":
    
    main()
    
