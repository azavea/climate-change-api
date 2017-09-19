#
# Documentation site resources
#
module "static-site" {
  source = "./static-site"

  aws_region  = "${var.aws_region}"
  environment = "${var.environment}"
  project     = "${var.project}"

  site_bucket         = "${var.climate_docs_site_bucket}"
  site_aliases        = ["docs.${replace(data.aws_route53_zone.external.name, "/.$/", "")}"]
  access_logs_bucket  = "${var.climate_docs_logs_bucket}"
  ssl_certificate_arn = "${var.ssl_certificate_arn}"
}
