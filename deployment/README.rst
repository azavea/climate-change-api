Deployment
==========

The Climate Change API app is a django app container deployed to Amazon ECS
via Amazon ECR. Terraform is used to configure the infrastructure. Makefiles
have been written to assist in building images and orchestrating the
infrastructure around it.

The ``STACK_TYPE`` environment variable
---------------------------------------

The ``STACK_TYPE`` environment variable lets you select which stack you are
working with as you run ``make`` commands. By default, the ``staging``
environment will be selected.

You can specify the ``production`` stack type by setting this environment
variable:

``export STACK_TYPE=production``

``make`` targets
----------------

Inside the ``climate-change-api`` directory, these make targets are available:

* ``push`` - build a new docker image and upload it to ECR
* ``deploy`` - build a new docker image, upload it, and update the
  infrastructure to use it
* ``pulltfvars`` - pull the terraform tfvars file from s3
* ``pushtfvars`` - push the terraform tfvars file to s3

Inside the ``deployment/terraform`` directory, these make targets are
available:

* ``apply`` - run ``terraform apply`` while handling the state upload and
  download
* ``destroy`` - run ``terraform destroy``
* ``pullvars`` - pull the terraform tfvars file from s3
* ``pushvars`` - push the terraform tfvars file to s3

*Remember to push tfvars before you apply any changes in terraform (including
`make deploy`), as tfvars will be redownloaded.*

