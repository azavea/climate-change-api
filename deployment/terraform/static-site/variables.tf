variable "region" {
    default = "us-east-1"
}
variable "project" {
    default = "Unknown"
}
variable "environment" {
    default = "Unknown"
}

variable "stack_type" { }
variable "r53_hosted_zone_id" { }
variable "climate_docs_site_bucket" { }
variable "climate_docs_logs_bucket" { }
variable "r53_public_dns_docs" { }
variable "acm_certificate_arn_docs" { }
