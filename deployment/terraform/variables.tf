variable "project" {
  default = "Climate Change API"
}

variable "environment" {
  default = "Staging"
}

variable "aws_region" {
  default = "us-east-1"
}

variable "rds_database_name" {
  default = "climate"
}

variable "cc_api_alb_ingress_cidr_block" {
  type = "list"
}

variable "cc_api_http_ecs_desired_count" {
  default = "1"
}

variable "cc_api_http_ecs_deployment_min_percent" {
  default = "0"
}

variable "cc_api_http_ecs_deployment_max_percent" {
  default = "100"
}

variable "cc_api_https_ecs_desired_count" {
  default = "1"
}

variable "cc_api_https_ecs_deployment_min_percent" {
  default = "0"
}

variable "cc_api_https_ecs_deployment_max_percent" {
  default = "100"
}

variable "git_commit" {}

variable "django_secret_key" {}

variable "rollbar_server_side_access_token" {}

variable "papertrail_host" {}

variable "papertrail_port" {}

variable "climate_docs_site_bucket" {}

variable "climate_docs_logs_bucket" {}

variable "ssl_certificate_arn" {}
