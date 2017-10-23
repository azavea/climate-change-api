Use AWS Batch for single city ingest
====================================

Context
-------

We would like to implement a feature that allows a user to request data for their city to be imported into the database if it is not already available.

We identified two options:

AWS Batch is available to us as a solution that handles autoscaling, a queue, and execution of Docker based workloads.

As an alternative to AWS Batch, we could roll our own autoscaling and use the queue polling loop we already have. This would give us finer control of the autoscaling. We would write a function to watch the queue. If there are jobs waiting, it would scale up. If there are no jobs waiting and no jobs in progress, it would scale down to zero instances. This solution would involve an ECS cluster.

Autoscaling could possibly be automated with CloudWatch alarms and the ``ApproximateNumberOfMessagesVisible`` and ``ApproximateNumberOfMessagesNotVisible`` SQS metrics. It is uncertain how and if these metrics could be configured in a way where alarms to scale up and scale down don't conflict.

Decision
--------

We have chosen to use AWS Batch. We will also create database records to keep track of job state in a place closer to the application.

Consequences
------------

We will need to refactor our data import script around importing one city and handling job parameters from AWS Batch.

We will need to upgrade to Terraform 0.10.x to be able to manage AWS Batch resources in AWS. There is an `upgrade guide`_ for 0.10.x. Upgrading Terraform is low risk and scoped to the project's docker container. We will build a Terraform module that can be reused in another project.

We may run into issues with AWS Batch's autoscaling putting excess load on the database. If this happens, we may have to find a workaround or reconsider this architecture decision entirely. Capping vCPUs is a way to throttle the number of batch processes.

.. _upgrade guide: https://www.terraform.io/upgrade-guides/0-10.html
