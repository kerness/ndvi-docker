import sys
import os
from typing import Dict
import matplotlib.pyplot as plt
import numpy as np
import rasterio.mask as rmask
import rasterio as rio
import fiona as fio
import fiona.errors as fioer

def read_args() -> Dict[str, str]:
    if len(sys.argv) != 3:
        print('Usage:  python landsat.py folder_name vector \n\tfolder_name - catalog with Landsat products \n\tvecotr - area of interest shapefile ')
        exit()
    return {
        "folder_name": str(sys.argv[1]),
        "vector": str(sys.argv[2]),
    }

def read_landsat_images(folder_name):
    file_list = os.listdir(folder_name)
    channel_list = []
    for f in file_list:
        if (f.startswith('LC') and f.endswith('.tif')):
            if 'band' in f:
                channel_list.append(folder_name + f)
    channel_list.sort()
    channel_numbers = np.arange(1,8)
    bands_dicionary = dict(zip(channel_numbers, channel_list))

    return bands_dicionary

def clip_area(vector_file, raster_file, save_image_to):
    
    try:
        with fio.open(vector_file, 'r') as clipper:
            geometry = [feature['geometry'] for feature in clipper]
    except fioer.DriverError as e:
        sys.exit(e)

    with rio.open(raster_file, 'r') as raster_source:
        clipped_image, transform = rmask.mask(raster_source, geometry, crop=True)
        metadata = raster_source.meta.copy()
    
    metadata.update({"driver": "GTiff",
        "height": clipped_image.shape[1],
        "width": clipped_image.shape[2],
        "transform": transform}
        )
    with rio.open(save_image_to, "w", **metadata) as g_tiff:
        g_tiff.write(clipped_image)

def calculate_index(index_name, landsat_8_bands):
    indexes = {
        'ndvi': (5, 4),
        'ndbi': (6, 5),
        'ndwi': (3, 6),
    }

    # Magiczne 10000 przez które dzielone są piksele poszczególnych obrazów
    # to maksymalna wartość pikseli w produktach poziomu 2 satelity Landsat 8

    if index_name in indexes:
        bands = indexes[index_name]

        with rio.open(landsat_8_bands[bands[0]]) as a:
            band_a = (a.read()[0] / 10000).astype(float)
        with rio.open(landsat_8_bands[bands[1]]) as b:
            band_b = (b.read()[0] / 10000).astype(float)

        numerator = band_a - band_b
        denominator = band_a + band_b

        idx = numerator / denominator
        idx[idx > 1] = 1
        idx[idx < -1] = -1
        return idx
    else:
        raise ValueError('Brak wskaźnika do wyboru, dostępne wskaźniki to ndbi, ndvi i ndwi')

def export_to_raster(result, filename) -> None:
    crs = rio.crs.CRS.from_epsg(32634)
    tr = rio.Affine(30.0, 0.0, 394365.0, 0.0, -30.0, 5574015.0)
    new_dataset = rio.open(filename, 'w', driver='GTiff',
                                height = result.shape[0], width = result.shape[1],
                                count=1, dtype=str(result.dtype),
                                crs = crs, transform = tr  )

    new_dataset.write(result, 1)
    new_dataset.close()


def process_images(folder_name, vector) -> None:
    clipped_folder = './clipped/'
    bands = read_landsat_images('./')

    for band in bands:
        destination = clipped_folder + 'LC_clipped_band' + str(band) + '.tif'
        clip_area(vector, bands[band], destination)
    
    index_res = calculate_index('ndvi', read_landsat_images('./clipped/'))
    export_to_raster(index_res, 'ndvi.tif')


def main() -> None:
    args = read_args()
    process_images(args['folder_name'], args['vector'])


if __name__ == '__main__':
    main()
