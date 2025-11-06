# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np

#step1
def generate_dictionaries():

    monthly = {}
    daily = {}
    
    # Generate a list of monthly dictionaries
    # 1：uniform??: 12 numbers, each equal to ??90
    monthly['uniform'] = [90] * 12
    
    # 2：concencret: 12 numbers, with only the 8th being 1080 and the rest 0?
    monthly['concencret'] = [0] * 12
    monthly['concencret'][7] = 1080 
    
    # 3：cycle: 60, 90, 120 repeated in 4 cycles (totaling 12 numbers)?
    cycle_pattern = [60, 90, 120]
    monthly['cycle'] = []
    for _ in range(4):
        monthly['cycle'].extend(cycle_pattern)
    
    # 4：Generate a list of daily dictionaries
    # uniform_un:  ??360 numbers, each being 3?
    daily['uniform_un'] = [3] * 360
    
    # 5：uniform_con:360 numbers, with only 12 being 90 (evenly distributed) and the rest 0?
    daily['uniform_con'] = [0] * 360
    for i in range(12):
        daily['uniform_con'][i * 30+14] = 90  
    
    # 6：uniform_cyc:360 numbers, grouped in cycles of 3 (repeating 1, 3, 5)?
    cycle_pattern = [1, 3, 5]
    daily['uniform_cyc'] = []
    for _ in range(120):  
        daily['uniform_cyc'].extend(cycle_pattern)
    
    # 7：concencret_un: 360 numbers, grouped in 30s; only the 8th group has all numbers as 36, the rest 0?
    daily['concencret_un'] = [0] * 360
    for i in range(30):
        daily['concencret_un'][7*30 + i] = 36  
    
    # 8：concencret_con: ?A mix of concencret_un and uniform_con
    daily['concencret_con'] = [0] * 360
    # the 15th number in the 8th group is 1080, the rest 0?
    daily['concencret_con'][7*30 + 14] = 1080  
    
    # 9：concencret_cyc: A mix of concencret_un and uniform_cyc
    daily['concencret_cyc'] = [0] * 360
    cycle_pattern = [1, 3, 5]
    for i in range(30):
        idx = i % 3  
        daily['concencret_cyc'][7*30 + i] = cycle_pattern[idx]  #the 8th group follows a cyclic pattern?
    
    # 10：Based on monthly['cycle']
    daily['cycle_un'] = []
    for val in monthly['cycle']:
        daily['cycle_un'].extend([val/30] * 30)  # each monthly value is divided by 30, then repeated 30 times?
    
    # 11：cycle_con: A mix of monthly['cycle'] and uniform_con
    daily['cycle_con'] = [0] * 360
    for i in range(12):
        daily['cycle_con'][i*30 + 14] = monthly['cycle'][i]  # he first position in each group uses the monthly value?
    
    # 12：cycle_cyc: ??12 groups (30 numbers each), with 3-group cycles
    daily['cycle_cyc'] = []
    patterns = [[0, 2, 4], [1, 3, 5], [2, 4, 6]]
    for i in range(12):
        pattern_idx = (i % 3)  
        current_pattern = patterns[pattern_idx]
        for _ in range(10):  # internally, each group cycles 3 numbers (repeated 10 times per group)?
            daily['cycle_cyc'].extend(current_pattern)
    
    return monthly, daily

# === 折线图绘制函数 ===
def plot_daily_with_annotations(ax, x, values, title, label_letter):
    ax.plot(x, values, color="#9CB0C3", linewidth=1.5)
    
    # 添加每月分界虚线
    for i in range(30, 360, 30):
        ax.axvline(i, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)

    # 动态设置y轴范围并放大
    y_min, y_max = np.min(values), np.max(values)
    y_range = y_max - y_min if y_max > y_min else 1
    ax.set_ylim(y_min - 0.2*y_range, y_max + 0.3*y_range)
    
    # === 智能标注逻辑 ===
    last_labeled_index = -999
    min_gap = 30  # 不同数字标注之间的最小间隔
    labeled_values = set()  # 记录已经标注过的数字
    
    for i, v in enumerate(values):
        if v == 0:
            continue
    
        # 若这个值已标注过，跳过
        if v in labeled_values:
            continue
    
        # 若距离上一个标注点太近，跳过这次（寻找下一个符合条件的点）
        if (i - last_labeled_index) < min_gap:
            continue
    
        # 画出标注点
        ax.scatter(x[i], v, color="#EAB080", s=7, alpha=0.84,zorder=3)
    
        # 标注数字
        ax.text(
            x[i], v + 0.05 * y_range, f"{v:.0f}",
            fontsize=12, fontweight='bold',
            color="#EAB080", ha='center', va='bottom'
        )
    
        # 更新记录
        labeled_values.add(v)
        last_labeled_index = i


    # 图标题
    ax.text(
        0.04, 1.05, f"({label_letter}) {title}",
        transform=ax.transAxes, fontsize=12,
        fontweight='bold', ha='left'
    )
    ax.set_ylabel("Precipitation (mm)")
    ax.set_xlabel("Day of year")
    ax.set_xticks([])


# === 主绘图函数 ===
def plot_rainfall_patterns(monthly, daily, outpath):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    monthly_keys  = ['uniform', 'concencret', 'cycle']
    monthly_titles = ['uM', 'conM', 'cycM']

    daily_keys_row2 = ['uniform_un', 'uniform_con', 'uniform_cyc']
    daily_titles_row2 = ['uM and uD', 'uM and conD', 'uM and cycD']

    daily_keys_row3 = ['concencret_un', 'concencret_con', 'concencret_cyc']
    daily_titles_row3 = ['conM and uD', 'conM and conD', 'conM and cycD']

    daily_keys_row4 = ['cycle_un', 'cycle_con', 'cycle_cyc']
    daily_titles_row4 = ['cycM and uD', 'cycM and conD', 'cycM and cycD']

    fig, axes = plt.subplots(4, 3, figsize=(18, 12))
    plt.subplots_adjust(hspace=0.35, wspace=0.2)

    # 第一行：月尺度柱状图
    for i, (key, title) in enumerate(zip(monthly_keys, monthly_titles)):
        ax = axes[0, i]
        values = monthly[key]
        x = np.arange(1, len(values) + 1)
        ax.bar(x, values, width=0.6, color="#9CB0C3")
        label = f"({chr(97 + i)}) "
        ax.text(0.04, 1.05, label + title, transform=ax.transAxes,
                fontsize=12, fontweight='bold', ha='left')
        ax.set_ylabel("Precipitation (mm)")
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45)

    # 第二~四行：日尺度折线图（带标注）
    for row_idx, (daily_keys, daily_titles, start_letter) in enumerate([
        (daily_keys_row2, daily_titles_row2, 100),  # b -> e
        (daily_keys_row3, daily_titles_row3, 103),  # e -> h
        (daily_keys_row4, daily_titles_row4, 106),  # h -> k
    ]):
        for i, (key, title) in enumerate(zip(daily_keys, daily_titles)):
            ax = axes[row_idx + 1, i]
            x = np.arange(1, 361)
            values = daily[key]
            label_letter = chr(start_letter + i - 3)
            plot_daily_with_annotations(ax, x, values, title, label_letter)

    plt.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close()


# === Run ===
outpath ="/data1/yyzhao/data/1980-2020/finally_result/picture/v5_figS2_12hypo_preci_bar_and_line.png"   

monthly, daily = generate_dictionaries()
plot_rainfall_patterns(monthly, daily, outpath)

print("ok")
        
    