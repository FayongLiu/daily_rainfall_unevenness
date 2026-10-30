# Code for visualization


import numpy as np
from scipy.stats import shapiro, levene, ttest_ind, ttest_rel, mannwhitneyu, wilcoxon
from matplotlib.colors import LinearSegmentedColormap


cool = ['#E9F3F5', '#D1EAEF', '#ABD5E3', '#83BCD7', '#599FC1', '#457DB6', '#325C98', '#1A3564']
warm = ['#F3EEE8', '#F5DAC7', '#E8B596', '#DF8A6D', '#D65C4F', '#C0333B', '#9B1D2B', '#690A1E']

cmap_cool = LinearSegmentedColormap.from_list("cool", cool, N=256)
cmap_warm = LinearSegmentedColormap.from_list("warm", warm, N=256)
cmap_coolwarm = LinearSegmentedColormap.from_list("coolwarm", cool[::-1] + warm, N=256)
cmap_warmcool = LinearSegmentedColormap.from_list("warmcool", warm[::-1] + cool, N=256)


# def a function to test the difference
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


# function to adjust x-y tick lables
def adjust_axis_label(axname, xlim=[-180.05, 180.05], ylim=[-60.05, 90.05], 
                      ticks_x=np.arange(-180, 180.001, 60), 
                      ticks_y=np.array([-60, -30, 0, 30, 60]),
                      ftsz=10):

    axname.set_xlim(xlim[0], xlim[1])
    axname.set_ylim(ylim[0], ylim[1])
    labels_x = [f'{abs(int(tick))}\xb0{"E" if tick > 0 else "W" if tick < 0 else " "}' for tick in ticks_x]
    labels_x[0], labels_x[-1] = ' ', ' '
    axname.set_xticks(ticks_x)
    axname.set_xticklabels(labels_x, fontsize=ftsz)
    labels_y = [f'{abs(tick)}\xb0{"N" if tick > 0 else "S" if tick < 0 else " "}' for tick in ticks_y]
    axname.set_yticks(ticks_y)
    axname.set_yticklabels(labels_y, fontsize=ftsz)
    axname.set_xlabel(None)
    axname.set_ylabel(None)
    axname.set_title('')

    return axname


# function set fig num
def add_fignum(axname, txt, xoffset=0, yoffset=0, ftsz=12):

    xlim = axname.get_xlim()
    ylim = axname.get_ylim()
    xpos = xlim[0] + xoffset*(xlim[1] - xlim[0])
    ypos = ylim[1] + yoffset*(ylim[1] - ylim[0])
    axname.text(xpos, ypos, txt, va='bottom', ha='left', fontweight='bold', fontsize=ftsz)

    return axname


# function to rename varname
def rename(varname):
    if 'S_' in varname:
        title_varname = 'UI'
    elif ('D_' in varname) and ('STD_' not in varname):
        title_varname = 'RE'
    elif 'PRCP_ratio' in varname:
        title_varname = 'R/Rmax'
    elif 'rain_day' in varname:
        title_varname = 'rainy days'
    elif 'STD_' in varname:
        title_varname = 'rainfall variability'
    else:
        print(f'Current varname: {varname}, no matched variable!')
    return title_varname


def get_alpha_label(i, with_parenthesis=True):

    result = ''
    idx = i
    while idx >= 0:
        result = chr(97 + (idx % 26)) + result
        idx = idx // 26 - 1
    
    if with_parenthesis:
        result = f'({result})'

    return result


def format_tick(value, decimal=1):
    if abs(value) < 0.0001:
        return '0'
    elif abs(value - round(value)) < 0.0001:
        return f'{int(round(value))}'
    else:
        format_map = {0: f'{value:.0f}', 1: f'{value:.1f}', 
                      2: f'{value:.2f}', 3: f'{value:.3f}'}
        return format_map.get(decimal, f'{value:.4f}')

