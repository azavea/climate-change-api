import calendar
import logging
import collections

import numpy
import netCDF4

from .models import City, ClimateDataYear, ClimateDataCell
from django.db import IntegrityError

DAY_OF_YEAR_FEB_29 = 60


class Nex2DB(object):
    """Import data from NetCDF files to database."""

    # cache list of cites to guarantee ordering during import
    cities = None

    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger(__name__)

    def get_cities(self):
        if not self.cities:
            self.cities = list(City.objects.all().order_by('pk'))
        return self.cities

    def netcdf2year(self, time_array, time_unit, netcdf_calendar):
        """Return the year of the netcdf file as an int.

        Raises ValueError if the time dimension contains more than a single year

        """
        first_date = netCDF4.num2date(time_array[0], time_unit, calendar=netcdf_calendar)
        last_date = netCDF4.num2date(time_array[-1], time_unit, calendar=netcdf_calendar)
        if first_date.year == last_date.year:
            return int(first_date.year)
        else:
            self.logger.debug("Mismatch in years: got %d-%d with calendar %s and units %s",
                              first_date.year, last_date.year, netcdf_calendar, time_unit)
            raise ValueError("Expected netcdf2year time_array to only contain values " +
                             "for a single year")

    def get_var_data(self, var_name, path, data_source):
        """Read out data from a NetCDF file and return its data, translated.

        Reads only the points representing the cities in the database.

        @param var_name Name of the variable in this NetCDF (tasmin, tasmax, or pr)
        @param path Full path to the NetCDF file on disk

        @returns Object containing:
            cells: map of cells by coordinate tuple to dictionary of variable values
                   keyed by corresponding date
            cities: map of each city by internal ID to the cell coordinates it matched to
        """
        # data in the climate NetCDF files can be referenced as:
        # ds.variables[var name][day of year index][latitude index][longitude index]
        self.logger.debug('processing NetCDF at %s for var %s', path, var_name)
        with netCDF4.Dataset(path, 'r') as ds:
            latarr = numpy.asarray(ds.variables['lat'])
            lonarr = numpy.asarray(ds.variables['lon'])
            time_unit = ds.variables['time'].units
            # using non-standard calendar
            netcdf_calendar = ds.variables['time'].calendar

            year = self.netcdf2year(ds.variables['time'], time_unit, netcdf_calendar)
            self.logger.debug("Got year %d ?= data_source.year %d", year, data_source.year)
            assert(year == int(data_source.year))

            # read variable data into memory
            var_data = ds.variables[var_name]

            cell_idx = set()
            city_to_coords = {}
            for city in self.get_cities():
                self.logger.debug('processing variable %s for city: %s', var_name, city.name)
                # Not geographic distance, but good enough for
                # finding a point near a city center from disaggregated data.
                # city_y must be in the range [-90, 90]
                city_y = city.geom.y
                # city_x must be in the range [0,360] in units degrees east
                # lon units are degrees east, so degrees west maps inversely to 180-360
                city_x = 360 + city.geom.x if city.geom.x < 0 else city.geom.x

                latidx = (numpy.abs(city_y - latarr)).argmin()
                lonidx = (numpy.abs(city_x - lonarr)).argmin()

                cell_idx.add((latidx, lonidx))
                city_to_coords[city.id] = (latarr[latidx], lonarr[lonidx])

            # Use numpy to get a list of var_data[*][lat][lon] for each referenced cell
            cell_data = {}
            for (latidx, lonidx) in cell_idx:
                values = list(var_data[:, latidx, lonidx])
                # Our DB assumes that leap years have 366 values in their ArrayFields.
                #   If we're woking with a calendar that doesn't consider leap years on a leap year,
                #   insert None for Feb 29
                if calendar.isleap(year) and len(values) == 365:
                    values.insert(DAY_OF_YEAR_FEB_29, None)
                cell_data[(latarr[latidx], lonarr[lonidx])] = values

        return {'cities': city_to_coords, 'cells': cell_data}

    def nex2db(self, variable_paths, data_source):  # NOQA: C901
        """Extract data about cities from three NetCDF files and writes it to the database.

        @param variable_paths Dictionary of variable identifier to path for the corresponding
                              NetCDF file
        @param data_source ClimateDataSource object that defines the source model/scenario/year
        """
        assert(set(variable_paths) == ClimateDataYear.VARIABLE_CHOICES)
        self.logger.debug("Using datasource: %s", data_source)

        variable_data = {label: self.get_var_data(label, path, data_source)
                         for label, path in variable_paths.items()}

        # Convert data from {variable: {'cells': coords: [data]}}
        # to {(coords): {'variable': [data]}}
        datasource_data = collections.defaultdict(dict)
        for variable, results in variable_data.items():
            for coords, data in results['cells'].items():
                datasource_data[coords][variable] = data

        self.logger.debug('Combining city list')
        city_coords = {}
        for results in variable_data.values():
            city_coords.update(results['cities'])

        # Go through the collated list and create all the relevant datapoints
        self.logger.debug('Saving to database')

        # Load all of the map cells that already exist
        cell_models = {(cell.lat, cell.lon): cell for cell in ClimateDataCell.objects.all()}

        for coords, results in datasource_data.items():

            assert(set(results.keys()) == ClimateDataYear.VARIABLE_CHOICES)

            lat, lon = coords
            try:
                cell_model = cell_models[coords]
            except KeyError:
                # This cell is not in the database, we should create it
                cell_model, created = ClimateDataCell.objects.get_or_create(lat=lat.item(),
                                                                            lon=lon.item())
                cell_models[coords] = cell_model

            climatedatayear_args = dict(map_cell=cell_model,
                                        data_source=data_source,
                                        **results)
            try:
                ClimateDataYear.objects.create(**climatedatayear_args)
            except IntegrityError:
                self.logger.warn('Deleting existing record for data_source: %s, map_cell: %s',
                                 data_source,
                                 cell_model)
                ClimateDataYear.objects.filter(map_cell=cell_model,
                                               data_source=data_source).delete()
                self.logger.warn('Re-attempting record insert for data_source: %s, map_cell: %s',
                                 data_source,
                                 cell_model)
                ClimateDataYear.objects.create(**climatedatayear_args)

        # Go through all the cities and set their map_cell to the appropriate model
        self.logger.debug('Updating cities')
        for city in self.get_cities():
            coords = city_coords[city.id]
            cell_model = cell_models[coords]
            if city.map_cell:
                assert(city.map_cell == cell_model)
            else:
                city.map_cell = cell_model
                city.save()

        # note job completed successfully
        data_source.import_completed = True
        data_source.save()
        self.logger.info('nex2db processing done')
