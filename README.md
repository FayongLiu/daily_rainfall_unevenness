# daily_rainfall_unevenness
Codes for evaluating historical daily rainfall unevenness.

## Create virtual python environment
Use following command to create a new virtual python environment, or you can also use your owe environemnt:
conda env create -f environment.yml

Then activate the new enviroment:
conda activate rainfall

## Preparation
According to the **Data available statement** in the paper to prepare the data.
After preparing the data, please revise the data path in the code before running them.

## Step by step
### 1. Navigate to the directory where the code folder is located
cd /your/own/code/path/

### 2. Ensure that your virtual python environment is acvated
conda activate rainfall (or use your own environment)

### 3. Preprocess
#### 3.1. Select valid ISD stations
Running time was estimated for running 21 years (2000-2020)
python pre_isd_select_valid_station.py (~ 2 min)
Here, you can also change the standard for defining what is a "valid station"

#### 3.2. Concatenate the data of each valid station in different years (multiple .csv file) into a .csv file
python pre_isd_concat_valid_station.py (~ 5 s)

#### 3.3. Select valid stations in Chinese Station Data
python pre_ChinaSD_select_valid_station.py (~ 3 s)

#### 3.4. Arregate hourly grid-based data to daily scale
python pre_ERA5_Land_hourly2daily_prcp.py (time consuming)
sbatch pre_CRU_JRA_hourly2daily_prcp.sh (time consuming)

#### 3.5. Calculate maximum annual precipitation (Rmax) across all grids and years for each grid-based data
python pre_GRID_cal_maximum_annual_prcp.py or sbatch pre_GRID_cal_maximum_annual_prcp.sh (~ 20 min)

### 4. Calculation
#### 4.1. Calculate Rmax, UI, RE, and R/Rmax for staions, as well as their multi-year averages and trend
python cal_d_s_r_mean_trend_isd.py (~ 30 s)

#### 4.2. Calculate UI, RE, and R/Rmax for each grid-based data for each year
python cal_d_s_r_each_year_GRID.py or sbatch cal_d_s_r_each_year_GRID.sh (~ 40 min)

#### 4.3. Calculate multi-year averages and trend of UI, RE, and R/Rmax for each grid-based data at global scale
python cal_d_s_r_mean_trend_global_GRID.py (~ 20 s)

#### 4.4. Calculate multi-year averages and trend of UI, RE, and R/Rmax for each grid-based data at grid scale
python cal_d_s_r_mean_trend_grid_GRID.py or sbatch cal_d_s_r_mean_trend_grid_GRID.sh (~ 13 min)

#### 4.5. Calculate avreages of all CMIP6 models
python cal_d_s_r_mean_trend_CMIP6_ensembles.py (~ 1 s)

#### 4.6. Calculate grid/area percentages with significant changes for each data
python cal_stats_significant_changes.py (~ 1 s)

### 5. Visualization
#### 5.1. Plot method comparison, among SD, RE, and UI
python plot_method_comparison_SD_RE_UI.py (~ 1 s)

#### 5.2. Plot method comparison, between daily and monthly RE
python plot_method_comparison_daily_monthly_RE.py (~ 1 s)

#### 5.3. Plot mean and trend for station data
python plot_mean_trend_isd.py (~ 2 s)

#### 5.4. Plot mean and trend for grid-based data
python plot_mean_trend_GRID.py (~ 4 min)

#### 5.5. Plot mean and trend for each CMIP6 model
python plot_mean_trend_each_CMIP6.py (~ 1 min)

#### 5.6. Plot grid/area percentages with significant changes for each data
python plot_stats_significant_changes.py (~ 1 s)