Use AWS Batch for single city ingest
====================================

Context
-------

We would like to implement a feature that allows a user to request data for their city be imported into the database if it is not already available.

We identified two options:

AWS batch is available to us as a solution that handles autoscaling, a queue, and execution of Docker based workloads.

As an alternative to AWS batch, we could roll our own autoscaling and use the queue polling loop we already have. This would give us finer control of the autoscaling. We would write a function to watch the queue. If there are jobs waiting, it would scale up. If there are no jobs waiting and no jobs in progress, it would scale down to zero instances. This solution would involve an ECS cluster.

Decision
--------

We have chosen to use AWS batch. We will also create database records to keep track of job state in a place closer to the application.

Consequences
------------

We will need to refactor our data import script around importing one city and handling job parameters from AWS Batch.

We will need to upgrade to Terraform 0.10.x to be able to manage Batch resources in AWS. Upgrading Terraform is low risk and scoped to the project's docker container. We will build a Terraform module that can be reused in another project.

We may run into issues with Batch's autoscaling putting excess load on the database. If this happens, we may have to find a workaround or reconsider this architecture decision entirely.
