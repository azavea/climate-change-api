"""Check for missing or incompletely imported data for check endpoint."""

import itertools
import logging

from django.db.models import Count

from climate_data.models import (City,
                                 ClimateDataSource,
                                 ClimateModel,
                                 Scenario)


logger = logging.getLogger(__name__)


def check_city_cells():
    """Check for cities that have no associated map cell."""
    missing = City.objects.filter(map_cell=None).values('name', 'admin')
    return {'missing_city_cells': list(missing)}


def check_incomplete_imports():
    """
    Check for partially completed imports.

    Find data sources created, but for which data import did not finish successfully.
    """
    missing = ClimateDataSource.objects.filter(import_completed=False).values('year',
                                                                              'model',
                                                                              'scenario')
    return {'incomplete_imports': list(missing)}


def check_missing_data_sources():
    """
    Check for missing data sources.

    Expect that every combination of year/model/scenario to have a source for which there is any
    source for that year, model, or scenario.
    """
    distinct_models = ClimateDataSource.objects.distinct('model').values_list('model', flat=True)
    historical_scenario = Scenario.objects.filter(name='historical').values_list('id', flat=True)
    future_scenarios = (ClimateDataSource.objects.distinct('scenario')
                                                 .exclude(scenario=historical_scenario)
                                                 .values_list('scenario', flat=True))

    # convert years to strings because ints are not iterable
    historical_years = [str(x) for x in set(range(1950, 2006))]
    future_years = [str(x) for x in set(range(2006, 2101))]

    expected_historic = len(distinct_models) * len(historical_scenario) * len(historical_years)
    expected_future = len(distinct_models) * len(future_scenarios) * len(future_years)
    expected_total = expected_historic + expected_future

    # first do a simple check of counts to see if anything is missing
    if ClimateDataSource.objects.all().count() == expected_total:
        return {'missing_data_sources': []}

    # If got this far, at least one expected data source is not present. Find them all.
    # expect to see a source for every combination of each year, model, and scenario present
    expected_set = set()
    [expected_set.add(tuple(x)) for x in itertools.product(historical_years,
                                                           distinct_models,
                                                           historical_scenario)]

    [expected_set.add(tuple(x)) for x in itertools.product(future_years,
                                                           distinct_models,
                                                           future_scenarios)]

    # convert years back to int
    expected_set = set((int(item[0]), item[1], item[2]) for item in expected_set)

    # every year/model/scenario for which there is a source
    source_set = ClimateDataSource.objects.values_list('year', 'model', 'scenario')

    # will output set of tuples of missing year/model/scenario sources
    missing = expected_set.difference(source_set)

    # list of missing data sources to return
    response = []
    for year, model, scenario in missing:
        model = ClimateModel.objects.get(id=model)
        scenario = Scenario.objects.get(id=scenario)
        response.append({'year': year, 'scenario': scenario.name, 'model': model.name})
    return {'missing_data_sources': response}


def check_data():
    """Return the results of all data status checks in a single object."""
    return {'status': [check_city_cells(),
                       check_incomplete_imports(),
                       check_missing_data_sources()]}
