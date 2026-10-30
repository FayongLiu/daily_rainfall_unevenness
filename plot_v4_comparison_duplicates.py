# Code for plotting comparison of duplicate gauges
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from rainfall_ui.util.config import parse_args


args = parse_args()
OVERWRITE = args.overwrite
OVERWRITE = True if OVERWRITE == 1 else False
START_YEAR = args.start_yr
END_YEAR = args.end_yr
TH_YEAR = args.th_yr

dataset_map = {
    'cma': 'CMA',
    'hpd': 'HPD',
    'isd': 'ISD-daily',
    'cdc': 'CDC-Germany',
    'swiss': 'SwissMetNet',
    'eca': 'ECA&D',
    'saca': 'SACA&D',
    'ghcnd': 'GHCN-daily'
}


def plot_comparison(data_df, ref_df, dataset_name, ref_name, data_name, outdir):
    ''' Function to plot comparison of duplicate stations '''

    data_df['DATE'] = pd.to_datetime(data_df['DATE'], errors='coerce')
    ref_df['DATE'] = pd.to_datetime(ref_df['DATE'], errors='coerce')
    data_df = data_df.sort_values('DATE').reset_index(drop=True)
    ref_df = ref_df.sort_values('DATE').reset_index(drop=True)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    plt.subplots_adjust(hspace=0.1)
    alp = 0.3
    ax1.plot(data_df['DATE'], data_df['PRCP'], color='steelblue', alpha=alp, label=f'{dataset_map[dataset_name]}')
    ax1.plot(ref_df['DATE'], ref_df['PRCP'], color='dimgray', alpha=alp, label='GHCN-daily')
    ax1.legend(ncol=2, loc='upper left', frameon=False, fontsize=10)
    title = f'Lat: {data_df["LATITUDE"][0]:.2f}, Lon: {data_df["LONGITUDE"][0]:.2f}'
    ax1.set_title(title, fontsize=12)
    ax1.set_ylabel('Rainfall (mm)', fontsize=10)
    ax1.yaxis.set_major_locator(MaxNLocator(5))
    ax1.set_xticks(["1980-01-01", "1990-01-01", "2000-01-01", "2010-01-01", "2020-01-01"])
    # Add annotaion of mean and std for data_df and ref_df
    ax1.text(0.02, 0.90, f'{dataset_map[dataset_name]}, mean={data_df["PRCP"].mean():.2f}, std={data_df["PRCP"].std():.2f}', transform=ax1.transAxes, fontsize=10, ha='left', va='top')
    ax1.text(0.02, 0.835, f'GHCN-daily, mean={ref_df["PRCP"].mean():.2f}, std={ref_df["PRCP"].std():.2f}', transform=ax1.transAxes, fontsize=10, ha='left', va='top')

    # Plot difference between data_df and ref_df
    merged_df = pd.merge(
        data_df[['DATE', 'PRCP', 'LATITUDE', 'LONGITUDE']],
        ref_df[['DATE', 'PRCP']],
        on='DATE',
        how='inner',
        suffixes=('_data', '_ref')
    )
    differ = merged_df['PRCP_data'] - merged_df['PRCP_ref']
    ax2.plot(merged_df['DATE'], differ, color='maroon', alpha=alp, label=f'{dataset_map[dataset_name]} - GHCN-daily')
    ax2.legend(ncol=1, loc='upper left', frameon=False, fontsize=10)
    ax2.set_ylabel('Difference (mm)', fontsize=10)
    ax2.set_xlabel('Year', fontsize=10)
    ax2.text(0.02, 0.90, f'Mean={differ.mean():.2f}, std={differ.std():.2f}', transform=ax2.transAxes, fontsize=10, ha='left', va='top')
    ax2.yaxis.set_major_locator(MaxNLocator(5))
    ax2.set_xticks(["1980-01-01", "1990-01-01", "2000-01-01", "2010-01-01", "2020-01-01"])
    ax2.set_xticklabels(["1980", "1990", "2000", "2010", "2020"])

    os.makedirs(outdir, exist_ok=True)
    outname = f'comparison_ghcnd_{ref_name.split(".")[0]}_{dataset_name}_{data_name.split(".")[0]}.png'
    outpath = os.path.join(outdir, outname)
    fig.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f'Saving {outpath}')

    return


def main():

    ref_dir = rf'../data/ghcnd_daily_prcp/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/'
    outdir = rf'../fig_v4/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/station_duplicates/'
    os.makedirs(outdir, exist_ok=True)
    data_names = ['cma', 'hpd', 'isd', 'cdc', 'swiss', 'eca', 'saca']
    for data_set in data_names:
        dup_path = rf'../data/station_duplicates/{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/{data_set}_duplicate_stations.csv'
        dup_df = pd.read_csv(dup_path)
        data_dir = rf'../data/{data_set}_daily_prcp//{START_YEAR}_{END_YEAR}_gte{TH_YEAR}/'
        if dup_df.shape[0] > 0:
            for i in range(1):#dup_df.shape[0]):
                ref_name = dup_df['REF_STATION'][i]
                data_name = dup_df['STATION'][i]
                ref_path = os.path.join(ref_dir, ref_name)
                data_path = os.path.join(data_dir, data_name)
                ref_df = pd.read_csv(ref_path)
                data_df = pd.read_csv(data_path)
                # Plot ref prcp and data prcp
                plot_comparison(data_df, ref_df, data_set, ref_name, data_name, outdir)

    return


if __name__ == '__main__':

    main()

