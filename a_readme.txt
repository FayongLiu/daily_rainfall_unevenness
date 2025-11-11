Use following command to create a new virtual python environment, or you can also use your owe environemnt
  conda env create -f environment.yml
Then activate the new enviroment
  conda activate rainfall


1. preprocess
1) select and concat valid isd station data
pre_isd_xxx.py
2) aggregate hourly era5_land/cur-jra precipitation data to daily scale, and then calculate multi-year maximum annual precipitation, as well as CMIP6 models
pre_CUR_JRA/ERA5_Land_hourly2daily_prcp.py/.sh
pre_GRID_cal_maximum_annual_prcp.py/.sh


2. calulate R/Rmax (ratio), RE(d), UI(s) and their multi-year mean and trend
cal_d_s_r_mean_trend_xxx.py
cal_d_s_r_each_year_GRID.py/.sh