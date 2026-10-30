# plot comparison of SD and DSI method
import matplotlib.pyplot as plt
import numpy as np
import time
import os


# function to calculate UI, R/Rmax,RE, mean, sd
def cal_stats(arr, Rmax):
    arr = np.array(arr, dtype=float)
    m = len(arr)
    q = 1 / m
    mean_val = np.nanmean(arr)
    std_val = np.nanstd(arr)
    total = np.nansum(arr)
    pi = arr / total
    RE = np.nansum(np.where(pi > 0, pi * np.log2(pi / q), 0))
    PRCP_ratio = total / Rmax
    UI = RE * PRCP_ratio

    return mean_val, std_val, RE, PRCP_ratio, UI


# function to plot comparison between SD and DSI method
def plot_compare(data):
    # cal stats
    mean_ls = []
    std_ls = []
    re_ls = []
    prcp_ratio_ls = []
    ui_ls = []
    Rmax = np.max(np.sum(data, axis=1))
    for i in range(len(data)):
        mean_val, std_val, RE, PRCP_ratio, UI = cal_stats(data[i], Rmax)
        mean_ls.append(mean_val)
        std_ls.append(std_val)
        re_ls.append(RE)
        prcp_ratio_ls.append(PRCP_ratio)
        ui_ls.append(UI)

    # plot bar
    MONTH = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    x = np.arange(len(MONTH))
    width = 0.2
    center = [-3*width/2, -width/2, width/2, 3*width/2]
    labels = ['S0', 'S1', 'S2', 'S3']
    CLR = ['#C9C9C9', '#9CB0C3', '#7C9D97', '#EAB080']
   
    fig, ax = plt.subplots(figsize=(12, 6))
    for i in range(len(data)):
        ax.bar(x + center[i], data[i], width, label=labels[i], color=CLR[i], alpha=0.8)
        text = f"{labels[i]}: SD={std_ls[i]:.3f} mm, $R$/$R$$_m$$_a$$_x$={prcp_ratio_ls[i]:.3f}, RE={re_ls[i]:.3f}, DSI={ui_ls[i]:.3f}"
        ax.text(0.01, 0.97 - 0.04 * i, text, transform=ax.transAxes, color=CLR[i],
                ha='left', va='top', weight='bold', alpha=0.8)
    ax.set_ylabel("Rainfall (mm)")
    ymax = np.max(np.max(data)) *1.4
    ax.set_ylim(0, ymax)
    ax.set_xlim(-0.5, 11.5)
    ax.set_xlabel("Month")
    ax.set_xticks(x)
    ax.set_xticklabels(MONTH)
    ax.legend(ncols=1, loc='upper right', frameon=False)

    # save result
    outpath = rf'../fig_v4/method_comparison_SD_DSI.png'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'Saving {outpath}')

    return


def main():
    data1 = [30, 40, 50, 30, 40, 50, 30, 40, 50, 30, 40, 50]
    data2 = [32.4, 43.2, 54.0, 32.4, 43.2, 54.0, 32.4, 43.2, 54.0, 32.4, 43.2, 54.0]
    data3 = [29.2, 40, 50.8, 29.2, 40, 50.8, 29.2, 40, 50.8, 29.2, 40, 50.8]
    data4 = [40, 40, 20, 40, 40, 40, 40, 40, 60, 40, 40, 40]
    data = np.array([data1, data2, data3, data4])
    plot_compare(data)

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