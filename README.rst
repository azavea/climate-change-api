Climate Change API
==================

Development Environment
-----------------------

In order to develop on this project, you'll need to setup an AWS ``climate`` profile. First,
sign into your user in the azavea-climate AWS account and create a set of access keys.

Then, run ``aws configure --profile climate`` and follow the prompts.

With AWS ready, run the following to configure the VM and load the most recent database backup:

.. code-block:: bash

    ./scripts/setup

Next, ssh into the VM with ``vagrant ssh``. Then run::

    ./scripts/console django './manage.py createsuperuser'

and follow the prompts to create an initial user to login with. You will also need to create a UserProfile so that you can login to the app.

In the VM:

.. code-block:: bash

    ./scripts/console django './manage.py shell_plus'

Within the shell:

.. code-block:: bash

    In  [1]: my_user = ClimateUser.objects.get(email=<Your User's Email>)
    In  [2]: UserProfile.objects.create(user=my_user)
    Out [2]: <UserProfile: (Your User's Email)>


Once you have a new user, run ``./scripts/server`` inside the VM to begin serving the application on port 8080.

This project conforms to the specification provided by `Azaveas Scripts to Rule Them All`_.


Running Tests
-------------

Run Django linter with::

    ./scripts/console django 'flake8'

Run Django tests with::

    ./scripts/console django './manage.py test'


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


Request Debugging
-----------------
The project has the `Django Debug Toolbar`_ installed to help provide insight into the steps behind producing an HTML response. It is available on a development environment when accessed directly from the host computer and can be seen in the User Profile pages as well as in API requests when using the HTML-based BrowsableAPI. To use the BrowsableAPI log into the User Profile page in a browser and then in the browser navigate to the URL of the desired API request.


Bypassing Cache
---------------

For debugging queries and cache configuration, caching may be disabled per-query by sending::

    noCache=True

as an additional parameter. The load testing configuration always sends this parameter.


Documentation
-------------

Documentation for the API can be built with::

    ./scripts/docs

Docs are served in development via nginx and can be viewed at http://localhost:8084


Django Management commands
--------------------------

To run Django management commands, use the console helper script::

    ./scripts/console django './manage.py migrate'

Django runserver can be found on port 8082. Have the project running, in another terminal window inside the VM execute::

    docker exec -it climatechangeapi_django_1 /bin/bash

    ./manage.py runserver 0.0.0.0:8082

and view at http://localhost:8082


Manually Getting Data
------------

If the need arises, there are two methods available for manually importing climate data: Import from the raw NetCDF, or import from another ClimateChangeAPI instance. When loading climate data, you will need to bump your API user's throttling rate (``ClimateUser.burst_rate`` and ``ClimateUser.sustained_rate``) if loading from another instance. Even if not, you'll probably want to bump it for ease of development.


Access the Remote Instance
''''''''''''''''''''''''''

To make changes to a remote instance of CC API (i.e. staging), you'll need to SSH in. First download ``pem.txt`` from the Climate Change SSH Key folder in LastPass. From there, you'll want to add it to your SSH key store and make sure it is accessible::

    cp <pem_file> > ~/.ssh/
    chmod 600 ~/.ssh/<pem_file>
    ssh-add ~/.ssh/<pem_file>

Next, you'll need the IPs of the remote instances. Log into the Climate Change AWS account and find the IP addresses of the active EC2 instances. SSH into them, making sure to port your permissions with ``-A``. Lastly, find and ssh into the django docker container::

    ssh -A ec2-user@<IP_of_Bastion>
    ssh <other_container_private_ip>
    docker ps
    docker exec -it <django_container_id> /bin/bash

From here, ``./manage.py`` commands are available to you.


Loading Data from NetCDF
''''''''''''''''''''''''

Running ``./scripts/setupdb`` will populate your database with scenario, climate model, 200 cities, region, and boundary data -- if sufficient, skip to the section "Loading Data From Staging".

Run migrations::

    ./scripts/console django './manage.py migrate'


Load scenario and climate model data::

    ./scripts/console django './manage.py loaddata scenarios'
    ./scripts/console django './manage.py loaddata climate-models'
    ./scripts/console django './manage.py loaddata climate-datasets'


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

To clear database before importing data::

    ./scripts/console django './manage.py shell_plus'
    ClimateDataCell.objects.all().delete()
    ClimateDataSource.objects.all().delete()

Import data (10 models, 100 cities)::

    ./scripts/console django './manage.py import_from_other_instance staging.somewhere.com API_KEY RCP85 10 100'

Any import failures will be logged to ``django/climate_change_api/logs/import_error.log`` and will be
re-attempted if the import job is repeated.


Getting Historic Summary Data
-----------------------------

Some indicators rely on comparison to aggregated values computed from historic observations. Because the aggregated data is based on historic readings and requires processing a large amount data to generate a relatively small result, these historic observations have been pre-computed and stored in a Django fixture.

Loading From Fixture
''''''''''''''''''''
To load pre-computed historic aggregated values from the fixture::

    ./scripts/console django './manage.py loaddata historic_averages historic_baselines'


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


Updating The Development Database Dump
--------------------------------------

When the database schema changes or new models/data are added to staging, it may be necessary to update the database dump used to setup the develoment environment. To create the database dump, do the following:

Downoad the `azavea-climate.pem` SSH key from the fileshare and add it to your virtual machine's ssh-agent.

Setup an SSH tunnel from your virtual machine, through the bastion host, to the database instance::

    ssh -A -l ec2-user -L <local port>:database.service.climate.internal:5432 -Nf bastion.staging.climate.azavea.com


After the SSH tunnel is setup, run ``pg_dump`` to take a backup of Staging and save it in the ``database_backup`` folder::

    $ pg_dump -U climate -d climate -p <local port> -h localhost  -v -O -Fc -f database_backup/cc_dev_db.dump

Where ``-O`` ignores table permissions, ``-p`` is the port forwarded to the bastion host, ``-h`` is the database host, and ``-Fc`` ensures that the dump is in the ``pg_restore`` custom format.

Once that backup has completed and you have the dump locally, Console into the `postgres` container and use ``pg_restore`` to load the database.::

    $ ./scripts/console postgres /bin/bash
    # pg_restore -j 4 -v -O -d climate -U climate /opt/database_backup/cc_dev_db.dump

After the backup is loaded, decrease the size of the database by removing ClimateData for all cities but Phoenix, AZ, Philadelphia, PA, and Houston, TX. Additionally, ClimateUser, Session objects, Tokens, UserProfiles and Projects should be removed. From inside the VM, do:::

    $ ./scripts/console django './manage.py shell_plus'

And from the django console, do::

    # Delete all climate users
    In [1]: ClimateUser.objects.all().delete()
    Out[1]:
    (38,
     {'admin.LogEntry': 0,
      'authtoken.Token': 12,
      'user_management.ClimateUser': 12,
      'user_management.ClimateUser_groups': 0,
      'user_management.ClimateUser_user_permissions': 0,
      'user_management.UserProfile': 8,
      'user_projects.Project': 6})

    # Delete all User sessions
    In [2]: Session.objects.all().delete()
    Out[2]: (36, {'sessions.Session': 36})

    # Delete all cities whose names are not Philadelphia, Houston or Phoenix
    In [3]: City.objects.exclude(name__in=['Philadelphia', 'Houston', 'Phoenix']).delete()
    Out[3]: (14, {'climate_data.City': 7, 'climate_data.CityBoundary': 7})

    # Delete all Climate data that isn't associated with one of the cities above
    In [4]: ClimateDataCell.objects.exclude(id__in=City.objects.all().values_list("map_cell_id", flat=True)).delete()
    Out[4]:
    (9413650,
     {'climate_data.ClimateData': 9411795,
      'climate_data.ClimateDataBaseline': 20,
      'climate_data.ClimateDataCell': 5,
      'climate_data.HistoricAverageClimateData': 1830})

Once the database has been pruned, run ``pg_dump`` from inside of the postgres container to make a database dump of the current state. Console into the ``postgres`` container::

    $ docker-compose exec postgres db_dump -T pg_dump -U climate -d climate -v -O -Fc -f /opt/database_backup/cc_dev_db.dump

Finally, move the ``latest`` backup on S3 into the ``archive`` folder, then copy the newest backup to S3.::

    $ aws s3 mv s3://development-climate-backups-us-east-1/db/latest/cc_dev_db.dump s3://development-climate-backups-us-east-1/db/archive/cc_dev_db_<DATE>.dump

    $ aws s3 cp database_backup/cc_dev_db.dump s3://development-climate-backups-us-east-1/db/latest/

Where DATE is in the format mmddyyyy (i.e. cc_dev_db_05082017.dump)

.. _Azaveas Scripts to Rule Them All: https://github.com/azavea/architecture/blob/master/doc/arch/adr-0000-scripts-to-rule-them-all.md
.. _Django Debug Toolbar: https://django-debug-toolbar.readthedocs.io
