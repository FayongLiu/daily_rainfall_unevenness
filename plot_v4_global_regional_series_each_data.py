# Code for plotting global and regional series for each data

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
import os
import time
import seaborn as sns
import pymannkendall as mk
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.visualization import add_fignum, rename, get_alpha_label, cool, warm
from rainfall_ui.util.datainfo import (REGIONS, DATA_LS_80, DATA_LS_50)


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr
DATA_LS = DATA_LS_80 if START_YEAR >= 1980 else DATA_LS_50


# function to plot global and regional series for each data
def plot_global_regional_series_each_data(df_ls, region_name_ls, varname, axname, fignum):
    ''' df_ls: list of dataframes in order of 
        [global, North America, Europe, Asia, Australia]
    '''
    new_varname = rename(varname)
    ftsz = 10

    clr_ls = ['darkgray', cool[5], cool[3], warm[4], warm[3]]
    clr_dict = {}
    for region_name in region_name_ls:
        if region_name == 'global':
            clr_dict[region_name] = clr_ls[0]
        elif region_name == 'North America':
            clr_dict[region_name] = clr_ls[1]
        elif region_name == 'Europe':
            clr_dict[region_name] = clr_ls[2]
        elif region_name == 'Asia':
            clr_dict[region_name] = clr_ls[3]
        elif region_name == 'Australia':
            clr_dict[region_name] = clr_ls[4]
        else:
            raise ValueError(f'Unknown region name: {region_name}')
    alp = 0.7
    slopes = []
    means = []
    for i, (df, region_name) in enumerate(zip(df_ls, region_name_ls)):
        clr = clr_dict[region_name]
        if region_name == 'global':
            lab = 'Globe'
        else:
            lab = region_name
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
        slopes.append(slope)
        mean = df[varname].mean()
        means.append(mean)
        # add annotation
        if p_value < 0.01:
            text = f'Slope = {slope:.2f} ({slope_unit}), $P$ < 0.01'
        else:
            text = f'Slope = {slope:.2f} ({slope_unit}), $P$ = {p_value:.2f}'
        if i < 3:
            x = 0.49
            y_idx = i
            ha = 'right'
        else:
            x = 0.5
            y_idx = i - 3
            ha = 'left'
        y0 = -0.47
        axname.text(x, y0 + 0.1 * y_idx, text, transform=axname.transAxes, va='bottom', ha=ha, color=clr, alpha=alp, fontsize=ftsz-1)
    axname.set_ylabel(ylab, fontsize=ftsz)
    axname.set_xlabel('', fontsize=ftsz)
    axname.set_xlim([START_YEAR-1, END_YEAR+1])
    axname.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5))
    axname.yaxis.set_major_locator(ticker.MaxNLocator(nbins=4))
    axname.tick_params(axis='both', which='major', labelsize=ftsz)
    add_fignum(axname, fignum, xoffset=0.02, yoffset=-0.1, ftsz=ftsz+2)
    if fignum == 'd':
        axname.legend(bbox_to_anchor=[1.25, 1.01], loc='upper left', ncols=1, frameon=False, fontsize=ftsz)

    return slopes, means


def main():

    t1 = time.time()

    varname_ls = ['S_daily']
    for varname in varname_ls:
        print(f'Plotting {varname}...')
        fig, axes = plt.subplots(7, 5, figsize=(20, 16), dpi=300)
        axes = axes.flatten()
        to_delete = [9, 4]
        for idx in to_delete:
            fig.delaxes(axes[idx])
        axes = np.delete(axes, to_delete)
        plt.subplots_adjust(
            left=0.04,
            right=0.97,
            top=0.99,
            bottom=0.045,
            hspace=0.53,
            wspace=0.28
        )

        data_name_ls = ['station'] + DATA_LS
        region_name_ls = ['global'] + list(REGIONS.keys())
        slopes_ls = []
        means_ls = []
        for i, data_name in enumerate(data_name_ls):
            df_ls = []
            for region in region_name_ls:
                if region == 'global':
                    tempt_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/global_{data_name}.csv'
                else:
                    tempt_path = rf'../data/mean_trend/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/region_{region.replace(" ", "_")}_{data_name}.csv'
                tempt_df = pd.read_csv(tempt_path)
                df_ls.append(tempt_df)
            
            axname = axes[i]
            fignum = get_alpha_label(i, with_parenthesis=False)
            # if i == 0:
            #     fignum = f'(a) Gauges'
            # else:
            #     fignum = f'{get_alpha_label(i)} {data_name}'
            slopes, means = plot_global_regional_series_each_data(df_ls, region_name_ls, varname, axname, fignum)
            slopes_ls.append(slopes)
            means_ls.append(means)
        
        slope_df = pd.DataFrame(slopes_ls)
        slope_df.columns = region_name_ls
        slope_df.index = data_name_ls
        df_outpath = rf'../data/global_regional_slopes_means/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{varname}_global_regional_slopes_each_data.csv'
        os.makedirs(os.path.dirname(df_outpath), exist_ok=True)
        slope_df.to_csv(df_outpath, index=True)
        print(f'Saving {df_outpath}')

        mean_df = pd.DataFrame(means_ls)
        mean_df.columns = region_name_ls
        mean_df.index = data_name_ls
        df_outpath = rf'../data/global_regional_slopes_means/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{varname}_global_regional_means_each_data.csv'
        os.makedirs(os.path.dirname(df_outpath), exist_ok=True)
        mean_df.to_csv(df_outpath, index=True)
        print(f'Saving {df_outpath}')

        fig_outpath = rf'../fig_v4/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{varname}_global_regional_series_each_data.png'
        plt.savefig(fig_outpath, dpi=300)
        print(f'Saving {fig_outpath}')
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
    
