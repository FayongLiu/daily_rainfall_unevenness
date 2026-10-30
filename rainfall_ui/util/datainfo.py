# Code for data info
# CATEGORY_NAMES = ["Gauge-based", "Satellite", "Reanalysis", "CMIP6", "Grid-based"]
# CATEGORY_NAMES_FULL = ["Gauge-based", "Satellite-based", "Reanalysis", "CMIP6 ensembles", "All grid-based"]
CATEGORY_NAMES = ["Gauge-based", "Reanalysis", "CMIP6"]
CATEGORY_NAMES_FULL = ["Gauge-based", "Reanalysis", "CMIP6 ensembles"]
GAUGE_BASED_LS_80 = ["CPC", "GPCC", "REGEN_LM"] # from 1980
GAUGE_BASED_LS_50 = ["REGEN_LM"] # from 1950 as supplementary
SATELLITE_LS = ["IMERG", "GSMaP", "CMORPH", "PERSIANN", "PERSIANN_CDR"] # not used in the final version due to the limited temporal coverage
REANALYSIS_LS_80 = ["MSWEP", "CRU_JRA", "ERA5_Land", "JRA3q"]
REANALYSIS_LS_50 = ["CRU_JRA", "ERA5_Land", "JRA3q"]
CMIP6_LS = ["ACCESS-CM2_day", "ACCESS-ESM1-5_day", "AWI-ESM-1-1-LR_day", "AWI-ESM-1-REcoM_day",
            "BCC-ESM1", "CanESM5_day", "CESM2-FV2_day", "CESM2-WACCM-FV2_day",
            "CESM2-WACCM_day", "CESM2", "CMCC-CM2-HR4_day", "CMCC-CM2-SR5_day",
            "CMCC-ESM2_day", "EC-Earth3-CC_day", "FGOALS-g3_day", "GISS-E2-2-G_day",
            "IITM-ESM_day", "MIROC6_day", "MPI-ESM-1-2-HAM_day", "MPI-ESM1-2-HR_day",
            "MPI-ESM1-2-LR_day", "NorCPM1", "NorESM2-LM_day", "NorESM2-MM_day", "SAM0-UNICON_day"]
DATA_LS_80 = GAUGE_BASED_LS_80 + REANALYSIS_LS_80 + CMIP6_LS
DATA_LS_50 = GAUGE_BASED_LS_50 + REANALYSIS_LS_50 + CMIP6_LS
CATEGORY_LS_80 = [GAUGE_BASED_LS_80, REANALYSIS_LS_80, CMIP6_LS]
CATEGORY_LS_50 = [GAUGE_BASED_LS_50, REANALYSIS_LS_50, CMIP6_LS]
DATAPATHS = {
    "CPC": r"/data4/dataset/atmosphere/precipitation/CPC_Global_Data/",
    "GPCC": r"/data4/dataset/atmosphere/precipitation/GPCC_daily/",
    "REGEN_LM": r"/data4/dataset/atmosphere/precipitation/REGEN_LM_V1_2019_Data/",
    "CRU_JRA": r"/data4/dataset/atmosphere/precipitation/CRU-JRA/pre/",
    "ERA5_Land": r"/data4/dataset/atmosphere/ERA5_land/precipitation/daily/"
}
for dataname in SATELLITE_LS+["MSWEP", "JRA3q"]:
    DATAPATHS[dataname] = rf"/data4/dataset/atmosphere/precipitation/{dataname.lower()}_daily/"

for dataname in CMIP6_LS:
    DATAPATHS[dataname] = rf"/data1/jzzhou/precipitation/season/cmip6/{dataname}/"

RESOLUTIONS = {
    "CPC": 0.5,
    "GPCC": 1.0,
    "REGEN_LM": 1.0,
    "IMERG": 0.1,
    "GSMaP": 0.1,
    "CMORPH": 0.07,
    "PERSIANN_CDR": 0.04,
    "PERSIANN": 0.25,
    "MSWEP": 0.1,
    "CRU_JRA": 0.5,
    "ERA5_Land": 0.1,
    "JRA3q": 0.375
}
# use 1 degree to represent the course resolution of CMIP6, which does not influence the results
# as this resolution is only used to determine the cores for processing data in parallel in avoid of memory overflow
for dataname in CMIP6_LS:
    RESOLUTIONS[dataname] = 1.0 

REGIONS = {
    'North America': [-170, -50, 10, 80],
    'Europe': [-15, 70, 30, 80],
    'Asia': [70, 175, 0, 80],
    'Australia': [110, 160, -45, -10]
}