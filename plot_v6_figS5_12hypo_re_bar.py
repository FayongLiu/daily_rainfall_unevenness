# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import numpy as np

#Generate daily rainfall by combining three monthly patterns (uniform/concentrated/cyclical) with three daily patterns, producing nine distinct datasets.

#step1
def generate_dictionaries():

    monthly = {}
    daily = {}
    
    # Generate a list of monthly dictionaries
    # uniform??: 12 numbers, each equal to ??90
    monthly['uniform'] = [90] * 12
    
    # concencret: 12 numbers, with only the 8th being 1080 and the rest 0?
    monthly['concencret'] = [0] * 12
    monthly['concencret'][7] = 1080 
    
    # cycle: 60, 90, 120 repeated in 4 cycles (totaling 12 numbers)?
    cycle_pattern = [60, 90, 120]
    monthly['cycle'] = []
    for _ in range(4):
        monthly['cycle'].extend(cycle_pattern)
    
    # Generate a list of daily dictionaries
    # uniform_un:  ??360 numbers, each being 3?
    daily['uniform_un'] = [3] * 360
    
    # uniform_con:360 numbers, with only 12 being 90 (evenly distributed) and the rest 0?
    daily['uniform_con'] = [0] * 360
    for i in range(12):
        daily['uniform_con'][i * 30+14] = 90  
    
    # uniform_cyc:360 numbers, grouped in cycles of 3 (repeating 1, 3, 5)?
    cycle_pattern = [1, 3, 5]
    daily['uniform_cyc'] = []
    for _ in range(120):  
        daily['uniform_cyc'].extend(cycle_pattern)
    
    # concencret_un: 360 numbers, grouped in 30s; only the 8th group has all numbers as 36, the rest 0?
    daily['concencret_un'] = [0] * 360
    for i in range(30):
        daily['concencret_un'][7*30 + i] = 36  
    
    # concencret_con: ?A mix of concencret_un and uniform_con
    daily['concencret_con'] = [0] * 360
    # the 15th number in the 8th group is 1080, the rest 0?
    daily['concencret_con'][7*30 + 14] = 1080  
    
    # concencret_cyc: A mix of concencret_un and uniform_cyc
    daily['concencret_cyc'] = [0] * 360
    cycle_pattern = [1, 3, 5]
    for i in range(30):
        idx = i % 3  
        daily['concencret_cyc'][7*30 + i] = cycle_pattern[idx]  #the 8th group follows a cyclic pattern?
    
    # Based on monthly['cycle']
    daily['cycle_un'] = []
    for val in monthly['cycle']:
        daily['cycle_un'].extend([val/30] * 30)  # each monthly value is divided by 30, then repeated 30 times?
    
    # cycle_con: A mix of monthly['cycle'] and uniform_con
    daily['cycle_con'] = [0] * 360
    for i in range(12):
        daily['cycle_con'][i*30 + 14] = monthly['cycle'][i]  # he first position in each group uses the monthly value?
    
    # cycle_cyc: ??12 groups (30 numbers each), with 3-group cycles
    daily['cycle_cyc'] = []
    patterns = [[0, 2, 4], [1, 3, 5], [2, 4, 6]]
    for i in range(12):
        pattern_idx = (i % 3)  
        current_pattern = patterns[pattern_idx]
        for _ in range(10):  # internally, each group cycles 3 numbers (repeated 10 times per group)?
            daily['cycle_cyc'].extend(current_pattern)
    
    return monthly, daily
    
#step2
def calculate_values(monthly, daily):


    monthly_d = {}
    daily_d = {}
    monthly_s = {}
    daily_s = {}
    
    # Calculate the D value for each list in the monthly dictionary
    for key, values in monthly.items():
        # Calculate the total sum R
        R = sum(values)
        R_max = R
        
        if R > 0:  # Avoid division by zero
            # Calculate the average proportion q.
            m = len(values)  # Number of elements.
            q = 1 / m  # Average proportion.
            
            # Calculate the proportion for each element
            pi_values = [val / R for val in values]
            
            # Calculate the D value
            D = 0
            for pi in pi_values:
                if pi > 0:  # Only calculate cases where pi > 0.
                    D += pi * np.log2(pi / q)
            monthly_d[key + "_d"] = D
            monthly_s[key + "_s"] = D * R / R_max
        else:
            monthly_d[key + "_d"] = np.nan
            monthly_s[key + "_s"] = np.nan
    
    # Calculate the D value for each list in the daily dictionary.
    for key, values in daily.items():
        R = sum(values)
        R_max = R        
        if R > 0:  
            m = len(values)  
            q = 1 / m 
            pi_values = [val / R for val in values]
            D = 0
            for pi in pi_values:
                if pi > 0:  
                    D += pi * np.log2(pi / q)
            daily_d[key + "_d"] = D
            daily_s[key + "_s"] = D * R / R_max
        else:
            daily_d[key + "_d"] = np.nan
            daily_s[key + "_s"] = np.nan
    
    return monthly_d, daily_d, monthly_s, daily_s
    
