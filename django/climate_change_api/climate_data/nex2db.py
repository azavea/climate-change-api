import os
import datetime
import gc
import logging
import sys

import numpy
import netCDF4

from models import City, ClimateData

logger = logging.getLogger()

CITIES = list(City.objects.all())


def get_var_data(var_name, path):
    """
    Read out data from a NetCDF file and return its data, translated, for only the points
    representing the cities in the database.

    @param var_name Name of the variable in this NetCDF (tasmin, tasmax, or pr)
    @param path Full path to the NetCDF file on disk

    @returns Object containing:
        cities: matrix of variable readings for nearest point to each city, where offsets correspond
                to those in CITIES; each city entry contains a list of readings for dates
        dates: map of each date for which there is a reading to the offset for that reading in the
               list of readings for the city
    """

    # data in the climate NetCDF files can be referenced as:
    # ds.variables[var name][day of year index][latitude index][longitude index]
    logging.debug('processing NetCDF at %s', path)
    sys.stdout.flush()

    with netCDF4.Dataset(path, 'r') as ds:
        latarr = numpy.asarray(ds.variables['lat'])
        lonarr = numpy.asarray(ds.variables['lon'])
        time_unit = ds.variables['time'].units
        # using non-standard calendar
        calendar = ds.variables['time'].calendar

        # build map of converted date-time values to its array index in the variable values
        dates = {}
        for i, numdays in enumerate(ds.variables['time']):
            dates[netCDF4.num2date(numdays, time_unit, calendar=calendar).date()] = i

        # flip right side up by reversing range
        latarr = 90.0 - (90.0 + latarr)
        # shift range from (0 to 360) to (-180 to 180)
        lonarr = lonarr - 180

        # read variable data into memory
        var_data = numpy.asarray(ds.variables[var_name])
        num_vars = len(var_data)

    # map city ID to its values for each day
    city_vals = []
    for city in CITIES:
        logging.debug('processing variable %s for city: %s', var_name, city.name)
        sys.stdout.flush()

        # Not geographic distance, but good enough for
        # finding a point near a city center from disaggregated data.
        latidx = (numpy.abs(city.geom.y - latarr)).argmin()
        lonidx = (numpy.abs(city.geom.x - lonarr)).argmin()

        city_vals.append([var_data[i][latidx][lonidx] for i in range(num_vars)])

    return {'cities': city_vals, 'dates': dates}


def days_in_year(year):
    """
    Generator that yields each day in the year as a date object

    @param Year as int
    """
    first_of_year = datetime.date(year=year, month=1, day=1)
    last_of_year = datetime.date(year=year, month=12, day=31)
    delta = datetime.timedelta(days=1)

    dt = first_of_year
    while dt <= last_of_year:
        yield dt
        dt += delta


def get_date_val(var_data, city_index, date):
    """
    Helper to look up variable value for a given date and city, if an entry for that date exists

    @param var_data Object returned by get_var_data
    @param city_index Offset of the city to reference in CITIES list
    @param date Day of variable reading to get

    @returns Variable reading for given city and day, or None if no reading for that day
    """
    val = None
    date_index = var_data['dates'].get(date)
    if date_index:
        val = var_data['cities'][city_index][date_index]
    return val


def nex2db(tasmin_path, tasmax_path, pr_path, data_source):
    """
    Extracts data about cities from three NetCDF files and writes it to the database

    @param tasmin_path Path to NetCDF with tasmin readings for the data source model/scenario/year
    @param tasmax_path Path to NetCDF with tasmax readings for the data source model/scenario/year
    @param pr_path Path to NetCDF with pr readings for the data source model/scenario/year
    @param data_source ClimateDataSource object that defines the source model, scenario, and year
    """
    tasmin = get_var_data('tasmin', tasmin_path)
    tasmax = get_var_data('tasmax', tasmax_path)
    pr = get_var_data('pr', pr_path)

    for i, city in enumerate(CITIES):
        to_insert = []
        for day_of_year, date in enumerate(days_in_year(int(data_source.year))):
            to_insert.append(ClimateData(city=city,
                                         day_of_year=day_of_year + 1,
                                         data_source=data_source,
                                         tasmin=get_date_val(tasmin, i, date),
                                         tasmax=get_date_val(tasmax, i, date),
                                         pr=get_date_val(pr, i, date)))

        ClimateData.objects.bulk_create(to_insert)

    logging.info('nex2db processing done')
    sys.stdout.flush()
