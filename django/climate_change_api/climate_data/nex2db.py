import os
from datetime import date, timedelta
import logging

import numpy

os.environ['GDAL_NETCDF_BOTTOMUP'] = 'NO'
import rasterio
from rasterio._io import RasterReader

from models import City, ClimateData

logger = logging.getLogger()


def get_cities():
    """
    Loads cities from database and returns them
    """
    return list(City.objects.all())


def open_netCDF(path, subds=''):
    """
    Opens a NetCDF file as a rasterio object
    """
    p = 'NETCDF:' + path
    if subds:
        p += ':' + subds
    s = RasterReader(p)
    s.start()
    return s


def get_window(affine, x, y, height):
    """
    Return small window for raster from WGS84 coordinates
    """
    # window = ((y1, y2), (x1, x2)) because rows get read backwards
    (col, row) = ~affine * (x, y)
    col, row = int(col), int(row)
    return ((height - row, height - row + 1), (col, col + 1))


def insert_data(dt, scenario, model, city, var, value):
    """Inserts data by updating the relevant row"""
    day_of_year = (dt - date(dt.year, 1, 1)).days + 1
    ClimateData.objects.filter(city=city,
                               scenario=scenario,
                               climate_model=model,
                               year=dt.year,
                               day_of_year=day_of_year).update(**{var: value})


def nex2db(input_path,
           var='',
           scenario=None,
           model=None,
           base_time=date(1950, 1, 1)):
    """
    Extracts data about cities from a NetCDF and writes it to a json file

    Arguments:
    input_path -- the path of the NetCDF file to extract from
    var -- the NetCDF subdataset to extract from
    scenario -- scenario object from database
    model -- model object from database
    base_time -- base time of the model
    """
    with rasterio.drivers():
        with open_netCDF(input_path, var) as dataset:
            rows = dataset.meta['height']

            # Logic for doing extent windowing.
            affine = dataset.affine

            for city in get_cities():
                read_window = get_window(affine, city.geom.x, city.geom.y, rows)

                for i in range(1, dataset.count + 1):
                    tags = dataset.tags(i)
                    days_since = float(tags['NETCDF_DIM_time'])
                    band_date = base_time + timedelta(days=days_since)

                    # WEIRDNESS: The netCDF is "bottom-up" data. This causes GDAL
                    # to not be able to work with it unless this evnironment variable
                    # is exported: export GDAL_NETCDF_BOTTOMUP=NO
                    # So it reads the band upside down, and we need to flip it.
                    wrong_way_up = dataset.read_band(i, window=read_window)
                    tile_data = numpy.flipud(wrong_way_up)
                    insert_data(band_date,
                                scenario,
                                model,
                                city,
                                var,
                                float(tile_data[0][0]))
