## Table of Contents

* [Ingesting new cities](#ingesting-new-cities)
* [Ingesting new climate data](#ingesting-new-climate-data)
   * [Prepare ingest data](#prepare-ingest-data)
   * [Take DB Snapshot](#take-db-snapshot)
   * [Modify RDS Database Parameters and Instance Type](#modify-rds-database-parameters-and-instance-type)
   * [Create new RunJobs management command](#create-new-runjobs-management-command)
   * [Create new EC2 Launch Configuration](#create-new-ec2-launch-configuration)
   * [Create new EC2 Autoscaling Group](#create-new-ec2-autoscaling-group)
   * [Create new RunJobs ECS Service](#create-new-runjobs-ecs-service)
   * [Trigger climate ingest jobs](#trigger-climate-ingest-jobs)
   * [Stop ECS and EC2 import services](#stop-ecs-and-ec2-import-services)
   * [Run post-ingest management tasks](#run-post-ingest-management-tasks)
   * [Cleanup Resources](#cleanup-resources)

## Ingesting new cities
If you only want to ingest data for a small number of cities, please read the documentation on [the single city ingest process instead](single_city_ingest.md).

## Ingesting new climate data

**Before continuing, familiarize yourself with the *Loading Data from NetCDF* and *Loading From Historic Readings* sections of the project [README](../README.rst). This guide is intended to show how to run those commands in an ECS cluster.**

**WARNING:** Until [#695](https://github.com/azavea/climate-change-api/issues/695) is addressed further imports of climate data are impossible due to exhaustion of Foreign Key references in the database.

### Prepare Ingest Data

In order to ingest additional data into the Climate API database, you'll likely want to use the newer `--import-geojson-url` or `--import-shapefile-url` options. Rather than ingest data for all of the `City` objects defined in the database, these import options allow you to specify a publicly available GeoJSON or Shapefile that contains Point geometries to use as the points to ingest.

Existing GeoJSON import files live in the s3://azavea-climate-sandbox, and the newer files were generated with the LocationSource helpers in `climate_data.nex2db.location_sources`. It's recommended that you place any additional GeoJSON files intended to be used for climate data imports in that bucket and make them publicly accessible.

### Take DB Snapshot

Before proceeding further, you'll want to generate a database snapshot of the current database state. If all else goes wrong, the snapshot can be used to restore the database.

To generate a snapshot, sign into the AWS console and go to [RDS -> Databases -> "dbproduction"](https://console.aws.amazon.com/rds/home?region=us-east-1#database:id=dbproduction;is-cluster=false) -> Actions -> Take Snapshot. Type a descriptive name, such as `dbproduction-YYYY-MM-DD-pre-ingest` and then click "Take Snapshot".

You'll want to avoid continuing further until the snapshot is complete. You can check snapshot status on the [Snapshots Dashboard](https://console.aws.amazon.com/rds/home?region=us-east-1#db-snapshots:).

### Modify RDS Database Parameters and Instance Type

**NOTE:** This step causes a minute or two of downtime, generally 5-10 minutes after you trigger the parameter modification. Plan your downtime communications accordingly and continue below during your planned downtime window.

Go to [RDS -> Databases -> "dbproduction"](https://console.aws.amazon.com/rds/home?region=us-east-1#database:id=dbproduction;is-cluster=false) -> Modify.

Change DB instance class:
- `db.t2.medium` -> `db.m4.2xlarge` (8 vCPU, 32Gb RAM)

Change DB parameter group:
- `dbproduction` -> `data-imports`

(Optional) Change Allocated storage:
- `2000 GiB` -> `<desired amount>`
It's likely you don't need this, but if you do, type in the new storage amount (in GiB) you want provisioned. See the section immediately following for some additional notes about this.

Click "Continue" at the bottom of the page.

Under "Scheduling of modifications" click "Apply immediately". 

Ensure you're within your scheduled downtime window then click "Modify DB Instance" and accept the warning that you might incur downtime (you will).

The update will take 30-60 minutes. Ensure that all ECS services come back up automatically once the downtime is over. If they do not, navigate to the ECS console and restart them. You may continue with the instructions below while these changes are being applied, but **do not** continue to "Trigger climate ingest jobs" until the database returns to the "Available" state, which can be viewed [here](https://console.aws.amazon.com/rds/home?region=us-east-1#database:id=dbproduction;is-cluster=false)

Once the update completes, you may need to reboot the database once more to apply the parameter group. To check if this is the case, navigate to ["RDS" -> "Databases" -> "dbproduction"](https://console.aws.amazon.com/rds/home?region=us-east-1#database:id=dbproduction;is-cluster=false;tab=configuration). On the "Configuration" tab scroll down and verify that "Parameter group" states `data-imports (in-sync)` and is green. If it has another status or color, such as `data-imports (pending-reboot)`, select "Actions" -> "Reboot" from the top of the page. Then click "Reboot with failover" -> "Reboot". This may incur additional downtime of < 1 min but it is typically fast enough not to be noticed.

#### (Optional) Resize RDS Volume

If you need to increase the RDS volume size because you're planning on ingesting a large quantity of additional data, then the RDS volume size should be updated along with the DB instance type and parameter group when those modifications are made during the step above. It's simpler to trigger all the modifications at once and it doesn't add additional downtime. The DB will take longer to modify, dependent on how much more additional space you're provisioning.

### Create new RunJobs management command

Navigate to the [ECS console](https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters).

Navigate to "Task Definitions" -> "ProductionManagement". From there, click the checkbox next to the definition with the highest revision number. Then click "Create New Revision".

On the next screen set the following fields. Everything else can be left at the defaults:
- "Task Definition Name": "ProductionManagementRunJobs"
- "Requires Compatibilities": Check "EC2"
- "Task memory (MiB)": 8192
- "Task CPU (unit)": "1 vcpu"
- Under "Container Definitions", click the "management" definition. Change "Memory limits (Hard limit)" to 8192.
- Under "Constraint" click "Add constraint". "Type": "member of" and "Expression": `attribute:ecs.instance-type == m5.2xlarge`

Click the blue "Create" button. Continue for now, you'll use this new "ProductionManagementRunJobs" task definition later when you create a new ECS Service to run the task.

### Create new EC2 Launch Configuration

Navigate to the [Launch Configurations](https://console.aws.amazon.com/ec2/autoscaling/home?region=us-east-1#LaunchConfigurations:) section of the EC2 console. Click the checkbox next to the most recent launch configuration that has a name of the form `lcProductionRunJobsYYYYMMDD`.

Click "Actions" -> "Copy Launch Configuration".

On the "Copy Launch Configuration" screen click "Edit AMI". In another tab, open the [ECS-Optimized AMI docs](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html) and copy the AMI ID for the `us-east-1` region.

Back on the "Copy Launch Configuration" tab click "Community AMIs" and paste the AMI ID you copied into the search bar. Click "Select" for the AMI matching the ID you searched since you'll likely see more than one search result. If a dialog appears asking you to confirm your choice, click "Yes".

Ensure `m5.2xlarge` is selected in the next table then click "Next: Configure details".

Update Name to match the format `lcProductionRunJobsYYYYMMDD` substituting the current date for `YYYYMMDD`. Ensure "Request Spot Instances" is selected and that your maximum price is ~2x the current price for the instance type selected. The remaining options can be left as their defaults. Click "Next: Add Storage".

On the Add Storage page ensure that the instance has an additional EBS device attached at `/dev/xvdcz` with type "General Purpose (SSD)". It should be a 100Gb volume. The remaining fields can be left at defaults. Click "Skip to review".

On the review settings page ensure that the settings summary matches the instructions above then click "Create launch configuration".

### Create new EC2 Autoscaling Group

Navigate to the [Auto Scaling Groups](https://console.aws.amazon.com/ec2/autoscaling/home?region=us-east-1#AutoScalingGroups:view=details) section of the EC2 console then click "Create Auto Scaling group".

Choose "Launch Configuration" and "Use an existing launch configuration". Click the checkbox next to the name of the "lcProductionRunJobsYYYYMMDD" configuration that you just created and then click "Next Step".

Enter "asgProductionRunJobsYYYYMMDD" in the "Group name" field, substituting today's date for YYYYMMDD as before. Choose the "ccProduction" VPC from the Network dropdown. Then click the "subnet" input box and a dropdown list of subnets will appear. Select all of the subnets labelled "private". The remaining settings can be left at the defaults so click "Next: Configure scaling policies".

Ensure "Keep this group at its initial size" is selected and then click "Review".

On the review page double check that the settings described above are reflected and then click "Create Auto Scaling group".

### Create new RunJobs ECS Service

Almost there. The last thing we need to do is create the ECS Service so navigate to the [Clusters](https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters) tab of the ECS console. Click "ecsProductionCluster".

Click the "Services" tab if its not already selected then click "Create". Make the following selections:
- Launch type: ECS
- Task Definition: "ProductionManagementRunJobs"
- Revision: "latest" (this should match the revision number you created earlier in "Create new RunJobs management command")
- Cluster: ecsProductionCluster
- Service name: ProductionDataImportYYYYMMDD (replace YYYYMMDD with current date)
- Number of tasks: 1

The remaining settings can be left at their defaults. Click "Next step".

All of the defaults on this page can be left as-is. Click "Next step".

Ensure that "Do not adjust the service's desired count" is selected. Click "Next step".

Ensure your selections are correct on the review page then click "Create Service".

In a few moments if you made the correct selections in the preceding steps you should see a new run jobs task start automatically and the "Running tasks" count on the [services tab of the cluster dashboard](https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/ecsProductionCluster/services) should show 1. If this does not occur, click the service name then review the "Tasks" and "Events" tab to begin troubleshooting.

If the service starts successfully you should also be able to go to the [Climate Papertrail dashboard](https://papertrailapp.com/groups/4737532/events) for the production API stack and see messages like the following:
```
Dec 21 07:16:47 34.205.251.31 management: Starting job processing...
```

### Trigger climate ingest jobs

**STOP:** Ensure that the production database has finished applying changes before continuing. There should be sufficient storage volume and the database should have instance type `m4.2xlarge` and parameter group `data-imports`.

Assuming all is well, the easiest way is to SSH into a running Climate API gunicorn container instance and trigger the jobs from there. This documentation does not review that process as this is generally a well understood process at Azavea.

Once you're at a console that looks something like this:
```
root@dbe69bfaf6ff:/opt/django/climate_change_api#
```

You're ready to trigger jobs. Earlier on we only started one EC2 instance and one ECS task in the service. Before opening the floodgates, we'll do the same here by triggering only a single queue message so we can watch the logs for errors before triggering the entire import. To do so, trigger an import for a single dataset + variable + model + scenario like so:
```
./manage.py create_jobs --import-geojson-url "<your url here>" LOCA RCP85 CCSM4 2006
```

Hit enter and head back to Papertrail. If you see output like:
```
Dec 15 12:00:00 34.205.251.31 management:  Downloading file: s3://nasanex/LOCA/MIROC5/16th/historical/r1i1p1/tasmax/tasmax_day_MIROC5_historical_r1i1p1_20040101-20041231.LOCA_2016-04-02.16th.nc
```
and don't see any errors or exceptions being thrown, you're likely in good shape. It's time to kick off the remaining jobs. To do so go back to the [Auto Scaling Group console](https://console.aws.amazon.com/ec2/autoscaling/home?region=us-east-1#AutoScalingGroups:view=details) and select your "asgProductionRunJobsYYYYMMDD" group. In the "Details" tab click "Edit" on the far right, set "Desired Capacity" to 20 and then click "Save".

Next go to the [ECS services console](https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/ecsProductionCluster/services) click the service you just created and then "Update". Set "Number of tasks" to `60` and then proceed to click "Next step" until you get to "Update service" then click that to finalize the update to the service task count.

Wait a few minutes until the ECS services tab reports 60 services then go back to your SSH console on the Django web worker.

Trigger the jobs:
```
/manage.py create_jobs --import-geojson-url "<your url here>" <dataset> RCP85 all all
/manage.py create_jobs --import-geojson-url "<your url here>" <dataset> RCP45 all all
/manage.py create_jobs --import-geojson-url "<your url here>" <dataset> historical all all
```

The commands will take awhile to run and if you navigate to the [SQS console](https://console.aws.amazon.com/sqs/home?region=us-east-1#) you should see thousands of jobs in the "cc-api-production" queue with some number of them already in flight.

Ensure you're still seeing no errors in Papertrail. Continue to check on the queue count and RDS metrics every few hours until the queue is empty.

### Stop ECS and EC2 import services

Once the queue is empty and you are done ingesting data, shut down the services you created in reverse order. This means:
- Update the ProductionDataImportYYYYMMDD ECS Service to have zero running tasks
- Update the EC2 Auto Scaling Group you created earlier to have zero "desired" instances. This will shut down all currently running instances.

For now, we won't delete these services in case we need to run further ingest jobs due to an import error. We'll delete them later.

### Run post-ingest management tasks

There are a few tasks to run to generate derived data after an ingest is complete. Run the following in the SSH shell you opened earlier on the running production gunicorn worker. Additionally its recommended that you run these within a screen or tmux session to avoid the jobs from being killed if your SSH connection is terminated.

```
./manage.py generate_historic
./manage.py import_coastline
./manage.py dbshell
climate=> VACUUM (VERBOSE, ANALYZE) climate_data_climatedatacell;
climate=> VACUUM (VERBOSE, ANALYZE) climate_data_climatedatayear;
climate=> VACUUM (VERBOSE, ANALYZE) climate_data_historicaverageclimatedatayear;
```

Once these have all completed successfully you can proceed to Post-ingest cleanup.

### Cleanup Resources

The import is complete! To clean up resources perform the following tasks:

- [ ] Delete the ECS ProductionDataImport service 
- [ ] Ensure the EC2 ProductionRunJobs Auto Scaling group is set to zero desired capacity
- [ ] Delete all but the most recent ProductionRunJobs Auto Scaling group and Launch Configuration definitions. We keep the most recent one of each around so we can use it as a template for the next import round.
- [ ] Close your SSH/tmux/screen session on the production gunicorn worker, if you created one
- [ ] Revert the changes to the database, planning accordingly for downtime and following the steps above in the section "Modify RDS Database". The original settings should be instance type `db.m2medium` and parameter group `dbproduction`. Note that as before, you might need to reboot the database after applying changes.
