#!/usr/bin/env python

import os

from locust import HttpLocust, TaskSet, task


class UserBehavior(TaskSet):
    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        print('starting locust...')
        token = os.getenv('API_TOKEN')
        if not token:
            raise ValueError('Must set API_TOKEN on environment to run load tests.')
        self.headers = {'Authorization': 'Token {token}'.format(token=token)}

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
        self.client.get('/api/scenario/RCP85/', headers=self.headers)

    @task(1)
    def cities(self):
        self.client.get('/api/city/', headers=self.headers)

    @task(1)
    def city_data(self):
        self.client.get('/api/climate-data/1/RCP85/', headers=self.headers)

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

    @task(1)
    def avg_high_temp(self):
        self.client.get('/api/climate-data/14/RCP45/indicator/average_high_temperature/',
                        headers=self.headers)

    @task(1)
    def avg_high_temp_monthly(self):
        self.client.get('/api/climate-data/14/RCP45/indicator/average_high_temperature/',
                        params={'time_aggregation': 'monthly'}, headers=self.headers)

    @task(1)
    def avg_high_temp_daily(self):
        self.client.get('/api/climate-data/14/RCP45/indicator/average_high_temperature/',
                        params={'time_aggregation': 'daily'}, headers=self.headers)


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000
