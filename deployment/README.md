# Amazon Web Services Deployment

Amazon Web Services deployment is driven by [Terraform](https://terraform.io/) and the [AWS Command Line Interface (CLI)](http://aws.amazon.com/cli/).

## Table of Contents

* [AWS Credentials](#aws-credentials)
* [Terraform](#terraform)
* [Database Population](#staging-database-population)
	* [Prepare a New task revision](#prepare-a-new-task-revision)
	* [Run Migrations](#run-migrations)
	* [Load Scenarios](#load-scenarios)
	* [Load Climate Models](#load-climate-models)
	* [Load Cities](#load-cities)
	* [Create a Processing Job](#create-a-processing-job)
	* [`run_jobs`](#run-jobs)
		* [Add Spot Instances to the ECS cluster](#adding-spot-instances-to-the-ecs-cluster)
		* [Resize the Database](#resize-database)
		* [Create a Processing Service](#creating-a-processing-service)
	* [Generating Historical Data](#generating-historical-data)
		* [Import Raw Data](#import-raw-data)
		* [General Historical Data](#generate-historical-data)

## AWS Credentials

Using the AWS CLI, create an AWS profile named `climate`:

```bash
$ vagrant ssh
vagrant@vagrant-ubuntu-trusty-64:~$ aws --profile climate configure
AWS Access Key ID [****************F2DQ]:
AWS Secret Access Key [****************TLJ/]:
Default region name [us-east-1]: us-east-1
Default output format [None]:
```

You will be prompted to enter your AWS credentials, along with a default region. These credentials will be used to authenticate calls to the AWS API when using Terraform and the AWS CLI.

## Terraform

Next, use the `infra` wrapper script to lookup the remote state of the infrastructure and assemble a plan for work to be done:

```bash
vagrant@vagrant-ubuntu-trusty-64:~$ export CC_SETTINGS_BUCKET="staging-us-east-1-climate-config"
vagrant@vagrant-ubuntu-trusty-64:~$ export AWS_PROFILE="climate"
vagrant@vagrant-ubuntu-trusty-64:~$ ./scripts/infra plan
```

Once the plan has been assembled, and you agree with the changes, apply it:

```bash
vagrant@vagrant-ubuntu-trusty-64:~$ ./scripts/infra apply
```
This will attempt to apply the plan assembled in the previous step using Amazon's APIs. In order to change specific attributes of the infrastructure, inspect the contents of the environment's configuration file in Amazon S3.

## Staging Database Population

**Before continuing, familiarize yourself with the *Loading Data from NetCDF* and *Loading From Historic Readings* sections of the project [README](../README.rst). This guide is intended to show how to run those commands in an ECS cluster.**

### Prepare a new task revision

- Login to the task definition page in the [AWS ECS console](https://console.aws.amazon.com/ecs/home?region=us-east-1#/taskDefinitions).  

- Create a new revision of the StagingManagement task definition.
	- Click Create New Revision on the Task Definitions page.
	![Create New Revision](https://cloud.githubusercontent.com/assets/2507188/23276740/7d88fb6a-f9d9-11e6-8b2b-db83a73b3aee.png)

    - In the Container Definitions section, click the `management` container name. In the ensuing Edit Container screen, remove the hard memory limit and set the soft limit to 2048 MB. This ensures that containers for batch processing jobs will not be killed if they use too much memory.
    ![Container Overrides](https://cloud.githubusercontent.com/assets/2507188/23276741/7d8aee02-f9d9-11e6-94af-7017d6406a0c.png)

 	- Take note of the revision number (i.e. StagingManagement:13)

- The StagingManagement task definition sets the docker `ENTRYPOINT` for the `management` container as `./manage.py`, so in subsequent steps all we'll need to do is supply the container with a Command Override (analogous to a docker `CMD`).

### Run Migrations

- Go to the console page for the [Staging ECS cluster](https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/ecsStagingCluster/services).

- In the Tasks tab, create a new task based on the StagingManagement task definition revision created in the previous section.

- Add `migrate` as a Command Override for the `management` container.
![Command Overrides](https://cloud.githubusercontent.com/assets/2507188/23276743/7d8bcf34-f9d9-11e6-9958-139097492f82.png)

- Click run task.

### Load Scenarios

- Repeat the steps in [Run Migrations](#run-migrations), with the Command Override `loaddata,scenarios`.

- Note that multi-word commands should be entered as a comma separated string, as shown. See the [ECS Command Override Docs](http://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_run_task.html) for more information on this topic.

### Load Climate models

- Repeat the steps in [Run Migrations](#run-migrations) with the Command Override `loaddata,climate-models`.

### Load Cities

- Repeat the steps in [Run Migrations](#run-migrations) with the Command Override `import_cities,azavea-climate-sandbox,geonames_cities_top200_us.geojson`.


### Create a processing job
- Repeat the steps in [Run Migrations](#run-migrations) with the arguments to `create_jobs RCP85`. To create jobs for all models in all years, the Command Override would be `create_jobs,RCP85,all,all`.

### Run Jobs

Additional container instances will likely need to be added into the ECS cluster in order to handle the amount of processing capacity necessary for processing jobs. A cluster with 20 `m4.2xlarge` container instances should be sufficient. The instructions to launch a spot fleet into the ECS Cluster are below.

#### Launching a spot fleet into the ECS cluster
- Through the AWS Console, Create a copy of the latest terraform-managed launch configuration for a container instance. 
- Modify this launch config to have an instance size of `m4.2xlarge`, and 100GB of disk. Changing a pre-existing launch config ensures that instances will have the proper ECS cluster name at launch time.
![Instance Size Modifications](https://cloud.githubusercontent.com/assets/2507188/23183815/574f290e-f84b-11e6-90a0-641c7636c194.png)

- Edit the `Configure Details` section to request spot pricing. The current market price for your instance type will be shown, so bid at your own discretion.
![Spot Pricing Modifications](https://cloud.githubusercontent.com/assets/2507188/23183951/ca63e2fe-f84b-11e6-849d-2fe5d5058b5e.png)

- Once your launch config is created, launch an Autoscaling Group with a desired capacity of 20, tied to that launch configuration.
![Launching an ASG](https://cloud.githubusercontent.com/assets/2507188/23184132/9574abd6-f84c-11e6-9f51-536b98f8ff4a.png)


#### Resize database

- Before starting the import process, resize the database to `db.m4.xlarge` with 240 GB of disk.

#### Creating a Processing Service
Start 200 `run_jobs` tasks. The easiest way to do this is to create a service.

- In the [ECS Services page](https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/ecsStagingCluster/services), click Create.

- Using the StagingManagement task definition created above, add `run_jobs` to the Container Overrides and set the number of tasks to 200. It's also a good idea to set `DJANGO_LOG` to `DEBUG` for better output. 

- Scope `run_jobs` tasks to run on the spot instances only.
	- Under Task Placement, select a custom template.
	- Set Type to Spread, and Field to attribute:ecs.instance-type.
	- Under Constraint, set Type to MemberOf, and Expression to `attribute:ecs.instance-type == m4.2xlarge`, or whatever spot instance types have been launched into the cluster.
![Creating a Service](https://cloud.githubusercontent.com/assets/2507188/23276742/7d8b56da-f9d9-11e6-93ab-293797e185d0.png)
- Click Create Service, and tasks should launch shortly.


### Generating Historical Data

#### Import Raw Data
- Repeat the steps in [Run Migrations](#run-migrations) with the arguments to `create_jobs historical`. To import historical data for all models in all years, the Command Override would be `create_jobs,historical,all,all`.

- Follow the steps outlined in [Run Jobs](#run-jobs) to perform the actual data import.

#### Generate Historical Data
- Repeat the steps in [Run Migrations](#run-migrations) with the Command Override `generate_historic`.

## Releases

## Create Release Branch

First, create a release branch for the version about to be released:

```
$ git flow release start X.Y.Z
```

# Update Change Log #

Thus far, the `CHANGELOG` has been generated by [`github-changelog-generator`](https://github.com/skywinder/github-changelog-generator). Follow the steps below to install and execute `github-changelog-generator` to update the `CHANGELOG`:

```
$ docker run -ti --rm -v ${PWD}:/changelog -w /changelog ruby:2.3 /bin/bash
root@545d989d9130:/changelog# gem install github_changelog_generator
root@545d989d9130:/changelog# github_changelog_generator --token ${GITHUB_TOKEN} \
                                                         --future-release X.Y.Z \
                                                         --no-issues \
                                                         --no-issues-wo-labels \
                                                         --no-author
```

## Publish Release Branch

Next, publish the release branch, but do so knowing that Jenkins will automatically attempt to deploy it to staging:

```
$ git flow release publish X.Y.Z
```

Once published, monitor the **Branches** tab of the Jenkins UI for a `release/*` job to begin:

- http://urbanappsci.internal.azavea.com/job/azavea/job/climate-change-api/

## Production Release

Once sufficient testing has occurred on the release, identify the first seven characters of the release branch SHA, and `export` it via `GIT_COMMIT`:

```bash
$ git rev-parse --short HEAD
FFFFFFF
$ export GIT_COMMIT="FFFFFFF"
```

Next, export all of the other necessary environment variables and execute `cibuild`, `cipublish`, and `infra`:

```bash
$ export CC_DOCS_FILES_BUCKET="production-us-east-1-climate-docs"
$ export CC_SETTINGS_BUCKET="production-us-east-1-climate-config"
$ export CC_S3STORAGE_BUCKET="climate-change-api-production"
$ export CC_AWS_ECR_ENDPOINT="xxxxx.dkr.ecr.us-east-1.amazonaws.com"
$ ./scripts/cibuild
$ ./scripts/cipublish
$ docker-compose -f docker-compose.ci.yml run --rm terraform ./scripts/infra plan
$ docker-compose -f docker-compose.ci.yml run --rm terraform ./scripts/infra apply
```

## Repository Cleanup

Finally, execute the following commands to merge the contents of the release branch back into `develop` and `master`:

```
$ git flow release finish X.Y.Z
$ git push origin develop
$ git checkout master && git push origin master
$ git push --tags
```
