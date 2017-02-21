#!/usr/bin/python3

from functools import partial
import os

from locust import HttpLocust, TaskSet, task

CITY_ID = os.getenv('LOAD_TEST_CITY_ID') or 1
SCENARIO = os.getenv('LOAD_TEST_SCENARIO') or 'RCP85'

DEFAULT_THRESHOLD_PARAMS = {
    'threshold': 100,
    'threshold_comparator': 'lte',
    'threshold_units': 'F'
}


def general_indicator_query(locust_object, indicator, params):
    locust_object.client.get('/api/climate-data/{city}/{scenario}/indicator/{indicator}'.format(
        city=CITY_ID, scenario=SCENARIO, indicator=indicator),
        headers=locust_object.headers,
        params=params,
        name='{indicator} {agg}'.format(indicator=indicator,
                                        agg=params.get('time_aggregation', '')))


class UserBehavior(TaskSet):

    def build_indicator_queries(self):
        """
        Add a load test query for each indciator / time aggregation
        """
        indicators = self.client.get('/api/indicator/',
                                     headers=self.headers).json()
        for indicator in indicators:
            indicator_name = indicator['name']
            if indicator_name.endswith('threshold'):
                params = DEFAULT_THRESHOLD_PARAMS
                if indicator_name.find('precepitation') > -1:
                    params['threshold_units'] = 'in'
                self.tasks.append(partial(general_indicator_query,
                                          indicator=indicator_name,
                                          params=params))
            else:
                # for non-threshold indicators, test all non-custom aggregation levels
                for agg in indicator['valid_aggregations']:
                    if agg != 'custom':
                        self.tasks.append(partial(general_indicator_query,
                                                  indicator=indicator_name,
                                                  params={'time_aggregation': agg}))

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
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
        self.client.get('/', headers=self.headers)

    @task(1)
    def api_main(self):
        self.client.get('/api/', headers=self.headers)

    @task(1)
    def scenarios(self):
        self.client.get('/api/scenario/', headers=self.headers)

    @task(1)
    def scenario_details(self):
        self.client.get('/api/scenario/{scenario}/'.format(scenario=SCENARIO), headers=self.headers)

    @task(1)
    def cities(self):
        self.client.get('/api/city/', headers=self.headers)

    @task(1)
    def city_data(self):
        self.client.get('/api/climate-data/{city}/{scenario}/'.format(city=CITY_ID,
                                                                      scenario=SCENARIO),
                        headers=self.headers)

    @task(1)
    def projects(self):
        self.client.get('/api/project/', headers=self.headers)

    @task(1)
    def climate_models(self):
        self.client.get('/api/climate-model/', headers=self.headers)

    @task(1)
    def climate_model_detail(self):
        self.client.get('/api/climate-model/ACCESS1-0/', headers=self.headers)

    @task(1)
    def indicator_list(self):
        self.client.get('/api/indicator/', headers=self.headers)


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000
