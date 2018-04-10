import calendar
import logging
import collections
import tempfile
import boto3

from django.db.utils import IntegrityError

import numpy
import netCDF4

from .models import City, ClimateDataCell, ClimateDataCityCell, ClimateDataYear, ClimateDataSource

DAY_OF_YEAR_FEB_29 = 60
BUCKET = 'nasanex'


logger = logging.getLogger('climate_data')


class NetCdfDownloader(object):
    """Generic class for downloading a NetCDF object from S3 to a target path."""

    def get_object_key_format(self):
        raise NotImplementedError()

    def get_model_ensemble(self, model, rcp):
        raise NotImplementedError()

    def get_object_key(self, model, rcp, year, var):
        ensemble = self.get_model_ensemble(model, rcp)
        key_format = self.get_object_key_format()
        return key_format.format(
            rcp=rcp.lower(),
            model=model,
            year=year,
            var=var,
            ensemble=ensemble
        )

    def download(self, logger, rcp, model, year, var, filename):
        key = self.get_object_key(model, rcp, year, var)

        s3 = boto3.resource('s3')
        logger.warning('Downloading file: s3://{}/{}'.format(BUCKET, key))
        s3.meta.client.download_file(BUCKET, key, filename)


class GddpNetCdfDownloader(NetCdfDownloader):
    """Specialized NetCdfDownloader for downloading GDDP-originated S3 objects from S3."""

    def get_object_key_format(self):
        return ('NEX-GDDP/BCSD/{rcp}/day/atmos/{var}/{ensemble}/v1.0/'
                '{var}_day_BCSD_{rcp}_{ensemble}_{model}_{year}.nc')

    def get_model_ensemble(self, model, rcp):
        return 'r1i1p1'


class LocaNetCdfDownloader(NetCdfDownloader):
    """Specialized NetCdfDownloader for downloading LOCA-originated S3 objects from S3."""

    def get_object_key_format(self):
        return ('LOCA/{model}/16th/{rcp}/{ensemble}/{var}/'
                '{var}_day_{model}_{rcp}_{ensemble}_{year}0101-{year}1231.LOCA_2016-04-02.16th.nc')

    def get_model_ensemble(self, model, rcp):
        """Return ensemble given LOCA model and scenario."""
        ensembles = {
            'historical': {
                'CCSM4': 'r6i1p1',
                'GISS-E2-H': 'r6i1p1',
                'GISS-E2-R': 'r6i1p1',
            },
            'RCP45': {
                'CCSM4': 'r6i1p1',
                'EC-EARTH': 'r8i1p1',
                'GISS-E2-H': 'r6i1p3',
                'GISS-E2-R': 'r6i1p1'
            },
            'RCP85': {
                'CCSM4': 'r6i1p1',
                'EC-EARTH': 'r2i1p1',
                'GISS-E2-H': 'r2i1p1',
                'GISS-E2-R': 'r2i1p1'
            }
        }
        try:
            return ensembles[rcp][model]
        except KeyError:
            return 'r1i1p1'


def get_netcdf_downloader(dataset):
    downloader_class = {
        'LOCA': LocaNetCdfDownloader,
        'NEX-GDDP': GddpNetCdfDownloader
    }[dataset]
    return downloader_class()


class Nex2DB(object):
    """Import data from NetCDF files to database."""

    # cache list of cites to guarantee ordering during import
    cities = None
    # Datasource object representing the source we intend to import
    datasource = None
    # Boolean flag designating if we should update existing entries or only insert new
    update_existing = False

    def __init__(self, dataset, scenario, model, year, update_existing=False, logger=None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.update_existing = update_existing

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
        cities_queryset = City.objects.all().order_by('pk')
        if not self.update_existing:
            # Only process cities that don't have this datasource loaded
            cities_queryset = cities_queryset.exclude(
                map_cell_set__map_cell__climatedatayear__data_source=datasource
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

            # read variable data into memory
            var_data = ds.variables[var_name][:, :, :]  # :,:,: loads everything into ram
            assert ds.variables[var_name].shape == var_data.shape

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
                values = list(var_data[:, latidx, lonidx])
                # Our DB assumes that leap years have 366 values in their ArrayFields.
                #   If we're woking with a calendar that doesn't consider leap years on a leap year,
                #   insert None for Feb 29
                if calendar.isleap(year) and len(values) == 365:
                    values.insert(DAY_OF_YEAR_FEB_29, None)
                cell_data[(latarr[latidx], lonarr[lonidx])] = values

        return city_to_coords, cell_data

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

    def save_climate_data_year(self, data_by_coords, cell_models):
        # Go through the collated list and create all the relevant datapoints
        self.logger.debug('Saving to database')

        for coords, results in data_by_coords.items():
            assert(set(results.keys()) == ClimateDataYear.VARIABLE_CHOICES)

            # If appropriate ClimateDataYear object exists, update data
            # Otherwise create it
            cell_model = cell_models[coords]
            if self.update_existing:
                _, created = ClimateDataYear.objects.update_or_create(
                    map_cell=cell_model,
                    data_source=self.datasource,
                    defaults=results
                )
            else:
                try:
                    ClimateDataYear.objects.create(
                        map_cell=cell_model,
                        data_source=self.datasource,
                        **results
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

    def update_city_map_cells(self, city_coords, cell_models):
        self.logger.debug('Combining city list')

        # Go through all the cities and update their ClimateDataCityCell representations
        # Ensuring only one entry exists for a given city and dataset
        self.logger.debug('Updating cities')
        for city in self.cities:
            cell_coords = city_coords[city.id]
            cell_model = cell_models[cell_coords]
            try:
                _, created = ClimateDataCityCell.objects.get_or_create(
                    city=city,
                    dataset=self.datasource.dataset,
                    map_cell=cell_model
                )

                if created:
                    self.logger.info('Created new ClimateDataCityCell for '
                                     'city %s dataset %s map_cell %s',
                                     city.id, self.datasource.dataset.name, str(cell_model))
            except IntegrityError:
                # City and dataset are unique constraints, so an IntegrityError means our
                #  map_cell is different from the city's existing one, which is very bad.
                self.logger.warning('ClimateDataCityCell NOT created for '
                                    'city %s dataset %s map_cell %s',
                                    city.id, self.datasource.dataset.name, str(cell_model))

    def import_netcdf_data(self):
        """Extract data about cities from three NetCDF files and writes it to the database."""
        self.logger.debug("Using datasource: %s", self.datasource)

        if not self.cities:
            self.logger.warning("No cities need import for datasource {}, quitting early.".format(
                self.datasource))
            return

        # Combine the separate NetCDF files into useable results
        # - city_coords as a single mapping of city ID to map cell coordinates
        # - data_by_coords as a dictionary of {coord: {variable: [data]}}
        city_coords, data_by_coords = self.process_netcdf_variables()

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
