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

    @task(2)
    def index(self):
        resp = self.client.get("/", headers=self.headers)
        print(resp)

    @task(1)
    def profile(self):
        resp = self.client.get("/api/", headers=self.headers)
        print(resp)
        print(resp.json())


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000
