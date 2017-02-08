resource "aws_elasticache_subnet_group" "memcached" {
  name        = "${var.ec_memcached_identifier}"
  description = "Subnet Group for ElastiCache Memcached"
  subnet_ids  = ["${module.vpc.private_subnet_ids}"]
}

resource "aws_elasticache_parameter_group" "memcached" {
  name        = "${var.ec_memcached_identifier}"
  description = "Parameter Group for ElastiCache Memcached"
  family      = "memcached1.4"
}

module "cache" {
  source = "github.com/azavea/terraform-aws-memcached-elasticache?ref=0.1.0"

  vpc_id                 = "${module.vpc.id}"
  cache_identifier       = "${var.ec_memcached_identifier}"
  desired_clusters       = "${var.ec_memcached_desired_clusters}"
  instance_type          = "${var.ec_memcached_instance_type}"
  engine_version         = "${var.ec_memcached_engine_version}"
  parameter_group        = "${aws_elasticache_parameter_group.memcached.name}"
  subnet_group           = "${aws_elasticache_subnet_group.memcached.name}"
  maintenance_window     = "${var.ec_memcached_maintenance_window}"
  notification_topic_arn = "${aws_sns_topic.global.arn}"

  alarm_cpu_threshold_percent  = "${var.ec_memcached_alarm_cpu_threshold}"
  alarm_memory_threshold_bytes = "${var.ec_memcached_alarm_memory_threshold}"
  alarm_actions                = ["${aws_sns_topic.global.arn}"]

  project     = "${var.project}"
  environment = "${var.environment}"
}
