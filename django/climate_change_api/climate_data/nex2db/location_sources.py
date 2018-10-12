"""LocationSource methods that map external sources to a list of ClimateLocation tuples.

New sources should define functions or callable classes that perform this mapping.

"""

from collections import namedtuple
import math
import os
import shutil
import tempfile
import uuid
import zipfile

import fiona
from fiona.crs import from_epsg
import numpy as np
import requests
import rasterio
import rasterio.mask

""" ClimateLocation

id: A unique id that can be used to identify this ClimateLocation in your dataset
name: A human-readable name used in debug output (optional)
x: Longitude. The value must be between 0-360 (degrees east). e.g. 1 degree W == 359 degrees E
y: Latitude. The value must be between -90 and 90

"""
ClimateLocation = namedtuple('ClimateLocation', ['id', 'name', 'x', 'y'])


def download_file(url, local_filename=None):
    """Download a file at url to local_filename."""
    if not local_filename:
        local_filename = os.path.join('.', url.split('/')[-1])
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    return local_filename


def write_debug_shapefile(climate_locations, output_filename):
    """Write a shapefile of Points from the given list of ClimateLocation tuples."""
    with fiona.open(output_filename, 'w',
                    driver='ESRI Shapefile',
                    crs=from_epsg(4326),
                    schema={'geometry': 'Point', 'properties': []}) as shapefile:
        features = [{
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [l.x, l.y],
            },
            'properties': {},
        } for l in climate_locations]
        shapefile.writerecords(features)
    print('Features written to: {}'.format(output_filename))


def ClimateAPICityLocationSource(city_queryset, dataset):
    """Generate list of ClimateLocation cells from a climate_data.models.City queryset."""
    return [ClimateLocation(id=city.id, x=city.geom.x, y=city.geom.y, name=city.name)
            for city in city_queryset]


def MultipolygonBoundaryLocationSource(shapefile_url, dataset):
    """Generate list of ClimateLocation cells from intersection with shapes in shapefile_url.

    Uses rasterio.mask.mask to generate a raster mask of cells that intersect the input geometries.

    """
    cell_x = float(dataset.cell_size_x)
    cell_y = float(dataset.cell_size_y)

    tmpdir = tempfile.mkdtemp()
    shapefile = None
    raster = None
    lonlat_coords = []
    try:
        zip_filename = os.path.join(tmpdir, '{}.zip'.format(str(uuid.uuid4())))
        download_file(shapefile_url, local_filename=zip_filename)
        with zipfile.ZipFile(zip_filename) as zip_file:
            files = zip_file.namelist()
            zip_file.extractall(tmpdir)
            local_shapefile = next(filename for filename in files
                                   if filename.lower().endswith('.shp'))
        local_shapefile = os.path.join(tmpdir, local_shapefile)

        shapefile = fiona.open(local_shapefile, 'r')
        if shapefile.crs['init'] != from_epsg(4326)['init']:
            raise TypeError('Input shapefile must be EPSG:4326')
        west, south, east, north = shapefile.bounds
        west = math.floor(west)
        south = math.floor(south)
        east = math.ceil(east)
        north = math.ceil(north)

        features = [feature['geometry'] for feature in shapefile]
        height = math.ceil((north - south) / cell_y)
        width = math.ceil((east - west) / cell_x)

        transform = rasterio.transform.from_origin(west, north, cell_x, cell_y)
        raster_filename = os.path.join(tmpdir, '{}.tif'.format(str(uuid.uuid4())))
        ones = np.ones((height, width), dtype=float)
        raster = rasterio.open(raster_filename, 'w+', driver='GTiff',
                               height=height, width=width, count=1, dtype=ones.dtype,
                               crs='EPSG:4326', transform=transform)
        raster.write(ones, 1)
        mask, out_transform = rasterio.mask.mask(raster, features,
                                                 all_touched=True, nodata=0, filled=False)
        xy_coords = np.transpose(mask.nonzero())
        # idx 0 = raster band, idx 1 = height / row, idx 2 = width / col
        lonlat_coords = [rasterio.transform.xy(transform, c[1], c[2]) for c in xy_coords]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        if shapefile:
            shapefile.close()
        if raster:
            raster.close()
    return [ClimateLocation(id=str(uuid.uuid4()),
                            name='({}, {})'.format(c[0], c[1]),
                            x=c[0],
                            y=c[1]) for c in lonlat_coords]
