# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np
import os
import time
from plot_mean_trend_isd import add_fignum
from plot_method_comparison_SD_RE_UI import cal_stats


# function to generate 12 hypothetical precipitation distribution (3 monthly and 9 daily)
def generate_prcp_distribution():
    monthly_prcp = {}
    daily_prcp = {}

    # 3 monthly distribution
    # 1) uniform, each month equal to 90 mm
    monthly_prcp['u'] = [90] * 12
    # 2) concentrate, August 1080 mm, other month 0 mm
    monthly_prcp['con'] = [0] * 12
    monthly_prcp['con'][7] = 1080
    # 3) cycle, 60, 90, and 120 mm repeated for 4 cycles
    cycle_pattern = [60, 90, 120]
    monthly_prcp['cyc'] = []
    for _ in range(4):
        monthly_prcp['cyc'].extend(cycle_pattern)

    #  9 daily distribution
    # based on uniform monthly distribution
    # 4) uniform_un, uniform monthly distribution, then allocated equally to each day within each month
    # i.e., each day equal to 3 mm (total 360 days)
    daily_prcp['u_u'] = [3] * 360
    # 5) uniform_con, uniform monthly distribution, then allocated only in one day (90 mm) within each month
    daily_prcp['u_con'] = [0] * 360
    for i in range(12):
        daily_prcp['u_con'][i * 30 + 14] = 90
    # 6) uniform_cyc, uniform monthly distribution, then allocated repeatedly in a cycle of 1, 3, 5 mm within each month
    cycle_pattern = [1, 3, 5]
    daily_prcp['u_cyc'] = []
    for _ in range(120):
        daily_prcp['u_cyc'].extend(cycle_pattern)
    # based on concentrated monthly distribution
    # 7) concentrate_un, concentrated monthly distribution, then allocated equally to each day in August
    daily_prcp['con_u'] = [0] * 360
    for i in range(30):
        daily_prcp['con_u'][7 * 30 + i] = 36
    # 8) concentrate_con, concentrated monthly distribution, then allocated only in one day (1080 mm) in August
    daily_prcp['con_con'] = [0] * 360
    daily_prcp['con_con'][7 * 30 + 14] = 1080
    # 9) concentrate_cyc, concentrated monthly distribution,
    # then allocated repeatedly in a cycle of 24, 36, 48 mm in August
    daily_prcp['con_cyc'] = [0] * 360
    cycle_pattern = [24, 36, 48]
    for i in range(30):
        idx = i % 3
        daily_prcp['con_cyc'][7 * 30 + i] = cycle_pattern[idx]
    # based on cycle monthly distribution
    # 10) cycle_un, cycle monthly distribution, then allocated equally to each day within each month
    daily_prcp['cyc_u'] = []
    for val in monthly_prcp['cyc']:
        daily_prcp['cyc_u'].extend([val / 30] * 30)
    # 11) cycle_con, cycle monthly distribution, then allocated only in one day within each month
    daily_prcp['cyc_con'] = [0] * 360
    for i in range(12):
        daily_prcp['cyc_con'][i * 30 + 14] = monthly_prcp['cyc'][i]
    # 12) cycle_cyc, cycle monthly distribution, then allocated repeatedly in a cycle within each month
    daily_prcp['cyc_cyc'] = []
    patterns = [[0, 2, 4], [1, 3, 5], [2, 4, 6]]
    for i in range(12):
        pattern_idx = (i % 3)
        current_pattern = patterns[pattern_idx]
        for _ in range(10):
            daily_prcp['cyc_cyc'].extend(current_pattern)

    return monthly_prcp, daily_prcp


# function to plot daily precipitation distribution
def plot_daily_prcp_distribution(axname, daily_prcp, fignum):
    # plot
    x = np.arange(1, 361)
    axname.plot(x, daily_prcp, color="#9CB0C3", linewidth=1, alpha=0.8)
    # add refline
    for i in range(30, 360, 30):
        axname.axvline(i, color="gray", linestyle="--", linewidth=0.5, alpha=0.5)
    axname.set_xlim(0, 361)
    axname.set_ylabel("Precipitation (mm)")
    axname.set_xlabel("Day of year")
    axname.set_xticks([])
    add_fignum(axname, fignum)

    return


# function to plot monthly precipitation distribution
def plot_monthly_prcp_distribution(axname, monthly_prcp, fignum):
    # plot
    x = np.arange(1, 13)
    axname.bar(x, monthly_prcp, width=0.5, color="#9CB0C3", alpha=0.8)
    axname.set_xlim(0, 13)
    axname.set_ylabel("Precipitation (mm)")
    axname.set_xlabel('')
    axname.set_xticks(x)
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    axname.set_xticklabels(months)
    add_fignum(axname, fignum)

    return


