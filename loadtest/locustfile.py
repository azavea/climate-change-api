#!/usr/bin/python3

from functools import partial
import os

from locust import HttpLocust, TaskSet, task

CITY_ID = os.getenv('LOAD_TEST_CITY_ID') or 1
SCENARIO = os.getenv('LOAD_TEST_SCENARIO') or 'RCP85'

DEFAULT_PARAMS = {
    'noCache': 'True'
}

DEFAULT_THRESHOLD_PARAMS = {
    'threshold': 100,
    'threshold_comparator': 'lte',
    'threshold_units': 'F',
    'noCache': 'True'
}


def general_indicator_query(locust_object, indicator, params):
    locust_object.client.get('/api/climate-data/{city}/{scenario}/indicator/{indicator}/'.format(
        city=CITY_ID, scenario=SCENARIO, indicator=indicator),
        headers=locust_object.headers,
        params=params,
        name='{indicator} {agg}'.format(indicator=indicator,
                                        agg=params.get('time_aggregation', '')))


class UserBehavior(TaskSet):

    def get_api_url(self, url):
        """ Helper for querying API with authorization header"""
        self.client.get(url, headers=self.headers, params={'noCache': 'True'}, name=url)

    def build_indicator_queries(self):
        """Add a load test query for each indciator / time aggregation"""
        indicators = self.client.get('/api/indicator/',
                                     headers=self.headers).json()
        for indicator in indicators:
            indicator_name = indicator['name']
            if indicator_name.endswith('threshold'):
                params = DEFAULT_THRESHOLD_PARAMS.copy()
                if indicator_name.find('precipitation') > -1:
                    params['threshold_units'] = 'in'
            else:
                params = DEFAULT_PARAMS.copy()

            # vary all the available aggregations
            for agg in indicator['valid_aggregations']:
                if agg != 'custom':
                    agg_params = params.copy()
                    agg_params['time_aggregation'] = agg

                    self.tasks.append(partial(general_indicator_query,
                                              indicator=indicator_name,
                                              params=agg_params))

    def on_start(self):
        """Run tasks before any task is scheduled"""
        print('starting locust...')
        token = os.getenv('API_TOKEN')
        if not token:
            raise ValueError('Must set API_TOKEN on environment to run load tests.')
        self.headers = {'Authorization': 'Token {token}'.format(token=token)}
        print('adding indciator queries...')
        indicator_tasks = TaskSet(self)
        self.build_indicator_queries()
        print('ready to go!')

    @task(1)
    def index(self):
        self.get_api_url('/')

    @task(1)
    def scenarios(self):
        self.get_api_url('/api/scenario/')

    @task(1)
    def scenario_details(self):
        self.get_api_url('/api/scenario/{scenario}/'.format(scenario=SCENARIO))

    @task(1)
    def cities(self):
        self.get_api_url('/api/city/')

    @task(1)
    def city_data(self):
        self.get_api_url('/api/climate-data/{city}/{scenario}/'.format(city=CITY_ID,
                                                                       scenario=SCENARIO))

    @task(1)
    def projects(self):
        self.get_api_url('/api/project/')

    @task(1)
    def climate_models(self):
        self.get_api_url('/api/climate-model/')

    @task(1)
    def climate_model_detail(self):
        self.get_api_url('/api/climate-model/ACCESS1-0/')

    @task(1)
    def indicator_list(self):
        self.get_api_url('/api/indicator/')

    @task(1)
    def indicator_detail(self):
        self.get_api_url('/api/indicator/frost_days/')


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000
