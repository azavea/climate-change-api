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


Getting Data
------------

Once you have your environment set up, you need data. There are two methods available for importing climate data: Import from the raw NetCDF, or import from another ClimateChangeAPI instance.


Loading Data from NetCDF
''''''''''''''''''''''''

Run migrations::

    ./scripts/console django './manage.py migrate'


Load scenario and climate model data::

    ./scripts/console django loaddata scenarios
    ./scripts/console django loaddata climate-models


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
    ClimateModel.objects.all().delete()
    ClimateDataCell.objects.all().delete()
    ClimateDataSource.objects.all().delete()
    Scenario(name='RCP85').save()

Import data (10 models, 100 cities)::

    ./scripts/console django './manage.py import_from_other_instance staging.somewhere.com API_KEY RCP85 10 100'


Loading Computed Historic Aggregated Data
'''''''''''''''''''''''''''''''''''''''''

Some indicators rely on comparison to aggregated values computed from historic observations. Because the aggregated data is based on historic readings and requires processing a large amount data to generate a relatively small result, these historic observations have been pre-computed and stored in a Django fixture.

To load pre-computed historic aggregated values from the fixture::

    ./scripts/console django loaddata historic_averages

To rebuild the fixture of computed historic aggregated values, first load cities into the database.
Then run the management command to query for historic data from a remote server, aggregate the values,
and load them into the HistoricAverageClimateData model. Note that this will first delete any
existing HistoricAverageClimateData objects from the local database::

    ./scripts/console django './manage.py import_historic staging.somewhere.com API_KEY'

Then to dump the newly loaded HistoricAverageClimateData objects to a fixture file::

    ./scripts/console django './manage.py dumpdata climate_data.HistoricAverageClimateData > climate_data/fixtures/historic_averages.json'

And compress the result::

    gzip climate_data/fixtures/historic_averages.json
