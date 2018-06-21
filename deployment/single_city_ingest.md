# Single city ingest

Table of Contents
=================

   * [Single city ingest](#single-city-ingest)
      * [Create Cities](#create-cities)
      * [Create processing jobs](#create-processing-jobs)
      * [Resize the database](#resize-the-database)
      * [Run Jobs](#run-jobs)
         * [Add Spot Instances to the ECS cluster](#add-spot-instances-to-the-ecs-cluster)
         * [Prepare a new task revision and update the service](#prepare-a-new-task-revision-and-update-the-service)
         * [Run the jobs](#run-the-jobs)
         * [Turning off the import cluster](#turning-off-the-import-cluster)
      * [Resize the database again](#resize-the-database-again)
      * [Generate Historical Data](#generate-historical-data)


## Create Cities

Open a shell in a production `cc-api` Docker container, and add new `City` objects for each city you want to ingest data for. After creating the cities, run the `manage.py` commands `import_boundaries`, `import_coastlines`, and `import_regions`.

```shell
$ ssh climate-production-bastion
[ec2-user@ip-10-0-0-4 ~]$ ssh <ECS_CLUSTER_PRIVATE_IP>
[ec2-user@ip-10-0-3-137 ~]$ docker ps | grep cc-api
5e50a16cd125        784347171332.dkr.ecr.us-east-1.amazonaws.com/cc-api:e6e9fc7         "/usr/local/bin/guni…"   18 hours ago        Up 18 hours         8080/tcp                         ecs-ProductionHTTPSAPI-11-django-8ea4ab94e49987c49701
[ec2-user@ip-10-0-3-137 ~]$ docker exec -it 5e50a16cd125 /bin/bash
root@5e50a16cd125:/opt/django/climate_change_api# python manage.py shell
Python 3.5.5 (default, Feb 15 2018, 13:21:37) 
Type 'copyright', 'credits' or 'license' for more information
IPython 6.2.1 -- An enhanced Interactive Python. Type '?' for help.

In [1]: from climate_data.models import City

In [2]: from django.contrib.gis.geos import Point

In [3]: City.objects.create(geom=Point(lon, lat, srid=4326, name=city_name, admin=state_abbrev, population=2010_census_pop)

In [4]: exit
root@5e50a16cd125:/opt/django/climate_change_api# python manage.py import_boundaries
...
root@5e50a16cd125:/opt/django/climate_change_api# python manage.py import_coastlines
...
root@5e50a16cd125:/opt/django/climate_change_api# python manage.py import_regions
...
```


## Create processing jobs

From a shell in a production `cc-api` Docker container, run the `create_jobs` management command for every dataset and scenario you want to ingest.

```shell
$ ssh climate-production-bastion
[ec2-user@ip-10-0-0-4 ~]$ ssh <ECS_CLUSTER_PRIVATE_IP>
[ec2-user@ip-10-0-3-137 ~]$ docker ps | grep cc-api
5e50a16cd125        784347171332.dkr.ecr.us-east-1.amazonaws.com/cc-api:e6e9fc7         "/usr/local/bin/guni…"   18 hours ago        Up 18 hours         8080/tcp                         ecs-ProductionHTTPSAPI-11-django-8ea4ab94e49987c49701
[ec2-user@ip-10-0-3-137 ~]$ docker exec -it 5e50a16cd125 /bin/bash
root@5e50a16cd125:/opt/django/climate_change_api# python manage.py create_jobs NEX-GDDP rcp45 all all
...
root@5e50a16cd125:/opt/django/climate_change_api# python manage.py create_jobs NEX-GDDP rcp85 all all
...
root@5e50a16cd125:/opt/django/climate_change_api# python manage.py create_jobs NEX-GDDP historical all all
...
root@5e50a16cd125:/opt/django/climate_change_api# python manage.py create_jobs LOCA rcp45 all all
...
root@5e50a16cd125:/opt/django/climate_change_api# python manage.py create_jobs LOCA rcp85 all all
...
root@5e50a16cd125:/opt/django/climate_change_api# python manage.py create_jobs LOCA historical all all
...
```


## Resize the database

Before starting the import process, resize the `dbproduction` RDS instance in the AWS Console to `db.m4.xlarge` and change the DB parameter group to `db-imports`. Choose "Apply Immediately" when saving your changes. Remember to check the Papertrail logs to verify there is little/no usage of the application, as changing the database type will cause *a few minutes of downtime*.

![screenshot-2018-6-21 rds aws console](https://user-images.githubusercontent.com/4432106/41745735-fa7ea0ac-7575-11e8-9cff-23a62b071c88.png)
![screenshot-2018-6-21 rds aws console 1](https://user-images.githubusercontent.com/4432106/41745734-fa6eb502-7575-11e8-98c2-06eb9e714587.png)


## Run Jobs

Additional container instances will likely need to be added into the ECS cluster in order to handle the amount of processing capacity necessary for processing jobs. A cluster with 20 `m4.2xlarge` container instances should be sufficient. The instructions to launch a spot fleet into the ECS Cluster are below.

![screenshot-2018-6-21 amazon ecs](https://user-images.githubusercontent.com/4432106/41745663-b21e5bd6-7575-11e8-91e4-554fc86e0bfa.png)


### Add Spot Instances to the ECS cluster

- Through the AWS Console, update the `asgProductionDataImport` Autoscaling Group with a desired capacity of 20.
![screenshot-2018-6-21 ec2 management console](https://user-images.githubusercontent.com/4432106/41745804-3c7c2d3a-7576-11e8-93cc-47b044cd6d00.png)


### Prepare a new task revision and update the service

_This step can be skipped if there has not been a redeploy of the Climate Change API since the last data ingest._

- Login to the task definition page in the [AWS ECS console](https://console.aws.amazon.com/ecs/home?region=us-east-1#/taskDefinitions).

- Verify that the latest version of the `ProductionManagementRunJobs` task definition has a hard memory limit of `8192`.
  - If it does not, click Create New Revision on the Task Definitions page.

  - In the Container Definitions section, click the `management` container name. In the ensuing Edit Container screen, set the hard memory limit to `8192` and remove the soft limit. This ensures that containers for batch processing jobs will not be killed if they use too much memory.
    ![screenshot from 2018-06-21 15-29-33](https://user-images.githubusercontent.com/4432106/41745645-a5b2465a-7575-11e8-91e8-1cbb318bf7da.png)

### Run the jobs

From the `ProductionManagementRunJobs` task definition page, click Actions and choose "Update Service".
- Set the number of tasks to 60
- Check the PaperTrail logs immediately to verify that there were no errors, and check back periodically to see if the jobs have been completed


### Turning off the import cluster
Once you've verified in Papertrail that the ingest is complete, you should turn off the ECS cluster used for the data import.

- From the `ProductionManagementRunJobs` task definition, update the service as above, and set the desired number of workers to 0
- Through the AWS Console, update the `asgProductionDataImport` Autoscaling Group with a desired capacity of 0.


## Resize the database again

After finishing the ingest, revert the `dbproduction` RDS instance in the AWS Console to `db.t2.medium` and change the DB parameter group to `dbproduction`. Remember to check the Papertrail logs to verify there is little/no usage of the application, as changing the database type will cause *a few minutes of downtime*.

## Generate Historical Data
From a shell in a production `cc-api` Docker container, run the `create_jobs` management command for every dataset and scenario you want to ingest.

```shell
$ ssh climate-production-bastion
[ec2-user@ip-10-0-0-4 ~]$ ssh <ECS_CLUSTER_PRIVATE_IP>
[ec2-user@ip-10-0-3-137 ~]$ docker ps | grep cc-api
5e50a16cd125        784347171332.dkr.ecr.us-east-1.amazonaws.com/cc-api:e6e9fc7         "/usr/local/bin/guni…"   18 hours ago        Up 18 hours         8080/tcp                         ecs-ProductionHTTPSAPI-11-django-8ea4ab94e49987c49701
[ec2-user@ip-10-0-3-137 ~]$ docker exec -it 5e50a16cd125 /bin/bash
root@5e50a16cd125:/opt/django/climate_change_api# python manage.py generate_historic
...
```
