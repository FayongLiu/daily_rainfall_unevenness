# Code for plotting guages map
import os
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import seaborn as sns
import time
from rainfall_ui.util.config import parse_args
from rainfall_ui.util.visualization import adjust_axis_label
from rainfall_ui.util.datainfo import REGIONS


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr


# function to plot distribution of station data
def plot_gauges_map(df, gdf, outpath):

    ftsz = 10
    
    fig, axname = plt.subplots(1, 1, figsize=(8, 4), dpi=300)
    plt.subplots_adjust(
        left=0.06,
        right=0.98,
        top=0.98,
        bottom=0.18,
        hspace=0,
        wspace=0
    )
    clr = [
        '#ABD5E3',  # global (GHCN-daily)
        '#F5DAC7',  # global (ISD_daily)
        '#7BC48A',  # Europe (ECA&D)
        '#F9D86E',  # Southeast Asia (SACA&D)
        '#E8848A',  # China (CMA)
        '#E8A0BF',  # United States (HPD)
        '#B0BEC5',  # Germany (CDC-Germany)
        '#B596B5'   # Switzerland (SwissMetNet)
    ]
    sz = 10
    alp = 0.6
    
    hue_order = ['ghcnd', 'isd', 'eca', 'saca', 'cma', 'hpd', 'cdc', 'swiss']
    full_dataname = {
        'ghcnd': 'GHCN-daily',
        'isd': 'ISD-daily',
        'eca': 'ECA&D',
        'saca': 'SACA&D',
        'cma': 'CMA',
        'hpd': 'HPD',
        'cdc': 'CDC-Germany',
        'swiss': 'SwissMetNet'
    }
    df['dataname'] = df['dataname'].map(full_dataname)
    hue_order = [full_dataname[key] for key in hue_order]
    clr_dict = dict(zip(hue_order, clr))

    # add base map
    min_lon, max_lon = -180, 180
    min_lat, max_lat = -60, 90
    gdf = gdf.cx[min_lon:max_lon, min_lat:max_lat]
    gdf.plot(ax=axname, color='dimgray', linewidth=0.5)
    # plot scatter
    sns.scatterplot(
        data=df,
        x='lon', y='lat',
        hue='dataname',
        hue_order=hue_order,
        s=sz,
        alpha=alp,
        ax=axname,
        palette=clr_dict
    )
    adjust_axis_label(axname, ftsz=ftsz)
    axname.legend(loc='upper left', bbox_to_anchor=(0.15, -0.08), ncols=4, fontsize=ftsz, frameon=False)
    # add annotation
    text = f'Total: {len(df)}'
    left = 0.025
    bottom = 0.41
    axname.text(left, bottom, text, va='bottom', ha='left', fontsize=ftsz, transform=axname.transAxes, color='dimgray', alpha=0.7)
    for i, dataname in enumerate(hue_order):
        dataname_df = df[df['dataname'] == dataname]
        cnt = len(dataname_df)
        axname.text(
            x=left,
            y=bottom - 0.05*(i+1),
            s=f'{dataname}: {cnt}',
            va='bottom',
            ha='left',
            fontsize=ftsz,
            transform=axname.transAxes,
            color='dimgray',
            alpha=0.7
        )
    
    for region, (min_lon_r, max_lon_r, min_lat_r, max_lat_r) in REGIONS.items():
        axname.add_patch(plt.Rectangle(
            (min_lon_r, min_lat_r),
            max_lon_r - min_lon_r,
            max_lat_r - min_lat_r,
            fill=False,
            edgecolor='dimgray',
            linewidth=1,
            linestyle='--',
            alpha=alp
        ))
        # add annotation
        valid_df = df[df['lon'].between(min_lon_r, max_lon_r) & df['lat'].between(min_lat_r, max_lat_r)]
        if region == 'Australia':
            text = f'{region}\ngauges={len(valid_df)}'
            x = min_lon_r
            y = min_lat_r
            va = 'top'
            ha = 'left'
        else:
            text = f'{region}, gauges={len(valid_df)}'
            x = min_lon_r
            y = max_lat_r
            va = 'bottom'
            ha = 'left'
        axname.text(x, y, text, fontsize=ftsz, color='dimgray', ha=ha, va=va, alpha=0.7)

    # save result
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=300)
    print(f'Saving {outpath}')
    plt.close()

    return


def main():

    t1 = time.time()

    # load data
    station_path = rf'../data/station_info/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station.csv'
    if os.path.exists(station_path) and not OVERWRITE:
        print(f'{station_path} exists, loading...')
        station_df = pd.read_csv(station_path)
    else:
        if not os.path.exists(station_path):
            print(f'{station_path} does not exist, calculating...')
        else:
            print(f'{station_path} exists, overwriting...')
        station_dir = rf'../data/d_s_ratio/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station/'
        files = os.listdir(station_dir)
        files.sort()
        station_df = []
        for f in files:
            if f.endswith('.csv'):
                tempt_path = os.path.join(station_dir, f)
                tempt_df = pd.read_csv(tempt_path, usecols=['lon', 'lat', 'dataname'])
                station_df.append(tempt_df.iloc[0, :])
        station_df = pd.concat(station_df, axis=1).T
        os.makedirs(os.path.dirname(station_path), exist_ok=True)
        station_df.to_csv(station_path, index=False)
        print(f'Saving {station_path}')
    shp = r'/data4/dataset/lucc_boundary_map/global_coastline_110m/global_coastline_110m.shp'
    gdf = gpd.read_file(shp)
    print('Finish loading global coastline data')

    # plot map
    outpath = rf'../fig_v4/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/gauges_map.png'
    plot_gauges_map(station_df, gdf, outpath)

    t2 = time.time()
    running_time = t2 - t1
    hours = int(running_time // 3600)
    minutes = int((running_time % 3600) // 60)
    seconds = int(running_time % 60)
    print(f"Running time: {hours} h, {minutes} min, {seconds} s")

    return


if __name__ == "__main__":
    
    main()

