# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt


a = [30, 40, 50, 30, 40, 50, 30, 40, 50, 30, 40, 50]
b = [32.4, 43.2, 54.0, 32.4, 43.2, 54.0, 32.4, 43.2, 54.0, 32.4, 43.2, 54.0]

c = [29.2, 40, 50.8, 29.2, 40, 50.8, 29.2, 40, 50.8, 29.2, 40, 50.8]
d = [29.4, 40, 51.0, 29.4, 40, 51.0, 29.4, 40, 51.0, 29.4, 40, 51.0]

# 计算统计量
mean_a = np.nanmean(a)
std_a = np.nanstd(a)

mean_b = np.nanmean(b)
std_b = np.nanstd(b)

mean_c = np.nanmean(c)
std_c = np.nanstd(c)

mean_d = np.nanmean(d)
std_d = np.nanstd(d)


# x轴标签（12个月英文简写）
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

x = np.arange(len(months))
width = 0.18  
group_scale = 0.8 

colors = ['#D6D6D6', '#9CB0C3', '#7C9D97', '#EAB080']
labels = ['A/t0', 'B/t1','C/t3', 'D/t4']

# y轴最大值
ymax = max(max(a), max(b), max(c), max(d)) * 1.4

fig, ax = plt.subplots(figsize=(12, 6))

# 绘制柱状图
rects1 = ax.bar(x - 1.5*width, a, width, label=labels[0], color=colors[0])
rects2 = ax.bar(x - 0.5*width, b, width, label=labels[1], color=colors[1])
rects3 = ax.bar(x + 0.5*width, c, width, label=labels[2], color=colors[2])
rects4 = ax.bar(x + 1.5*width, d, width, label=labels[3], color=colors[3])

# y轴设置
ax.set_ylabel("Precipitation (mm)")
ax.set_ylim(0, ymax)
ax.set_xlabel("Month")
ax.set_xticks(x)
ax.set_xticklabels(months)
ax.legend(frameon=False)

# 添加文字标签
text_a = (f"A/t0: Mean = {mean_a:.2f} mm, SD = {std_a:.2f} mm")
text_b = (f"B/t1: Mean = {mean_b:.2f} mm, SD = {std_b:.2f} mm")
text_c = (f"C/t3: Mean = {mean_c:.2f} mm, SD = {std_c:.2f} mm")
text_d = (f"D/t4: Mean = {mean_d:.2f} mm, SD = {std_d:.2f} mm")

# 在图中放置标签
ax.text(0.05, 0.96, text_a, transform=ax.transAxes, 
        fontsize=11, color=colors[0], ha='left', va='top', 
        weight='bold')  # bold 只加在文字整体
ax.text(0.05, 0.91, text_b, transform=ax.transAxes, 
          fontsize=11, color=colors[1], ha='left', va='top', 
        weight='bold')
ax.text(0.05, 0.86, text_c, transform=ax.transAxes, 
        fontsize=11, color=colors[2], ha='left', va='top', 
        weight='bold')  # bold 只加在文字整体
ax.text(0.05, 0.81, text_d, transform=ax.transAxes, 
          fontsize=11, color=colors[3], ha='left', va='top', 
        weight='bold')

plt.savefig("/data1/yyzhao/code/figure_fayong.png",
        dpi=300, bbox_inches='tight')
plt.close()

print("ok save")    