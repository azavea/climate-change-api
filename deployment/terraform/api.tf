#
# Security group resources
#
resource "aws_security_group" "cc_api_alb" {
  vpc_id = "${module.vpc.id}"

  tags {
    Name        = "sgAPIServerLoadBalancer"
    Project     = "${var.project}"
    Environment = "${var.environment}"
  }
}

#
# ALB resources
#
resource "aws_alb" "cc_api" {
  security_groups = ["${aws_security_group.cc_api_alb.id}"]
  subnets         = ["${module.vpc.public_subnet_ids}"]
  name            = "alb${var.environment}APIServer"

  tags {
    Name        = "albAPIServer"
    Project     = "${var.project}"
    Environment = "${var.environment}"
  }
}

resource "aws_alb_target_group" "cc_api_http" {
  # Name can only be 32 characters long, so we MD5 hash the name and
  # truncate it to fit.
  name = "tf-tg-${replace("${md5("${var.environment}HTTPAPIServer")}", "/(.{0,26})(.*)/", "$1")}"

  health_check {
    healthy_threshold   = "3"
    interval            = "60"
    matcher             = "301"
    protocol            = "HTTP"
    timeout             = "3"
    path                = "/"
    unhealthy_threshold = "2"
  }

  port     = "80"
  protocol = "HTTP"
  vpc_id   = "${module.vpc.id}"

  tags {
    Name        = "tg${var.environment}HTTPAPIServer"
    Project     = "${var.project}"
    Environment = "${var.environment}"
  }
}

resource "aws_alb_target_group" "cc_api_https" {
  # Name can only be 32 characters long, so we MD5 hash the name and
  # truncate it to fit.
  name = "tf-tg-${replace("${md5("${var.environment}HTTPSAPIServer")}", "/(.{0,26})(.*)/", "$1")}"

  health_check {
    healthy_threshold   = "3"
    interval            = "30"
    protocol            = "HTTP"
    timeout             = "3"
    path                = "/healthcheck/"
    unhealthy_threshold = "2"
  }

  port     = "443"
  protocol = "HTTP"
  vpc_id   = "${module.vpc.id}"

  tags {
    Name        = "tg${var.environment}HTTPSAPIServer"
    Project     = "${var.project}"
    Environment = "${var.environment}"
  }
}

resource "aws_alb_listener" "cc_api_http" {
  load_balancer_arn = "${aws_alb.cc_api.id}"
  port              = "80"
  protocol          = "HTTP"

  default_action {
    target_group_arn = "${aws_alb_target_group.cc_api_http.id}"
    type             = "forward"
  }
}

resource "aws_alb_listener" "cc_api_https" {
  load_balancer_arn = "${aws_alb.cc_api.id}"
  port              = "443"
  protocol          = "HTTPS"
  certificate_arn   = "${var.ssl_certificate_arn}"

  default_action {
    target_group_arn = "${aws_alb_target_group.cc_api_https.id}"
    type             = "forward"
  }
}

data "template_file" "cc_api_http_ecs_task" {
  template = "${file("task-definitions/nginx.json")}"

  vars = {
    api_server_nginx_url       = "${var.aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/cc-nginx:${var.git_commit}"
    cc_api_papertrail_endpoint = "${var.papertrail_host}:${var.papertrail_port}"
  }
}

resource "aws_ecs_task_definition" "cc_api_http" {
  family                = "${var.environment}HTTPAPIServer"
  container_definitions = "${data.template_file.cc_api_http_ecs_task.rendered}"
}

resource "aws_ecs_service" "cc_api_http" {
  name                               = "${var.environment}HTTPAPIServer"
  cluster                            = "${aws_ecs_cluster.container_instance.id}"
  task_definition                    = "${aws_ecs_task_definition.cc_api_http.arn}"
  desired_count                      = "${var.cc_api_http_ecs_desired_count}"
  deployment_minimum_healthy_percent = "${var.cc_api_http_ecs_deployment_min_percent}"
  deployment_maximum_percent         = "${var.cc_api_http_ecs_deployment_max_percent}"
  iam_role                           = "${aws_iam_role.container_instance_ecs.name}"

  load_balancer {
    target_group_arn = "${aws_alb_target_group.cc_api_http.id}"
    container_name   = "nginx"
    container_port   = "80"
  }
}