# function to plot combined figure of daily and monthly precipitation distribution
def plot_combined_prcp_distribution(monthly_prcp, daily_prcp):
    monthly_keys = ['u', 'con', 'cyc']
    monthly_fignums = ['(a) uM', '(b) conM', '(c) cycM']
    daily_keys = ['u_u', 'u_con', 'u_cyc', 'con_u', 'con_con', 'con_cyc', 'cyc_u', 'cyc_con', 'cyc_cyc']
    daily_fignums = ['(d) uM and uD', '(e) uM and conD', '(f) uM and cycD',
                     '(g) conM and uD', '(h) conM and conD', '(i) conM and cycD',
                     '(j) cycM and uD', '(k) cycM and conD', '(l) cycM and cycD']
    fig, axes = plt.subplots(4, 3, figsize=(18, 12))
    plt.subplots_adjust(
        left=0.09,
        right=0.98,
        top=0.97,
        bottom=0.04,
        hspace=0.22,
        wspace=0.15
    )
    for i in range(12):
        axname = axes[i//3, i%3]
        if i <= 2:
            # mothly
            plot_monthly_prcp_distribution(axname, monthly_prcp[monthly_keys[i]], monthly_fignums[i])
        else:
            # daily scale
            plot_daily_prcp_distribution(axname, daily_prcp[daily_keys[i-3]], daily_fignums[i-3])

    # save result
    outpath = r'../fig/method_comparison_daily_monthly_prcp_distribution.png'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'Saving {outpath}')

    return


# function to plot daily and monthly precipitation RE
def plot_combined_RE(monthly_prcp, daily_prcp):
    # cal stats
    monthly_re = []
    daily_re = []
    monthly_keys = ['u', 'con', 'cyc']
    daily_keys = ['u_u', 'u_con', 'u_cyc', 'con_u', 'con_con', 'con_cyc', 'cyc_u', 'cyc_con', 'cyc_cyc']
    Rmax = 1080
    for key in monthly_keys:
        prcp = monthly_prcp[key]
        _, _, RE, _ = cal_stats(prcp, Rmax)
        monthly_re.append(RE)
    for key in daily_keys:
        prcp = daily_prcp[key]
        _, _, RE, _ = cal_stats(prcp, Rmax)
        daily_re.append(RE)
    re_ls = [daily_re, monthly_re]

    # plot
    fig = plt.figure(figsize=(12, 6), dpi=300)
    grid = GridSpec(1, 4, figure=fig, left=0.07, bottom=0.07, right=0.91, top=0.97, wspace=0, hspace=0)
    ax1 = plt.subplot(grid[0, 0:3])
    ax2 = plt.subplot(grid[0, 3])
    ax_ls = [ax1, ax2]
    colors = ['#9CB0C3', '#EAB080']
    fignums = ['(a) Daily (D)', '(b) Monthly (M)']
    width = 0.5
    for i in range(len(re_ls)):
        axname = ax_ls[i]
        prcp = re_ls[i]
        x = np.arange(1, len(prcp) + 1)
        axname.bar(x, prcp, width=width, color=colors[i])
        for j in range(len(prcp)):
            axname.text(j+1, prcp[j], f'{prcp[j]:.2f}', va='bottom', ha='center')
        axname.set_xlim(0.5, len(prcp)+0.5)

    # add legend annotations to ax1
    pattern_labels = [
        '1: uM and uD', '2: uM and conD', '3: uM and cycD',
        '4: conM and uD', '5: conM and conD', '6: conM and cycD',
        '7: cycM and uD', '8: cycM and conD', '9: cycM and cycD'
    ]
    ax1.text(0.6, 6.5, '\n'.join(pattern_labels), va='bottom', ha='left')
    ax1.set_ylabel('Relative entropy (RE)')
    add_fignum(ax1, fignums[0])
    # adjust ax2 ylim
    ylim = ax1.get_ylim()
    ax2.set_ylim(ylim[0], ylim[1])
    add_fignum(ax2, fignums[1])
    ax2.set_yticks([])
    ax2.set_xticks([1, 2, 3])
    ax2.set_xticklabels(['U', 'Con', 'Cyc'])

    #save result
    outpath = r'../fig/method_comparison_daily_monthly_prcp_RE.png'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'Saving {outpath}')

    return


def main():
    # plot daily and monthly prcp distribution
    monthly_prcp, daily_prcp = generate_prcp_distribution()
    plot_combined_prcp_distribution(monthly_prcp, daily_prcp)

    # plot daily and monthly prcp RE
    plot_combined_RE(monthly_prcp, daily_prcp)

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