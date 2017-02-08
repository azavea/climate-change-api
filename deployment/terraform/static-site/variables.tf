variable "aws_region" {
  default = "us-east-1"
}

variable "project" {
  default = "Unknown"
}

variable "environment" {
  default = "Unknown"
}

variable "site_bucket" {}

variable "site_aliases" {
  type = "list"
}

variable "access_logs_bucket" {}
variable "ssl_certificate_arn" {}
