import calendar
import logging
import collections

from django.db.utils import IntegrityError

import numpy
import netCDF4

from .models import City, ClimateDataCell, ClimateDataCityCell, ClimateDataYear

DAY_OF_YEAR_FEB_29 = 60


class Nex2DB(object):
    """Import data from NetCDF files to database."""

    # cache list of cites to guarantee ordering during import
    cities = None

    def __init__(self, data_source, update_existing=False, logger=None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.datasource = data_source

        # Store a cache of all cities locally
        cities_queryset = City.objects.all().order_by('pk')
        if not update_existing:
            # Only process cities that don't have this datasource loaded
            cities_queryset = cities_queryset.exclude(
                map_cell__datasource=data_source
            )
        self.cities = list(cities_queryset)

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

    def get_var_data(self, var_name, path):
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
            ds_year = int(self.datasource.year)
            assert(year == ds_year)
            self.logger.debug("Got year %d ?= self.datasource.year %d", year, ds_year)

            cell_indexes = set()
            city_to_coords = {}
            for city in self.cities:
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

                cell_indexes.add((latidx, lonidx))
                city_to_coords[city.id] = (latarr[latidx], lonarr[lonidx])

            # Use numpy to get a list of var_data[*][lat][lon] for each referenced cell
            cell_data = {}
            for (latidx, lonidx) in cell_indexes:
                values = list(ds.variables[var_name][:, latidx, lonidx])
                # Our DB assumes that leap years have 366 values in their ArrayFields.
                #   If we're woking with a calendar that doesn't consider leap years on a leap year,
                #   insert None for Feb 29
                if calendar.isleap(year) and len(values) == 365:
                    values.insert(DAY_OF_YEAR_FEB_29, None)
                cell_data[(latarr[latidx], lonarr[lonidx])] = values

        return city_to_coords, cell_data

    def merge_netcdf_data(self, variable_paths):
        # Parse each NetCDF file into useable data keyed by its variable
        variable_data = {}
        # In case any of the NetCDF files had different coordinates than any other, merge their
        # city coordinate mappings into a single dict
        city_coords = {}
        for label, path in variable_paths.items():
            city_to_coords, cell_data = self.get_var_data(label, path)
            city_coords.update(city_to_coords)
            variable_data[label] = cell_data

        return city_coords, variable_data

    def collate_variable_data(self, variable_data):
        # Convert data from {variable: {coords: [data]}}
        # to {(coords): {'variable': [data]}}
        data_by_coords = collections.defaultdict(dict)
        for variable, results in variable_data.items():
            for coords, data in results.items():
                data_by_coords[coords][variable] = data
        return data_by_coords

    def load_map_cell_models(self, city_coords):
        # Load all of the map cells that already exist
        cell_models = {(cell.lat, cell.lon): cell for cell in ClimateDataCell.objects.all()}

        for coords in city_coords:
            try:
                cell_model = cell_models[coords]
            except KeyError:
                # This cell is not in the database, we should create it
                lat, lon = coords
                cell_model, cell_model_created = (ClimateDataCell.objects
                                                    .get_or_create(lat=lat.item(), lon=lon.item()))
                cell_models[coords] = cell_model
                if cell_model_created:
                    self.logger.info('Created map_cell at (%s, %s)', lat.item(), lon.item())
        return cell_models

    def save_climate_data_year(self, data_by_coords, cell_models):
        # Go through the collated list and create all the relevant datapoints
        self.logger.debug('Saving to database')

        for coords, results in data_by_coords.items():
            assert(set(results.keys()) == ClimateDataYear.VARIABLE_CHOICES)

            # If appropriate ClimateDataYear object exists, update data
            # Otherwise create it
            cell_model = cell_models[coords]
            cdy, cdy_created = ClimateDataYear.objects.update_or_create(
                map_cell=cell_model,
                datasource=self.datasource,
                defaults=results
            )
            if cdy_created:
                self.logger.info('Created ClimateDataYear record for ' +
                                    'self.datasource: %s, map_cell: %s',
                                    self.datasource,
                                    cell_model)
            else:
                self.logger.debug('Updated ClimateDataYear record ' +
                                    'for self.datasource: %s, map_cell: %s',
                                    self.datasource,
                                    cell_model)

    def update_city_map_cells(self, city_coords, cell_models):
        self.logger.debug('Combining city list')

        for results in variable_data.values():

        # Go through all the cities and update their ClimateDataCityCell representations
        # Ensuring only one entry exists for a given city and dataset
        self.logger.debug('Updating cities')
        for city in self.cities:
            cell_coords = city_coords[city.id]
            cell_model = cell_models[cell_coords]
            try:
                city_cell, created = ClimateDataCityCell.objects.get_or_create(
                    city=city,
                    dataset=self.datasource.dataset,
                    map_cell=cell_model
                )

                if created:
                    self.logger.debug('Created new ClimateDataCityCell for '
                                      'city %s dataset %s map_cell %s',
                                      city.id, self.datasource.dataset.name, str(cell_model))

            except IntegrityError:
                self.logger.warning('ClimateDataCityCell NOT created for '
                                    'city %s dataset %s map_cell %s',
                                    city.id, self.datasource.dataset.name, str(cell_model))

    def nex2db(self, variable_paths):
        """Extract data about cities from three NetCDF files and writes it to the database.

        @param variable_paths Dictionary of variable identifier to path for the corresponding
                              NetCDF file
        """
        assert(set(variable_paths.keys()) == ClimateDataYear.VARIABLE_CHOICES)
        self.logger.debug("Using datasource: %s", self.datasource)

        # Convert the separate NetCDF file processing results into distinct results
        # - city_coords as a single mapping of city ID to map cell coordinates
        # - variable_data as a dictionary of {variable: {coords: [data]}}
        city_coords, variable_data = self.merge_netcdf_data(variable_paths)

        # Group the distinct variable data sets by coordinate
        data_by_coords = self.collate_variable_data(variable_data)

        # Make or load ClimateDataCell models for each coordinate set we have
        cell_models = self.load_map_cell_models(data_by_coords.keys())

        # Save the raw climate data to database
        self.save_climate_data_year(data_by_coords, cell_models)

        # Update cities to map to their respective map cell as needed
        self.update_city_map_cells(city_coords, cell_models)

        # note job completed successfully
        self.datasource.import_completed = True
        self.datasource.save()
        self.logger.info('nex2db processing done')
