variable "ecs_iam_role" { }
variable "ecs_stack_type" { }
variable "git_commit" { }
variable "ecs_elb_name" { }
variable "ecs_cluster_name" { }

variable "rds_host" { }
variable "rds_password" { }
variable "rds_username" { }
variable "rds_database_name" { }

variable "alarm_actions" { }

variable "django_secret_key" { }
variable "django_allowed_hosts" { }
variable "sqs_queue_name" { }
variable "cloudwatch_logs_group" { }
variable "s3storage_bucket" { }

variable "desired_instances" { }
variable "deploy_max_instances_pct" { }
variable "deploy_min_healthy_instances_pct" { }