#step3
def plot_s_values(monthly_s, daily_s):

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 6), 
                              gridspec_kw={'width_ratios': [8, 3]}, 
                              sharey=True)
    color = ['#9CB0C3','#EAB080']
    
    # Calculate the actual identical bar width for both subplots.
    width_daily = 0.3  
    width_monthly = width_daily * 2/3  

    
    # Daily data
    x1 = np.arange(9)

    daily_data = [
        daily_s['uniform_un_s'],
        daily_s['uniform_con_s'],
        daily_s['uniform_cyc_s'],
        daily_s['concencret_un_s'],
        daily_s['concencret_con_s'],
        daily_s['concencret_cyc_s'],
        daily_s['cycle_un_s'],
        daily_s['cycle_con_s'],
        daily_s['cycle_cyc_s']
    ]
    rects1 = ax1.bar(x1, daily_data, width_daily, color=color[0])
    
    # Monthly data
    x2 = np.arange(3)
    monthly_data = [
        monthly_s['uniform_s'],
        monthly_s['concencret_s'],
        monthly_s['cycle_s']
    ]
    rects2 = ax2.bar(x2, monthly_data, width_monthly, color=color[1])
    for rect in rects1:
        height = rect.get_height()
        ax1.text(rect.get_x() + rect.get_width()/2., height,
                f'{height:.3g}',
                ha='center', va='bottom')
    
    for rect in rects2:
        height = rect.get_height()
        ax2.text(rect.get_x() + rect.get_width()/2., height,
                f'{height:.3g}',
                ha='center', va='bottom')
    
    # Configure the Daily subplot.
    ax1.set_ylabel('Relative entropy (RE) values')
    ax1.set_xticks(x1)
    ax1.set_xticklabels(range(1, 10))
    #ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.set_xlim(-0.5, 9.0)  
     


    
    # Configure the Monthly subplot.
    ax2.set_xticks(x2)
    ax2.set_xticklabels(['U', 'Con', 'Cyc'])
    #ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.set_ylabel('') 
    ax2.set_xlim(-0.5, 2.4)  

    
    # Adjust the spacing between subplots.
    plt.subplots_adjust(wspace=0, left=0.1, right=0.9)

    # Get the x-axis and y-axis ranges for both subplots.
    x_min1, x_max1 = ax1.get_xlim()
    x_min2, x_max2 = ax2.get_xlim()
    y_min1, y_max1 = ax1.get_ylim()
    y_min2, y_max2 = ax2.get_ylim()
    # Add titles in the top-left corner of each respective subplot.
    ax1.text(x_min1, y_max1 * 1.02, '(a) Daily (D)', 
             fontweight='bold', fontsize=12,
             horizontalalignment='left',  
             verticalalignment='bottom') 

    ax2.text(x_min2, y_max2 * 1.02, '(b) Monthly (M)', 
             fontweight='bold', fontsize=12,
             horizontalalignment='left',  
             verticalalignment='bottom')  

    
    # Add legend annotations.
    pattern_labels = [
        '1: uM and uD', '2: uM and conD', '3: uM and cycD',
        '4: conM and uD', '5: conM and conD', '6: conM and cycD',
        '7: cycM and uD', '8: cycM and conD', '9: cycM and cycD'
    ]
    fig.text(0.115, 0.62, '\n'.join(pattern_labels),
             verticalalignment='bottom',
             bbox=dict(boxstyle='round',facecolor='none', edgecolor='none',alpha=1))
    

    plt.savefig("/data1/yyzhao/data/1980-2020/finally_result/picture/v2_figS1_hypothesis_two_subplot_s.png", dpi=300)
    plt.close()
# Call the function.
monthly, daily = generate_dictionaries()
monthly_d, daily_d, monthly_s, daily_s = calculate_values(monthly, daily)
plot_s_values(monthly_s, daily_s)