# Static Site
module "static-site" {
  source = "./static-site"

  aws_region  = "${var.aws_region}"
  environment = "${var.environment}"
  project     = "${var.project}"

  site_bucket         = "${var.climate_docs_site_bucket}"
  site_aliases        = ["docs.${var.r53_public_hosted_zone}"]
  access_logs_bucket  = "${var.climate_docs_logs_bucket}"
  ssl_certificate_arn = "${var.ssl_certificate_arn}"
}
