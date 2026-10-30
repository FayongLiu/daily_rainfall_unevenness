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
Some data can be downloaded by python
```bash
# Examples
python download_data.py
```
After preparing the data, please replace the data paths in the codes before running.
These codes include '/rainfall_ui/util/data_info.py' and those you need to run as follows.
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
#### 1) Preprocessing station data, including ISD, GHCNd, CMA, and etc.
Here, you can also change the criteria for defining a "valid station."
The default criterion is START_YEAR = 1980, END_YEAR = 2020, and valid years >= 30 (TH_YEAR = 30).
```bash
# for example
python pre_station_select.py -s 1980 -e 2020 -th 30 # default
# for details
python pre_station_select.py --help
```
If you need to add more criteria, you will need to modify the code in '/rainfall_ui/preprocess/preprocess_station.py'.
```bash
python pre_station_select.py
# or
sbatch pre_station_select.sh
# Count valid stations for each dataset
python pre_station_count.py
# Examples to find out the duplicates from different data source, GHCNd as reference
python pre_station_duplicates.py
# Visualization for comparing time peries between different data source
python plot_vx_comparison_duplicates.py
```
#### 4) Aggregate hourly grid-based data to daily scale
```bash
python pre_GRID_daily_prcp.py
# or
sbatch pre_GRID_daily_prcp.sh
```
#### 5) Calculate maximum annual precipitation (Rmax)
Calculate maximum annual precipitation (Rmax) across all years for each grid in each grid-based dataset:
```bash
python pre_GRID_cal_maximum_annual_prcp.py
# or
sbatch pre_GRID_cal_maximum_annual_prcp.sh
```
### 3.4. Calculation
#### 1) Station-based indices
Calculate Rmax, UI, RE, R/Rmax, and Std for stations, as well as their multi-year averages and trends:
```bash
python cal_d_s_r_mean_trend_station.py
python cal_d_s_r_mean_trend_station2grid.py # to grid, 0.5 * 0.5 deg
```
#### 2) Yearly grid-based indices
Calculate UI, RE, and R/Rmax for each grid-based dataset for each year:
```bash
python cal_d_s_r_each_year_GRID.py
# or
sbatch cal_d_s_r_each_year_GRID.sh
```
#### 3) Global and regional multi-year averages and trends
Calculate multi-year averages and trends of UI, RE, and R/Rmax for each grid-based dataset at the global and regional scale:
```bash
python cal_d_s_r_mean_trend_global_regional_GRID.py
```
#### 4) Grid-scale multi-year averages and trends
Calculate multi-year averages and trends of UI, RE, and R/Rmax for each grid-based dataset at the grid scale:
```bash
python cal_d_s_r_mean_trend_grid_GRID.py
# or
sbatch cal_d_s_r_mean_trend_grid_GRID.sh
```
#### 5) Category averages
Calculate averages of different categories:
```bash
python cal_d_s_r_mean_trend_categories.py
```
#### 6) Percentages of significant changes
Calculate grid/area percentages with significant changes for each dataset:
```bash
python cal_stats_significant_changes.py
```
### 7) Attribution
Attribute UI change to RE and R/Rmax based on staitons
```bash
python cal_attribution_station.py
```
### 3.5. Visualization
```bash
python plot_xxx.py
```
## 4. Contact
If you have any questions, please feel free to open an issue in this repository or contact: Fayong Liu (<liufayong3375@igsnrr.ac.cn>).
