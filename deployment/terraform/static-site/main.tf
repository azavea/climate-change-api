#
# S3 resources
#
data "template_file" "read_only_bucket_policy" {
  template = "${file("${path.module}/policies/s3-read-only-anonymous-user.json")}"

  vars {
    bucket = "${lower("${var.environment}")}-${var.aws_region}-${var.site_bucket}"
  }
}

resource "aws_s3_bucket" "site" {
  bucket = "${lower("${var.environment}")}-${var.aws_region}-${var.site_bucket}"
  policy = "${data.template_file.read_only_bucket_policy.rendered}"

  website {
    index_document = "index.html"

    # TODO: Replace with 404.html once the page exists
    error_document = "index.html"
  }

  tags {
    Project     = "${var.project}"
    Environment = "${var.environment}"
  }
}

resource "aws_s3_bucket" "access_logs" {
  bucket = "${lower("${var.environment}")}-${var.aws_region}-${var.access_logs_bucket}"
  acl    = "log-delivery-write"

  tags {
    Project     = "${var.project}"
    Environment = "${var.environment}"
  }
}

#
# CDN Resources
#
resource "aws_cloudfront_distribution" "site" {
  origin {
    domain_name = "${aws_s3_bucket.site.website_endpoint}"
    origin_id   = "SiteOriginEastId"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1", "TLSv1.1", "TLSv1.2"]
    }
  }

  enabled             = true
  http_version        = "http2"
  default_root_object = "index.html"
  retain_on_delete    = true
  aliases             = "${var.site_aliases}"
  price_class         = "PriceClass_100"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "SiteOriginEastId"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    # Only applies if the origin adds Cache-Control headers. The
    # CloudFront default is also 0.
    min_ttl = 0

    # Five minutes, and only applies when the origin DOES NOT
    # supply Cache-Control headers.
    default_ttl = 300

    # One day, but only applies if the origin adds Cache-Control
    # headers. The CloudFront default is 31536000 (one year).
    max_ttl = 86400
  }

  logging_config {
    include_cookies = false
    bucket          = "${aws_s3_bucket.access_logs.id}.s3.amazonaws.com"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = "${var.ssl_certificate_arn}"
    minimum_protocol_version = "TLSv1"
    ssl_support_method       = "sni-only"
  }
}