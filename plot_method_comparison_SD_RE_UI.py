# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np
import time
import os


# function to calculate UI, RE, mean, sd
def cal_stats(arr, Rmax):
    arr = np.array(arr, dtype=float)
    m = len(arr)
    q = 1 / m
    mean_val = np.nanmean(arr)
    std_val = np.nanstd(arr)
    total = np.nansum(arr)
    pi = arr / total
    RE = np.nansum(np.where(pi > 0, pi * np.log2(pi / q), 0))
    UI = RE * total / Rmax

    return mean_val, std_val, RE, UI


# function to plot comparison of SD method
def plot_compare(data, key):
    # cal stats
    mean_ls = []
    std_ls = []
    re_ls = []
    ui_ls = []
    Rmax = np.max(np.sum(data, axis=1))
    for i in range(len(data)):
        mean_val, std_val, RE, UI = cal_stats(data[i], Rmax)
        mean_ls.append(mean_val)
        std_ls.append(std_val)
        re_ls.append(RE)
        ui_ls.append(UI)

    # plot bar
    MONTH = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    x = np.arange(len(MONTH))
    width = 0.2
    if key == 'SD':
        center = [-3 * width / 2, -width / 2, width / 2, 3 * width / 2]
        labels = ['A/t0', 'B/t1', 'C/t3', 'D/t4']
        CLR = ['#EAB080', '#7C9D97', '#9CB0C3', '#C9C9C9']
    else:
        center = [-width / 2, width / 2]
        labels = ['A', 'B']
        CLR = ['#EAB080', '#9CB0C3']
    fig, ax = plt.subplots(figsize=(12, 6))
    for i in range(len(data)):
        ax.bar(x + center[i], data[i], width, label=labels[i], color=CLR[i], alpha=0.8)
        if key == 'SD':
            text = f"{labels[i]}: Mean = {mean_ls[i]:.2f} mm, SD = {std_ls[i]:.2f} mm"
        elif key == 'SD_RE':
            text = f"{labels[i]}: Mean = {mean_ls[i]:.2f} mm, SD = {std_ls[i]:.2f} mm, RE = {re_ls[i]:.4f}"
        elif key == 'RE_UI':
            text = f"{labels[i]}: RE = {re_ls[i]:.2f}, UI = {ui_ls[i]:.2f}"
        ax.text(0.01, 0.97 - 0.04 * i, text, transform=ax.transAxes, color=CLR[i],
                ha='left', va='top', weight='bold', alpha=0.8)
    ax.set_ylabel("Precipitation (mm)")
    ymax = np.max(np.max(data)) *1.4
    ax.set_ylim(0, ymax)
    ax.set_xlim(-0.5, 11.5)
    ax.set_xlabel("Month")
    ax.set_xticks(x)
    ax.set_xticklabels(MONTH)
    ax.legend(ncols=1, loc='upper right', frameon=False)

    # save result
    outpath = rf'../fig/method_comparison_{key}.png'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'Saving {outpath}')

    return


def main():
    # plot comparison of SD method
    data1 = [30, 40, 50, 30, 40, 50, 30, 40, 50, 30, 40, 50]
    data2 = [32.4, 43.2, 54.0, 32.4, 43.2, 54.0, 32.4, 43.2, 54.0, 32.4, 43.2, 54.0]
    data3 = [29.2, 40, 50.8, 29.2, 40, 50.8, 29.2, 40, 50.8, 29.2, 40, 50.8]
    data4 = [29.4, 40, 51.0, 29.4, 40, 51.0, 29.4, 40, 51.0, 29.4, 40, 51.0]
    data = np.array([data1, data2, data3, data4])
    plot_compare(data, 'SD')

    # plot comparison between SD and RE method
    data1 = [40, 50, 60, 40, 50, 60, 40, 50, 60, 40, 50, 60]
    data2 = [50, 50, 30, 50, 50, 50, 50, 50, 70, 50, 50, 50]
    data = np.array([data1, data2])
    plot_compare(data, 'SD_RE')

    # plot comparison between RE and UI method
    data1 = [0, 0, 50, 0, 0, 0, 0, 0, 50, 0, 0, 0]
    data2 = [0, 0, 100, 0, 0, 0, 0, 0, 100, 0, 0, 0]
    data = np.array([data1, data2])
    plot_compare(data, 'RE_UI')

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