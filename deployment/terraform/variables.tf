# Variables stored in S3 for each environment
# This file defines which variables must be
# defined in order to run terraform

# Must be one of release, staging, production
variable "project" {
  default = "Climate Change API"
}

variable "aws_account_id" {
  default = "784347171332"
}

variable "aws_region" {}
variable "environment" {}

variable "bastion_ami" {
  default = "ami-f5f41398"
}

variable "r53_private_hosted_zone" {}
variable "r53_public_hosted_zone" {}

# Scaling
variable "container_instance_asg_desired_capacity" {}

variable "container_instance_asg_min_size" {}
variable "container_instance_asg_max_size" {}
variable "container_instance_type" {}
variable "aws_key_name" {}
variable "ecs_instance_ami_id" {}

# ECS
## HTTP API server
variable "cc_api_http_ecs_desired_count" {}

variable "cc_api_http_ecs_deployment_min_percent" {}
variable "cc_api_http_ecs_deployment_max_percent" {}

## HTTPS API server
variable "cc_api_https_ecs_deployment_max_percent" {}

variable "cc_api_https_ecs_desired_count" {}
variable "cc_api_https_ecs_deployment_min_percent" {}

# IAM
variable "aws_ecs_for_ec2_service_role_policy_arn" {
  default = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

variable "aws_ecs_service_role_policy_arn" {
  default = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceRole"
}

variable "aws_s3_policy_arn" {
  default = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

variable "aws_sqs_read_write_policy_arn" {
  default = "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
}

# Variables that must be defined for VPC
variable "vpc_cidr_block" {}

variable "vpc_private_subnet_cidr_blocks" {
  type = "list"
}

variable "vpc_public_subnet_cidr_blocks" {
  type = "list"
}

variable "vpc_external_access_cidr_block" {}
variable "vpc_bastion_instance_type" {}

variable "vpc_availibility_zones" {
  type = "list"
}

variable "git_commit" {}

# RDS
variable "rds_storage_size_gb" {}

variable "rds_engine_version" {}
variable "rds_instance_type" {}
variable "rds_storage_type" {}
variable "rds_database_identifier" {}
variable "rds_database_name" {}
variable "rds_username" {}
variable "rds_password" {}
variable "rds_database_port" {}
variable "rds_backup_retention_period" {}
variable "rds_parameter_group_family" {}
variable "rds_backup_window" {}
variable "rds_maintenance_window" {}
variable "rds_multi_availability_zone" {}
variable "rds_sorage_encrypted" {}
variable "rds_auto_minor_version_upgrade" {}
variable "rds_alarm_cpu_threshold" {}
variable "rds_alarm_disk_queue_threshold" {}
variable "rds_alarm_free_disk_threshold" {}
variable "rds_alarm_free_memory_threshold" {}

# Cache
variable "ec_memcached_desired_clusters" {}

variable "ec_memcached_alarm_cpu_threshold" {}
variable "ec_memcached_instance_type" {}
variable "ec_memcached_engine_version" {}
variable "ec_memcached_maintenance_window" {}
variable "ec_memcached_identifier" {}
variable "ec_memcached_alarm_memory_threshold" {}

variable "ec_memcached_max_item_size" {
  default = "8388608"
}

variable "django_secret_key" {}
variable "django_allowed_hosts" {}
variable "s3_storage_bucket" {}
variable "rollbar_server_side_access_token" {}

# SQS
variable "sqs_queue_name" {}

variable "sqs_max_message_size" {}
variable "sqs_receive_wait_time_seconds" {}
variable "sqs_visibility_timeout_seconds" {}

## Librato
variable "librato_climate_email" {}

variable "librato_climate_token" {}

# Static docs site
variable "climate_docs_site_bucket" {}

variable "climate_docs_logs_bucket" {}
variable "ssl_certificate_arn" {}

variable "papertrail_host" {}
variable "papertrail_port" {}

variable "aws_cloudwatch_logs_policy_arn" {
  default = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

variable "cc_api_alb_ingress_cidr_block" {
  type = "list"
}
