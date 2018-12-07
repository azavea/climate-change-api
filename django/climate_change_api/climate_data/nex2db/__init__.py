import calendar
import collections
import logging
import os
import tempfile
from uuid import uuid4

from django.conf import settings
from django.db.utils import IntegrityError

import numpy
import netCDF4

from climate_data.models import (
    City,
    ClimateDataCell,
    ClimateDataCityCell,
    ClimateDataYear,
    ClimateDataSource,
)
from climate_data.nex2db.downloaders import get_netcdf_downloader
from climate_data.nex2db.location_sources import (
    ClimateAPICityLocationSource,
    MultipolygonBoundaryLocationSource,
    write_debug_file,
)


DAY_OF_YEAR_FEB_29 = 60


logger = logging.getLogger('climate_data')


class Nex2DB(object):
    """Import data from NetCDF files to database."""

    # cache list of cites to guarantee ordering during import
    cities = None
    # Datasource object representing the source we intend to import
    datasource = None
    # Boolean flag designating if we should update existing entries or only insert new
    update_existing = False

    def __init__(self, dataset, scenario, model, year,
                 import_boundary_url=None, update_existing=False, logger=None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.update_existing = update_existing
        self.import_boundary_url = import_boundary_url

        datasource, created = ClimateDataSource.objects.get_or_create(
            dataset=dataset,
            model=model,
            scenario=scenario,
            year=year
        )
        if created:
            logger.info('Created data source for dataset %s model %s scenario %s year %s',
                        dataset.name, model.name, scenario.name, year)
        self.datasource = datasource

        # Store a cache of all cities locally
        if import_boundary_url:
            self.locations = MultipolygonBoundaryLocationSource(import_boundary_url, dataset)
        else:
            cities_queryset = City.objects.all().order_by('pk')
            if not self.update_existing:
                # Only process cities that don't have this datasource loaded
                cities_queryset = cities_queryset.exclude(
                    map_cell_set__map_cell__climatedatayear__data_source=datasource
                )
            self.locations = ClimateAPICityLocationSource(cities_queryset, dataset)
        if settings.DEBUG:
            debug_dir = os.path.join(settings.BASE_DIR, 'nex2db-locations-debug')
            try:
                os.mkdir(debug_dir)
            except FileExistsError:
                pass
            debug_file = os.path.join(debug_dir, '{}.shp'.format(str(uuid4())))
            logger.info('Writing debug locations shapefile to path: {}'.format(debug_file))
            write_debug_file(self.locations, debug_file, file_format='shpfile')

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

            # read variable data into memory
            var_data = ds.variables[var_name][:, :, :]  # :,:,: loads everything into ram
            assert ds.variables[var_name].shape == var_data.shape

            cell_indexes = set()
            location_to_coords = {}
            for location in self.locations:
                self.logger.debug('processing variable %s for city: %s', var_name, location.name)
                # Not geographic distance, but good enough for
                # finding a point near a city center from disaggregated data.
                # location_y must be in the range [-90, 90]
                location_y = location.y
                # location_x must be in the range [0,360] in units degrees east
                # lon units are degrees east, so degrees west maps inversely to 180-360
                location_x = 360 + location.x if location.x < 0 else location.x

                latidx = (numpy.abs(location_y - latarr)).argmin()
                lonidx = (numpy.abs(location_x - lonarr)).argmin()

                cell_indexes.add((latidx, lonidx))
                location_to_coords[location.id] = (latarr[latidx], lonarr[lonidx])

            # Use numpy to get a list of var_data[*][lat][lon] for each referenced cell
            cell_data = {}
            for (latidx, lonidx) in cell_indexes:
                values = list(var_data[:, latidx, lonidx])
                # Our DB assumes that leap years have 366 values in their ArrayFields.
                #   If we're woking with a calendar that doesn't consider leap years on a leap year,
                #   insert None for Feb 29
                if calendar.isleap(year) and len(values) == 365:
                    values.insert(DAY_OF_YEAR_FEB_29, None)
                cell_data[(latarr[latidx], lonarr[lonidx])] = values

        return location_to_coords, cell_data

    def process_netcdf_object(self, downloader, var):
        """Download and process a single NetCDF results file."""
        # Download data to a temporary file, using a context manager to ensure it gets cleaned up
        with tempfile.NamedTemporaryFile() as fp:
            path = fp.name
            downloader.download(
                self.logger,
                self.datasource.scenario.name,
                self.datasource.model.name,
                self.datasource.year,
                var,
                path
            )
            return self.get_var_data(var, path)

    def process_netcdf_variables(self):
        """Fetch and merge the NetCDF variables into a single dictionary keyed by coordinate."""
        # Choose the downloader for the dataset, to compensate for dataset-specific naming schemes
        downloader = get_netcdf_downloader(self.datasource.dataset.name)

        # Parse each NetCDF file into useable data keyed by its variable
        variable_data = {}
        # In case any of the NetCDF files had different cities than any other, merge their
        # city coordinate mappings into a single dict
        city_coords = {}
        for var in ClimateDataYear.VARIABLE_CHOICES:
            city_to_coords, cell_data = self.process_netcdf_object(downloader, var)
            city_coords.update(city_to_coords)
            variable_data[var] = cell_data

        # Group the distinct variable data sets by coordinate
        data_by_coords = self.collate_variable_data(variable_data)

        return city_coords, data_by_coords

    def collate_variable_data(self, variable_data):
        """Collate the initial per-variable result into a per-coordinate dictionary."""
        # Convert data from {variable: {(coords): [data]}}
        # to {(coords): {variable: [data]}}
        data_by_coords = collections.defaultdict(dict)
        for variable, results in variable_data.items():
            for coords, data in results.items():
                data_by_coords[coords][variable] = data
        return data_by_coords

    def load_map_cell_models(self, data_coords):
        """Load a dictionary of ClimateDataCell by coordinate, creating new objects as needed."""
        # Load all of the map cells that already exist
        cell_models = {(cell.lat, cell.lon): cell for cell in ClimateDataCell.objects.all()}

        # For any coordinates that aren't represented, create a new object
        missing_coords = (coord for coord in data_coords if coord not in cell_models)
        for coords in missing_coords:
            # This cell is not in the database, we should create it
            lat, lon = coords
            # Use get_or_create() just in case another process beat us to the punch
            cell_model, cell_model_created = ClimateDataCell.objects.get_or_create(
                lat=lat.item(),
                lon=lon.item()
            )
            cell_models[coords] = cell_model
            if cell_model_created:
                self.logger.info('Created map_cell at (%s, %s)', lat.item(), lon.item())
        return cell_models

    def save_climate_data_year(self, coordinates, climate_results, cell_models):
        assert(set(climate_results.keys()) == ClimateDataYear.VARIABLE_CHOICES)

        # If appropriate ClimateDataYear object exists, update data
        # Otherwise create it
        cell_model = cell_models[coordinates]
        if self.update_existing:
            _, created = ClimateDataYear.objects.update_or_create(
                map_cell=cell_model,
                data_source=self.datasource,
                defaults=climate_results
            )
        else:
            try:
                ClimateDataYear.objects.create(
                    map_cell=cell_model,
                    data_source=self.datasource,
                    **climate_results
                )
                created = True
            except IntegrityError:
                created = False

        if created:
            self.logger.info('Created ClimateDataYear record for ' +
                             'datasource: %s, map_cell: %s',
                             self.datasource,
                             cell_model)
        elif self.update_existing:
            self.logger.debug('Updated ClimateDataYear record ' +
                              'for datasource: %s, map_cell: %s',
                              self.datasource,
                              cell_model)

    def update_city_map_cell(self, city, city_coords, cell_models):
        try:
            cell_coords = city_coords[city.id]
        except KeyError:
            self.logger.warning('ClimateDataCityCell update SKIPPED for {}. City wasn\'t modified.'
                                .format(city.id))
            return
        cell_model = cell_models[cell_coords]
        try:
            city_cell, created = ClimateDataCityCell.objects.get_or_create(
                city=city,
                dataset=self.datasource.dataset,
                map_cell=cell_model
            )

            if created:
                self.logger.info('Created new ClimateDataCityCell for '
                                 'city %s dataset %s map_cell %s',
                                 city.id, self.datasource.dataset.name, str(cell_model))
            else:
                assert(city_cell.map_cell.id == cell_model.id)
        except IntegrityError:
            # City and dataset are unique constraints, so an IntegrityError means our
            #  map_cell is different from the city's existing one, which is very bad.
            self.logger.warning('ClimateDataCityCell NOT created for '
                                'city %s dataset %s map_cell %s',
                                city.id, self.datasource.dataset.name, str(cell_model))

    def import_netcdf_data(self):
        """Extract data about cities from three NetCDF files and writes it to the database."""
        self.logger.debug("Using datasource: %s", self.datasource)

        if not self.locations:
            self.logger.warning("No locations need import for datasource {}, quitting early."
                                .format(self.datasource))
            return

        # Combine the separate NetCDF files into useable results
        # - city_coords as a single mapping of city ID to map cell coordinates
        # - data_by_coords as a dictionary of {coord: {variable: [data]}}
        city_coords, data_by_coords = self.process_netcdf_variables()

        # Make or load ClimateDataCell models for each coordinate set we have
        cell_models = self.load_map_cell_models(data_by_coords.keys())

        # Save the raw climate data to database
        self.logger.debug('Saving to database')
        for coords, results in data_by_coords.items():
            self.save_climate_data_year(coords, results, cell_models)

        # Go through all the cities and update their ClimateDataCityCell representations
        # Ensuring only one entry exists for a given city and dataset
        self.logger.debug('Updating cities')
        for city in City.objects.all().order_by('pk'):
            self.update_city_map_cell(city, city_coords, cell_models)

        # note job completed successfully
        self.datasource.import_completed = True
        self.datasource.save()
        self.logger.info('nex2db processing done')
