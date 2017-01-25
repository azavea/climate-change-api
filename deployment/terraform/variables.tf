# Variables stored in S3 for each environment
# This file defines which variables must be
# defined in order to run terraform

# Must be one of release, staging, production
variable "stack_type" { }

variable "r53_hosted_zone_id" { }

# Scaling

variable "desired_instances" { }
variable "max_instances" { }
variable "deploy_min_healthy_instances_pct" { }
variable "deploy_max_instances_pct" { }

# Variables that must be defined for VPC
variable "vpc_cidr_block" { }
variable "vpc_bastion_instance_type" { }
variable "vpc_nat_instance_type" { }
variable "key_name" { }

variable "ecs_iam_role" { }
variable "ecs_iam_profile" { }
variable "git_commit" { }
variable "ecs_instance_ami_id" { }
variable "ecs_instance_type" { }
variable "elb_ssl_certificate_arn" { }

variable "rds_database_name" { }
variable "rds_instance_type" { }
variable "rds_password" { }
variable "rds_username" { }
variable "rds_storage_size_gb" { }
variable "rds_cpu_credit_alarm_threshold" { }

variable "django_secret_key" { }
variable "django_allowed_hosts" { }
variable "s3storage_bucket" { }
variable "sqs_queue_name" { }
variable "cloudwatch_logs_group" { }

# Static docs site
variable "climate_docs_site_bucket" { }
variable "climate_docs_logs_bucket" { }
variable "r53_public_dns_docs" { }
variable "acm_certificate_arn_docs" { }
