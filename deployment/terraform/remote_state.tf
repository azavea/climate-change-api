data "terraform_remote_state" "core" {
  backend = "s3"

  config {
    region = "${var.aws_region}"
    bucket = "${lower(var.environment)}-${var.aws_region}-climate-config"
    key    = "terraform/core/state"
  }
}
