import datetime
import logging
import collections

import numpy
import netCDF4

from models import City, ClimateData, ClimateDataCell
from django.db import IntegrityError

logger = logging.getLogger()


class Nex2DB(object):
    """
    Import data from NetCDF files to database
    """

    # cache list of cites to guarantee ordering during import
    cities = None

    def get_cities(self):
        if not self.cities:
            self.cities = list(City.objects.all().order_by('pk'))
        return self.cities

    def netcdf2date(self, value, time_unit, calendar):
        parsed = netCDF4.num2date(value, time_unit, calendar=calendar)
        try:
            return parsed.date()
        except AttributeError:
            # We got a netcdftime object, which doesn't have a date() method.
            # However, it does have timetuple(), which gives (year, month, day, [...])
            timetuple = parsed.timetuple()
            # We only want the first three, which we can give to datetime.date
            return datetime.date(*timetuple[0:3])

    def get_var_data(self, var_name, path):
        """
        Read out data from a NetCDF file and return its data, translated, for only the points
        representing the cities in the database.

        @param var_name Name of the variable in this NetCDF (tasmin, tasmax, or pr)
        @param path Full path to the NetCDF file on disk

        @returns Object containing:
            cells: map of cells by coordinate tuple to dictionary of variable values
                   keyed by corresponding date
            cities: map of each city by internal ID to the cell coordinates it matched to
        """

        # data in the climate NetCDF files can be referenced as:
        # ds.variables[var name][day of year index][latitude index][longitude index]
        logging.debug('processing NetCDF at %s', path)
        with netCDF4.Dataset(path, 'r') as ds:
            latarr = numpy.asarray(ds.variables['lat'])
            lonarr = numpy.asarray(ds.variables['lon'])
            time_unit = ds.variables['time'].units
            # using non-standard calendar
            calendar = ds.variables['time'].calendar

            # build map of converted date-time values to its array index in the variable values
            dates = [self.netcdf2date(numdays, time_unit, calendar=calendar)
                     for numdays in ds.variables['time']]

            # read variable data into memory
            var_data = ds.variables[var_name]

            cell_idx = set()
            city_to_coords = {}
            for city in self.get_cities():
                logging.debug('processing variable %s for city: %s', var_name, city.name)
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
            cell_data = {(latarr[latidx], lonarr[lonidx]):  # Key on actual coordinates
                         dict(zip(dates, list(var_data[:, latidx, lonidx])))  # netcdf slicing
                         for (latidx, lonidx) in cell_idx}

        return {'cities': city_to_coords, 'cells': cell_data}

    def nex2db(self, variable_paths, data_source):
        """
        Extracts data about cities from three NetCDF files and writes it to the database

        @param variable_paths Dictionary of variable identifier to path for the corresponding NetCDF file
        @param data_source ClimateDataSource object that defines the source model/scenario/year
        """

        assert(set(variable_paths) == ClimateData.VARIABLE_CHOICES)

        variable_data = {label: self.get_var_data(label, path)
                         for label, path in variable_paths.iteritems()}

        # Collate the variables into one list keyed by coordinates
        cell_list = {}
        city_coords = {}
        logger.debug("Collating results")
        for label, results in variable_data.iteritems():
            for coords, timeseries_data in results['cells'].iteritems():
                if coords not in cell_list:
                    cell_list[coords] = collections.defaultdict(dict)

                for date, value in timeseries_data.iteritems():
                    cell_list[coords][date].update({
                        label: value
                    })

            city_coords.update(results['cities'])

        # Go through the collated list and create all the relevant datapoints
        logger.debug("Creating database entries")

        # Load all of the map cells that already exist
        cell_models = {(cell.lat, cell.lon): cell for cell in ClimateDataCell.objects.all()}

        for coords, timeseries_data in cell_list.iteritems():
            (lat, lon) = coords
            try:
                cell_model = cell_models[coords]
            except KeyError:
                # This cell is not in the database, we should create it
                cell_model, created = ClimateDataCell.objects.get_or_create(
                    lat=lat.item(),
                    lon=lon.item()
                )
                cell_models[coords] = cell_model

            climatedata_list = []
            for date, values in timeseries_data.iteritems():
                # Testing, ensure that we have values for all variables
                # (set(dict) produces an unordered set of keys, no values)
                assert(set(values) == ClimateData.VARIABLE_CHOICES)

                # Use a dictionary since some of ClimateData's keyword args
                # are variable defined
                climatedata_args = {
                    'map_cell': cell_model,
                    'day_of_year': date.timetuple().tm_yday,
                    'data_source': data_source,
                }
                # Attach the datapoints for this date to the args
                climatedata_args.update(values)

                # Create the ClimateData entry
                climatedata_list.append(
                    ClimateData(**climatedata_args)
                    )

            ClimateData.objects.bulk_create(climatedata_list)

        # Go through all the cities and set their map_cell to the appropriate model
        logger.debug("Updating cities")
        for city in self.get_cities():
            coords = city_coords[city.id]
            cell_model = cell_models[coords]
            if city.map_cell:
                assert(city.map_cell == cell_model)
            else:
                city.map_cell = cell_model
                city.save()

        logging.info('nex2db processing done')
