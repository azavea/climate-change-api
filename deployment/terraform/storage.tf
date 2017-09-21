#
# S3 resources
#
module "docs" {
  source           = "github.com/azavea/terraform-aws-s3-origin?ref=0.2.0"
  bucket_name      = "${lower(var.environment)}-${var.aws_region}-climate-docs"
  logs_bucket_name = "${lower(var.environment)}-${var.aws_region}-climate-docs-logs"
  region           = "${var.aws_region}"

  project     = "${var.project}"
  environment = "${var.environment}"
}
