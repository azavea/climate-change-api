Climate Change API
==================

Development Environment
-----------------------

In order to develop on this project, you'll need to setup an AWS ``climate`` profile. First,
sign into your user in the azavea-climate AWS account and create a set of access keys.

Then, run ``aws configure --profile climate`` and follow the prompts.

Once your AWS profile is setup, run the following to configure the VM::

    ./scripts/setup

Next, ssh into the VM with ``vagrant ssh``. Then run::

    ./scripts/console django './manage.py createsuperuser'

and follow the prompts to create an initial user to login with.

Once you have a new user, run ``./scripts/server`` inside the VM to begin serving the application on port 8080.

This project conforms to the specification provided by `Azaveas Scripts to Rule Them All`_.


Running Tests
-------------

Run Django tests with::

    ./scripts/console django './manage.py test --settings climate_change_api.settings_test'


Load Testing
------------

The ``loadtest`` Docker container can be used to test API query response times using `locust <http://locust.io/>`_.

First set the environment variable ``API_TOKEN`` within the VM to a valid user token with::

    export API_TOKEN=<user token>

Optionally, the target server to test may be configured to target the local instance with::

    export API_HOST=http://localhost:8082

By default, the staging server will be targeted.

Then start the Docker container with::

    docker-compose up loadtest

Naviagate to http://localhost:8089 and start tests by setting the swarm and hatch rate (1 for each is fine). To stop tests, click the red button in the web UI (or halt the container).


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


Getting Data
------------

Once you have your environment set up, you need data. There are two methods available for importing climate data: Import from the raw NetCDF, or import from another ClimateChangeAPI instance.


Loading Data from NetCDF
''''''''''''''''''''''''

Run migrations::

    ./scripts/console django './manage.py migrate'


Load scenario and climate model data::

    ./scripts/console django './manage.py loaddata scenarios'
    ./scripts/console django './manage.py loaddata climate-models'


Load cities::

    ./scripts/console django './manage.py import_cities azavea-climate-sandbox geonames_cities_top200_us.geojson'

    Alternatively, load geonames_cities1000_us.geojson for more data.


Create a data processing job. Note that if a previous job has been run for the same parameters, the `ClimateDataSource` object it created will need to be deleted first::

    ./scripts/console django './manage.py create_jobs RCP45 ACCESS1-0 2050'

Process the job::

    ./scripts/console django './manage.py run_jobs'


Loading Data From Staging
'''''''''''''''''''''''''

Run migrations::

    ./scripts/console django './manage.py migrate'

Make sure database is clear for importing data::

    ./scripts/console django './manage.py shell_plus'
    ClimateDataCell.objects.all().delete()
    ClimateDataSource.objects.all().delete()

Import data (10 models, 100 cities)::

    ./scripts/console django './manage.py import_from_other_instance staging.somewhere.com API_KEY RCP85 10 100'


Getting Historic Summary Data
-----------------------------

Some indicators rely on comparison to aggregated values computed from historic observations. Because the aggregated data is based on historic readings and requires processing a large amount data to generate a relatively small result, these historic observations have been pre-computed and stored in a Django fixture.

Loading From Fixture
''''''''''''''''''''
To load pre-computed historic aggregated values from the fixture::

    ./scripts/console django './manage.py loaddata historic_averages historic_baselines'

Loading From Remote Instance
''''''''''''''''''''''''''''
If the fixture is missing data for the cities you need or needs to be regenerated and you happen to have a previously
deployed Climate Change API instance with the necessary data, you can use the `import_historic` management command to
pull the data into your environment.

Once you have the cities and models needed configured, run this command to pull the data down from the remote
instance. Note that if you already have historic aggregated data you will need to delete it using the administrative
tools first::

    ./scripts/console django './manage.py import_historic staging.somewhere.com API_KEY'


Loading From Historic Readings
''''''''''''''''''''''''''''''
If the data needs to be regenerated from scratch, you will need to use the section "Loading Data from NetCDF" above
to pull in historic data under the scenario "historical". Once the raw data has been loaded, use the management
command ``generate_historic`` to process the data locally and create the necessary summary data::

    ./scripts/console django './manage.py generate_historic'

Updating The Fixtures
'''''''''''''''''''''
If the tracked fixtures have become out of date and need to be updated, once generated or imported the fixtures can
be updated using the Django ``dumpdata`` command::

    ./scripts/console django './manage.py dumpdata climate_data.HistoricAverageClimateData --natural-foreign --natural-primary > climate_data/fixtures/historic_averages.json
        && ./manage.py dumpdata climate_data.ClimateDataBaseline --natural-foreign --natural-primary > climate_data/fixtures/historic_baselines.json'

Afterwards you will need to compress the historic averages::

    gzip climate_data/fixtures/historic_averages.json

Note that this will export all historic summary data you have for all cities and map cells. Conventionally this file
is based off of the ``geonames_cities_top200_us.geojson`` list of cities, so please make sure you have the correct
cities installed before updating the fixtures.


.. _Azaveas Scripts to Rule Them All: https://github.com/azavea/architecture/blob/master/doc/arch/adr-0000-scripts-to-rule-them-all.md
