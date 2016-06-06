Climate Change API
==================

Development Environment
-----------------------

In order to develop on this project, you'll need to setup an AWS ``climate`` profile. First,
sign into your user in the azavea-climate AWS account and create a set of access keys.

Then, run ``aws configure --profile climate`` and follow the prompts.

Once your AWS profile is setup, run these commands to configure the VM::

    vagrant up
    vagrant ssh
    cd climate-change-api
    docker-compose up

The Django app will be exposed on port 8080.

All further commands assume you are first in the directory ``~/climate-change-api`` inside the vagrant vm.


Documentation
-------------

Documentation for the API can be built with::

    ./scripts/docs

Then it can be served with::

    ./scripts/serve docs

and viewed at http://localhost:8088


Django Management commands
--------------------------

To run Django management commands, use the console helper script::

    ./scripts/console django './manage.py migrate'

Django runserver can be found on port 8082. Have the project running, in another terminal window inside the VM execute::

    docker exec -it climatechangeapi_django_1 /bin/bash

    ./manage.py runserver 0.0.0.0:8082

and view at http://localhost:8082
