#
# S3 resources
#
data "template_file" "read_only_bucket_policy" {
  template = "${file("${path.module}/policies/s3-read-only-anonymous-user.json")}"

  vars {
    bucket = "${var.stack_type}-${var.region}-${var.climate_docs_site_bucket}"
  }
}

resource "aws_s3_bucket" "climate_docs" {
  bucket = "${var.stack_type}-${var.region}-${var.climate_docs_site_bucket}"
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

resource "aws_s3_bucket" "climate_docs_logs" {
  bucket = "${var.stack_type}-${var.region}-${var.climate_docs_logs_bucket}"
  acl    = "log-delivery-write"

  tags {
    Project     = "${var.project}"
    Environment = "${var.environment}"
  }
}

#
# CDN Resources
#
resource "aws_cloudfront_distribution" "climate_docs" {
  origin {
    domain_name = "${aws_s3_bucket.climate_docs.website_endpoint}"
    origin_id   = "ClimateDocsOriginEastId"

    custom_origin_config {
      http_port = 80
      https_port = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols = ["TLSv1", "TLSv1.1", "TLSv1.2"]
    }
  }

  enabled             = true
  http_version        = "http2"
  comment             = "Climate Docs (${var.stack_type})"
  default_root_object = "index.html"
  retain_on_delete    = true

  price_class = "PriceClass_100"
  aliases     = ["${var.r53_public_dns_docs}"]

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "ClimateDocsOriginEastId"

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
    bucket          = "${aws_s3_bucket.climate_docs_logs.id}.s3.amazonaws.com"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = "${var.acm_certificate_arn_docs}"
    minimum_protocol_version = "TLSv1"
    ssl_support_method       = "sni-only"
  }
}

#
# DNS Resources
#
resource "aws_route53_record" "climate_docs_site" {
  zone_id = "${var.r53_hosted_zone_id}"
  name    = "${var.r53_public_dns_docs}"
  type    = "A"

  alias {
    name                   = "${aws_cloudfront_distribution.climate_docs.domain_name}"
    zone_id                = "${aws_cloudfront_distribution.climate_docs.hosted_zone_id}"
    evaluate_target_health = false
  }
}
