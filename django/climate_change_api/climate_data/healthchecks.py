"""Check for missing or incompletely imported data for watchman healthcheck endpoint."""

import itertools
import logging

from django.db.models import Count

from watchman.decorators import check

from climate_data.models import (City,
                                 ClimateDataSource,
                                 ClimateModel,
                                 Scenario)


logger = logging.getLogger(__name__)


@check
def _check_city_cells():
    """Check for cities that have no associated map cell."""
    missing = City.objects.filter(map_cell=None).values('name', 'admin')
    if not missing.count():
        return {'ok': True}
    return {'ok': False, 'error': 'MissingCityCells', 'stacktrace': list(missing)}


@check
def _check_incomplete_imports():
    """
    Check for partially completed imports.

    Find data sources created, but for which data import did not finish successfully.
    """
    missing = ClimateDataSource.objects.filter(import_completed=False).values('year',
                                                                              'model',
                                                                              'scenario')
    if not missing.count():
        return {'ok': True}
    return {'ok': False, 'error': 'IncompleteClimateDataSources', 'stacktrace': list(missing)}


@check
def _check_missing_data_sources():
    """
    Check for missing data sources.

    Expect that every combination of year/model/scenario to have a source for which there is any
    source for that year, model, or scenario.
    """
    # first do a simple check of counts to see if anything is missing
    expect = ClimateDataSource.objects.aggregate(expected_total=(Count('year', distinct=True) *
                                                                 Count('model', distinct=True) *
                                                                 Count('scenario', distinct=True)))
    if ClimateDataSource.objects.all().count() == expect.get('expected_total'):
        return {'ok': True}

    # If got this far, at least one expected data source is not present. Find them all.
    distinct_years = ClimateDataSource.objects.distinct('year').values_list('year', flat=True)
    distinct_models = ClimateDataSource.objects.distinct('model').values_list('model', flat=True)
    distinct_scenarios = ClimateDataSource.objects.distinct('scenario').values_list('scenario',
                                                                                    flat=True)
    # expect to see a source for every combination of each year, model, and scenario present
    expected_set = set()
    [expected_set.add(tuple(x)) for x in itertools.product(distinct_years,
                                                           distinct_models,
                                                           distinct_scenarios)]

    # every year/model/scenario for which there is a source
    source_set = set(ClimateDataSource.objects.values_list('year', 'model', 'scenario'))

    # will output set of tuples of missing year/model/scenario sources
    missing = expected_set.difference(source_set)

    # list of missing data sources to return
    response = []
    for year, model, scenario in missing:
        model = ClimateModel.objects.get(id=model)
        scenario = Scenario.objects.get(id=scenario)
        response.append({'year': year, 'scenario': scenario.name, 'model': model.name})
    return {'ok': False, 'error': 'MissingClimateDataSources', 'stacktrace': response}


def city_cells():
    return {'city_cells': _check_city_cells()}


def import_completion():
    return {'data_sources_import_completion': _check_incomplete_imports()}


def data_sources_present():
    return {'data_sources_present': _check_missing_data_sources()}