#
# CloudFront resources
#
resource "aws_cloudfront_distribution" "cdn" {
  origin {
    domain_name = "${module.docs.site_bucket}.s3.amazonaws.com"
    origin_id   = "originEastId"
  }

  enabled             = true
  http_version        = "http2"
  comment             = "${var.project} Docs (${var.environment})"
  default_root_object = "index.html"
  retain_on_delete    = true

  price_class = "PriceClass_All"
  aliases     = ["docs.${replace(data.aws_route53_zone.external.name, "/.$/", "")}"]

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "originEastId"

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
    bucket          = "${module.docs.logs_bucket}.s3.amazonaws.com"
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