data "template_file" "cc_api_https_ecs_task" {
  template = "${file("task-definitions/api.json")}"

  vars = {
    api_server_nginx_url             = "${var.aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/cc-nginx:${var.git_commit}"
    api_server_django_url            = "${var.aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/cc-api:${var.git_commit}"
    api_server_statsd_url            = "${var.aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/cc-statsd:${var.git_commit}"
    django_secret_key                = "${var.django_secret_key}"
    rds_host                         = "${module.database.hostname}"
    rds_password                     = "${var.rds_password}"
    rds_username                     = "${var.rds_username}"
    rds_database_name                = "${var.rds_database_name}"
    ec_memcached_host                = "${module.cache.endpoint}"
    ec_memcached_port                = "${module.cache.port}"
    sqs_queue_name                   = "${var.sqs_queue_name}"
    s3_storage_bucket                = "${aws_s3_bucket.static.id}"
    django_allowed_hosts             = "${var.django_allowed_hosts}"
    git_commit                       = "${var.git_commit}"
    rollbar_server_side_access_token = "${var.rollbar_server_side_access_token}"
    environment                      = "${var.environment}"
    feature_flag_array_data          = "${var.feature_flag_array_data}"
    cc_api_papertrail_endpoint       = "${var.papertrail_host}:${var.papertrail_port}"
    aws_region                       = "${var.aws_region}"
  }
}

resource "aws_ecs_task_definition" "cc_api_https" {
  family                = "${var.environment}HTTPSAPIServer"
  container_definitions = "${data.template_file.cc_api_https_ecs_task.rendered}"

  volume {
    name      = "statsd"
    host_path = "/var/lib/statsd/config.js"
  }
}

resource "aws_ecs_service" "cc_api_https" {
  name                               = "${var.environment}HTTPSAPIServer"
  cluster                            = "${aws_ecs_cluster.container_instance.id}"
  task_definition                    = "${aws_ecs_task_definition.cc_api_https.arn}"
  desired_count                      = "${var.cc_api_https_ecs_desired_count}"
  deployment_minimum_healthy_percent = "${var.cc_api_https_ecs_deployment_min_percent}"
  deployment_maximum_percent         = "${var.cc_api_https_ecs_deployment_max_percent}"
  iam_role                           = "${aws_iam_role.container_instance_ecs.name}"

  load_balancer {
    target_group_arn = "${aws_alb_target_group.cc_api_https.id}"
    container_name   = "nginx"
    container_port   = "443"
  }
}

data "template_file" "cc_api_management_ecs_task" {
  template = "${file("task-definitions/management.json")}"

  vars {
    management_url                   = "${var.aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/cc-api:${var.git_commit}"
    management_statsd_url            = "${var.aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/cc-statsd:${var.git_commit}"
    django_secret_key                = "${var.django_secret_key}"
    rds_host                         = "${module.database.hostname}"
    rds_password                     = "${var.rds_password}"
    rds_username                     = "${var.rds_username}"
    rds_database_name                = "${var.rds_database_name}"
    ec_memcached_host                = "${module.cache.endpoint}"
    ec_memcached_port                = "${module.cache.port}"
    sqs_queue_name                   = "${var.sqs_queue_name}"
    s3_storage_bucket                = "${aws_s3_bucket.static.id}"
    django_allowed_hosts             = "${var.django_allowed_hosts}"
    git_commit                       = "${var.git_commit}"
    rollbar_server_side_access_token = "${var.rollbar_server_side_access_token}"
    environment                      = "${var.environment}"
    feature_flag_array_data          = "${var.feature_flag_array_data}"
    cc_api_papertrail_endpoint       = "${var.papertrail_host}:${var.papertrail_port}"
    aws_region                       = "${var.aws_region}"
  }
}

resource "aws_ecs_task_definition" "cc_api_management" {
  family                = "${var.environment}Management"
  container_definitions = "${data.template_file.cc_api_management_ecs_task.rendered}"

  volume {
    name      = "tmp"
    host_path = "/tmp"
  }

  volume {
    name      = "statsd"
    host_path = "/var/lib/statsd/config.js"
  }
}
