# Daily rainfall unevenness
Codes for evaluating historical daily rainfall unevenness.
## 1. Create virtual Python environment
Use following command to create a new virtual Python environment (or you can also use your own environment):
```bash
conda env create -f environment.yml
```
Then activate the new enviroment:
```bash
conda activate rainfall
```
## 2. Preparation
Prepare the data according to the **Data availability statement** in the paper.
After preparing the data, please revise the data paths in the code before running.
## 3. Step by step
### 3.1. Navigate to the directory where the code folder is located
```bash
cd /your/own/code/path/
```
### 3.2. Ensure that your virtual Python environment is activated
```bash
conda activate rainfall   # or use your own environment
```
### 3.3. Preprocess
#### 1) Select valid ISD stations
Running time was estimated for 21 years (2000–2020):
```bash
python pre_isd_select_valid_station.py    # ~ 2 min
```
Here, you can also change the criterion for defining what is a “valid station”.
#### 2) Concatenate valid-station data across years
Concatenate the data of each valid station in different years (multiple .csv files) into a single .csv file:
```bash
python pre_isd_concat_valid_station.py    # ~ 5 s
```
#### 3) Select valid stations in Chinese Station Data
```bash
python pre_ChinaSD_select_valid_station.py    # ~ 3 s
```
#### 4) Aggregate hourly grid-based data to daily scale
```bash
python pre_ERA5_Land_hourly2daily_prcp.py
# or
sbatch pre_CRU_JRA_hourly2daily_prcp.sh       # time-consuming
```
#### 5) Calculate maximum annual precipitation (Rmax)
Calculate maximum annual precipitation (Rmax) across all years for each grid in each grid-based dataset:
```bash
python pre_GRID_cal_maximum_annual_prcp.py
# or
sbatch pre_GRID_cal_maximum_annual_prcp.sh    # ~ 20 min
```
### 3.4. Calculation
#### 1) Station-based indices
Calculate Rmax, UI, RE, and R/Rmax for stations, as well as their multi-year averages and trends:
```bash
python cal_d_s_r_mean_trend_isd.py    # ~ 30 s
```
#### 2) Yearly grid-based indices
Calculate UI, RE, and R/Rmax for each grid-based dataset for each year:
```bash
python cal_d_s_r_each_year_GRID.py
# or
sbatch cal_d_s_r_each_year_GRID.sh    # ~ 40 min
```
#### 3) Global multi-year averages and trends
Calculate multi-year averages and trends of UI, RE, and R/Rmax for each grid-based dataset at the global scale:
```bash
python cal_d_s_r_mean_trend_global_GRID.py    # ~ 20 min
```
#### 4) Grid-scale multi-year averages and trends
Calculate multi-year averages and trends of UI, RE, and R/Rmax for each grid-based dataset at the grid scale:
```bash
python cal_d_s_r_mean_trend_grid_GRID.py
# or
sbatch cal_d_s_r_mean_trend_grid_GRID.sh      # ~ 13 min
```
#### 5) CMIP6 ensemble averages
Calculate averages of all CMIP6 models:
```bash
python cal_d_s_r_mean_trend_CMIP6_ensembles.py    # ~ 1 s
```
#### 6) Percentages of significant changes
Calculate grid/area percentages with significant changes for each dataset:
```bash
python cal_stats_significant_changes.py           # ~ 1 s
```
### 3.5. Visualization
#### 1) Method comparison: SD, RE, and UI
```bash
python plot_method_comparison_SD_RE_UI.py         # ~ 1 s
```
#### 2) Method comparison: daily vs monthly RE
```bash
python plot_method_comparison_daily_monthly_RE.py # ~ 1 s
```
#### 3) Station data: mean and trend
```bash
python plot_mean_trend_isd.py                     # ~ 2 s
```
#### 4) Grid-based data: mean and trend
```bash
python plot_mean_trend_GRID.py                    # ~ 4 min
```
#### 5) Each CMIP6 model: mean and trend
```bash
python plot_mean_trend_each_CMIP6.py              # ~ 1 min
```
#### 6) Percentages of significant changes
```bash
python plot_stats_significant_changes.py          # ~ 1 s
```
## 4. Contact
If you have any questions, find bugs, or have suggestions for improving the codes, please feel free to open an issue in this repository or contact: Fayong Liu (<liufayong3375@igsnrr.ac.cn>).
