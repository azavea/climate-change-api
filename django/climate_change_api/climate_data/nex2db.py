import os
from datetime import date, timedelta
import logging

import numpy

os.environ['GDAL_NETCDF_BOTTOMUP'] = 'NO'
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


class VariableData:
    def __init__(self, var_name, path, base_time):
        self.raster = open_netCDF(path, var_name)
        self.rows = self.raster.meta['height']

    def _get_window(self, x, y):
        """
        Return small window for raster from WGS84 coordinates
        """
        # window = ((y1, y2), (x1, x2)) because rows get read backwards
        (col, row) = ~self.raster.affine * (x, y)
        col, row = int(col), int(row)
        return ((self.rows - row, self.rows - row + 1), (col, col + 1))

    def get_datum(self, i, x, y):
        # WEIRDNESS: The netCDF is "bottom-up" data. This causes GDAL
        # to not be able to work with it unless this evnironment variable
        # is exported: export GDAL_NETCDF_BOTTOMUP=NO
        # So it reads the band upside down, and we need to flip it.
        wrong_way_up = self.raster.read_band(i, window=self._get_window(x, y))
        tile_data = numpy.flipud(wrong_way_up)
        return float(tile_data[0][0])


def nex2db(tasmin_path,
           tasmax_path,
           pr_path,
           data_source,
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
    tasmin = VariableData('tasmin', tasmin_path, base_time)
    tasmax = VariableData('tasmax', tasmax_path, base_time)
    pr = VariableData('pr', pr_path, base_time)
    for city in get_cities():
        to_insert = []
        for i in range(1, tasmin.raster.count + 1):
            tags = tasmin.raster.tags(i)
            days_since = float(tags['NETCDF_DIM_time'])
            for var in (tasmax, pr):
                assert float(var.raster.tags(i)['NETCDF_DIM_time']) == days_since

            band_date = base_time + timedelta(days=days_since)
            day_of_year = (band_date - date(band_date.year, 1, 1)).days + 1
            to_insert.append(ClimateData(city=city,
                                         day_of_year=day_of_year,
                                         data_source=data_source,
                                         tasmin=tasmin.get_datum(i, city.geom.x, city.geom.y),
                                         tasmax=tasmax.get_datum(i, city.geom.x, city.geom.y),
                                         pr=pr.get_datum(i, city.geom.x, city.geom.y)))
        ClimateData.objects.bulk_create(to_insert)
