# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt

def calc_stats_RE(lis):
    Rmax = 600
    lis = np.array(lis, dtype=float)
    m = len(lis)
    q = 1 / m
    mean_val = np.nanmean(lis)
    std_val = np.nanstd(lis)  # 默认 ddof=0
    total = np.nansum(lis)
    pi = lis / total
    RE = np.nansum(np.where(pi > 0, pi * np.log2(pi / q), 0))
    DSI = RE * total/Rmax
        
    return mean_val, std_val, RE, DSI

def plot_A_B(a, b):
    # 计算统计量
    mean_a, std_a, RE_a, _ = calc_stats_RE(a)
    mean_b, std_b, RE_b, _ = calc_stats_RE(b)
    
    # x轴标签（12个月英文简写）
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    x = np.arange(len(months))  # 12个位置
    width = 0.25  # 柱子宽度
    
    colors = ['#9CB0C3', '#EAB080']
    labels = ['A', 'B']
    
    # y轴最大值
    ymax = max(max(a), max(b)) * 1.2
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 绘制柱状图
    rects1 = ax.bar(x - width/2, a, width, label='A', color=colors[0])
    rects2 = ax.bar(x + width/2, b, width, label='B', color=colors[1])
    
    # y轴设置
    ax.set_ylabel("Precipitation (mm)")
    ax.set_ylim(0, ymax)
    ax.set_xlabel("Month")
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.legend(frameon=False)
    
    # 添加文字标签
    text_a = (f"A: Mean = {mean_a:.2f} mm, SD = {std_a:.2f} mm, RE = {RE_a:.4f}")
    text_b = (f"B: Mean = {mean_b:.2f} mm, SD = {std_b:.2f} mm, RE = {RE_b:.4f}")
    
    # 在图中放置标签
    ax.text(0.1, 0.92, text_a, transform=ax.transAxes, 
            fontsize=11, color=colors[0], ha='left', va='top', 
            weight='bold')  # bold 只加在文字整体
    ax.text(0.1, 0.85, text_b, transform=ax.transAxes, 
              fontsize=11, color=colors[1], ha='left', va='top', 
            weight='bold')

    plt.savefig("/data1/yyzhao/data/1980-2020/finally_result/picture/v5_figS1_sd_re_hypo.png",
            dpi=300, bbox_inches='tight')
    plt.close()

def plot_C_D(c, d):
    # 计算统计量
    mean_c, std_c, RE_c, DSI_c = calc_stats_RE(c)
    mean_d, std_d, RE_d, DSI_d = calc_stats_RE(d)
    
    # x轴标签（12个月英文简写）
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    x = np.arange(len(months))  # 12个位置
    width = 0.25  # 柱子宽度
    
    colors = ['#9CB0C3', '#EAB080']
    labels = ['A', 'B']
    
    # y轴最大值
    ymax = max(max(c), max(d)) * 1.4
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 绘制柱状图
    rects1 = ax.bar(x - width/2, c, width, label='A', color=colors[0])
    rects2 = ax.bar(x + width/2, d, width, label='B', color=colors[1])
    
    # y轴设置
    ax.set_ylabel("Precipitation (mm)")
    ax.set_ylim(0, ymax)
    ax.set_xlabel("Month")
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.legend(frameon=False)
    
    # 添加文字标签
    text_c = (f"A: RE = {RE_c:.2f}, UI = {DSI_c:.2f}")
    text_d = (f"B: RE = {RE_d:.2f}, UI = {DSI_d:.2f}")
    
    # 在图中放置标签
    ax.text(0.1, 0.93, text_c, transform=ax.transAxes, 
            fontsize=11, color=colors[0], ha='left', va='top', 
            weight='bold')  # bold 只加在文字整体
    ax.text(0.1, 0.85, text_d, transform=ax.transAxes, 
              fontsize=11, color=colors[1], ha='left', va='top', 
            weight='bold')

    plt.savefig("/data1/yyzhao/data/1980-2020/finally_result/picture/v5_figS4_re_ui_hypo.png",
            dpi=300, bbox_inches='tight')
    plt.close()
    
# 测试
a = [40,50,60,40,50,60,40,50,60,40,50,60]
b = [50,50,30,50,50,50,50,50,70,50,50,50]

#c = [3,6,9,12,15,18,21,24,27,30,33,36]
#d = [6,12,18,24,30,36,42,48,54,60,66,72]
c = [0,0,50,0,0,0,0,0,50,0,0,0]
d = [0,0,100,0,0,0,0,0,100,0,0,0]
plot_A_B(a, b)
plot_C_D(c, d)
print("ok save")    