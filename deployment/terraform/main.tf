provider "aws" {
  region = "us-east-1"
  profile = "climate"
}

# set up SNS topic for monitoring
resource "aws_sns_topic" "cc_sns_topic" {
  name = "cc-monitor-alerts-${var.stack_type}"
}

# VPC module for setting up vpc
module "vpc" {
  name = "cc-monitor-${var.stack_type}"
  source = "github.com/azavea/terraform-aws-vpc?ref=1.1.0"
  region = "us-east-1"
  key_name = "${var.key_name}"
  external_access_cidr_block = "66.212.12.106/32"
  private_subnet_cidr_blocks = "10.0.1.0/24,10.0.3.0/24"
  public_subnet_cidr_blocks = "10.0.0.0/24,10.0.2.0/24"
  availability_zones = "us-east-1a,us-east-1c"
  bastion_ami = "ami-f5f41398"
  bastion_instance_type = "${var.vpc_bastion_instance_type}"
}

module "rds" {
  source = "github.com/azavea/terraform-aws-postgresql-rds?ref=0.4.0"
  vpc_id = "${module.vpc.id}"
  vpc_cidr_block = "${var.vpc_cidr_block}"

  allocated_storage = "${var.rds_storage_size_gb}"
  engine_version = "9.5.2"
  instance_type = "${var.rds_instance_type}"
  storage_type = "gp2"
  database_name = "${var.rds_database_name}"
  database_username = "${var.rds_username}"
  database_password = "${var.rds_password}"
  backup_retention_period = "30"
  backup_window = "04:00-04:30"
  maintenance_window = "sun:04:30-sun:05:30"
  multi_availability_zone = true
  storage_encrypted = false

  private_subnet_ids = "${module.vpc.private_subnet_ids}"
  parameter_group_family = "postgres9.5"
  alarm_actions = "${aws_sns_topic.cc_sns_topic.arn}"
}

resource "aws_elasticache_subnet_group" "memcached" {
  name = "cc-ec-subnet-group"
  description = "Subnet Group for ElastiCache Memcached"
  subnet_ids = ["${split(",", module.vpc.private_subnet_ids)}"]
}

resource "aws_elasticache_parameter_group" "memcached" {
  name = "cc-ec-parameter-group"
  description = "Parameter Group for ElastiCache Memcached"
  family = "memcached1.4"
}

module "cache" {
  source = "github.com/azavea/terraform-aws-memcached-elasticache?ref=0.1.0"

  vpc_id                     = "${module.vpc.id}"
  cache_identifier           = "cc-ec-memcached"
  desired_clusters           = "1"
  instance_type              = "cache.t2.micro"
  engine_version             = "1.4.33"
  parameter_group            = "${aws_elasticache_parameter_group.memcached.name}"
  subnet_group               = "${aws_elasticache_subnet_group.memcached.name}"
  maintenance_window         = "sun:02:30-sun:03:30"
  notification_topic_arn     = "${aws_sns_topic.cc_sns_topic.arn}"

  alarm_cpu_threshold_percent  = "75"
  alarm_memory_threshold_bytes = "100000000"
  alarm_actions                = ["${aws_sns_topic.cc_sns_topic.arn}"]
}

# Alarm for CPU credits for t2 instances
resource "aws_cloudwatch_metric_alarm" "rds_cpu_credits_alarm" {
  alarm_name = "alarm-rds-${module.rds.id}-CPUCredits"
  alarm_description = "RDS CPU Credits"
  comparison_operator = "LessThanThreshold"
  evaluation_periods = "1"
  metric_name = "CPUCreditBalance"
  namespace = "AWS/RDS"
  period = "60"
  statistic = "Average"
  threshold = "${var.rds_cpu_credit_alarm_threshold}"

  dimensions {
    DBInstanceIdentifier = "${module.rds.id}"
  }

  alarm_actions = ["${aws_sns_topic.cc_sns_topic.arn}"]
}

# Creates ELB with ASG for ECS stack
module "elb" {
  source = "./elb"
  vpc_id = "${module.vpc.id}"
  vpc_cidr_block = "${var.vpc_cidr_block}"
  public_subnet_ids = "${module.vpc.public_subnet_ids}"
  private_subnet_ids = "${module.vpc.private_subnet_ids}"
  bastion_security_group_id = "${module.vpc.bastion_security_group_id}"
  cache_security_group_id = "${module.cache.cache_security_group_id}"
  cache_port = "${module.cache.port}"
  ssl_certificate_arn = "${var.elb_ssl_certificate_arn}"
  ecs_stack_type = "${var.stack_type}"
  ecs_iam_profile = "${var.ecs_iam_profile}"
  ecs_instance_type = "${var.ecs_instance_type}"
  ecs_instance_ami_id = "${var.ecs_instance_ami_id}"
  key_name = "${var.key_name}"

  alarm_actions = "${aws_sns_topic.cc_sns_topic.arn}"

  desired_instances = "${var.desired_instances}"
  max_instances = "${var.max_instances}"
}

# Task definitions and services
module "ecs" {
  source = "./ecs"
  ecs_cluster_name = "cc-api"
  ecs_elb_name = "${module.elb.elb_name}"
  ecs_iam_role = "${var.ecs_iam_role}"
  ecs_stack_type = "${var.stack_type}"
  git_commit = "${var.git_commit}"
  rds_host = "${module.rds.hostname}"
  rds_password = "${var.rds_password}"
  rds_username = "${var.rds_username}"
  rds_database_name = "${var.rds_database_name}"
  ec_memcached_host = "${module.cache.endpoint}"
  ec_memcached_port = "${module.cache.port}"

  alarm_actions = "${aws_sns_topic.cc_sns_topic.arn}"
  django_secret_key = "${var.django_secret_key}"
  django_allowed_hosts = "${var.django_allowed_hosts}"
  sqs_queue_name = "${var.sqs_queue_name}"
  s3storage_bucket = "${var.s3storage_bucket}"
  cloudwatch_logs_group = "${var.cloudwatch_logs_group}"

  desired_instances = "${var.desired_instances}"
  deploy_max_instances_pct = "${var.deploy_max_instances_pct}"
  deploy_min_healthy_instances_pct = "${var.deploy_min_healthy_instances_pct}"
}

# SQS
resource "aws_sqs_queue" "sqs_queue" {
  name = "${var.sqs_queue_name}"
  max_message_size = 1024
  receive_wait_time_seconds = 10
  visibility_timeout_seconds = 14400
}

# Static Site
module "static-site" {
  source = "./static-site"

  region = "us-east-1"
  stack_type = "${var.stack_type}"

  r53_hosted_zone_id = "${var.r53_hosted_zone_id}"

  climate_docs_site_bucket = "${var.climate_docs_site_bucket}"
  climate_docs_logs_bucket = "${var.climate_docs_logs_bucket}"
  r53_public_dns_docs = "${var.r53_public_dns_docs}"
  acm_certificate_arn_docs = "${var.acm_certificate_arn_docs}"
}