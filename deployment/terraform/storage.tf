resource "aws_s3_bucket" "static" {
  bucket = "climate-change-api-${lower("${var.environment}")}"
  acl    = "private"

  cors_rule {
    allowed_origins = ["*"]
    allowed_methods = ["GET"]
    max_age_seconds = 3000
    allowed_headers = ["Authorization"]
  }

  tags {
    Environment = "${var.environment}"
    Project     = "${var.project}"
  }
}
