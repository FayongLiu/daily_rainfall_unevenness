# Code for coverting coastal line to land mask


import numpy as np
import xarray as xr
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import Point
from shapely.prepared import prep


def main():

    # load land shp data
    shp = r'/data1/fyliu/global_land_110m/ne_110m_land.shp'
    gdf = gpd.read_file(shp)
    land_poly = unary_union(gdf.geometry)
    land_poly = prep(land_poly)

    # load ref nc data
    ref_path = r'/data4/dataset/atmosphere/precipitation/CRU-JRA/pre/pre_2001_daily.nc'
    ds = xr.open_dataset(ref_path)
    lat = ds['lat'].values
    lon = ds['lon'].values

    # calculate land mask
    lon2d, lat2d = np.meshgrid(lon, lat)
    mask = np.zeros(lon2d.shape, dtype=bool)
    for i in range(lat2d.shape[0]):
        for j in range(lon2d.shape[1]):
            if land_poly.contains(Point(lon2d[i, j], lat2d[i, j])):
                mask[i, j] = True

    # create land mask
    mask_da = xr.DataArray(
        mask.astype(bool),
        dims=('lat', 'lon'),
        coords={'lat': lat, 'lon': lon},
        name='land',
        attrs={'description': 'True = inside land boundary, False = outside'}
    )

    outpath = r'../data/mask/land_mask_ref.nc'
    mask_da.to_netcdf(outpath)
    print(f'Land mask saved to {outpath}')

    return


if __name__ == '__main__':

    main()

