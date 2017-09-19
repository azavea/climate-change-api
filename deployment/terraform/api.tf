#
# Security group resources
#
resource "aws_security_group" "cc_api_alb" {
  vpc_id = "${data.terraform_remote_state.core.vpc_id}"

  tags {
    Name        = "sgAPILoadBalancer"
    Project     = "${var.project}"
    Environment = "${var.environment}"
  }
}

#
# ALB resources
#
resource "aws_alb" "cc_api" {
  security_groups = ["${aws_security_group.cc_api_alb.id}"]
  subnets         = ["${data.terraform_remote_state.core.public_subnet_ids}"]
  name            = "alb${var.environment}API"

  tags {
    Name        = "albAPI"
    Project     = "${var.project}"
    Environment = "${var.environment}"
  }
}

resource "aws_alb_target_group" "cc_api_http" {
  name = "tg${var.environment}HTTPAPI"

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
  vpc_id   = "${data.terraform_remote_state.core.vpc_id}"

  tags {
    Name        = "tg${var.environment}HTTPAPI"
    Project     = "${var.project}"
    Environment = "${var.environment}"
  }
}

resource "aws_alb_target_group" "cc_api_https" {
  name = "tg${var.environment}HTTPSAPI"

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
  vpc_id   = "${data.terraform_remote_state.core.vpc_id}"

  tags {
    Name        = "tg${var.environment}HTTPSAPI"
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

#
# ECS resources
#
data "template_file" "cc_api_http_ecs_task" {
  template = "${file("task-definitions/nginx.json")}"

  vars = {
    api_server_nginx_url       = "${data.terraform_remote_state.core.aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/cc-nginx:${var.git_commit}"
    cc_api_papertrail_endpoint = "${data.terraform_remote_state.core.papertrail_host}:${data.terraform_remote_state.core.papertrail_port}"
  }
}

resource "aws_ecs_task_definition" "cc_api_http" {
  family                = "${var.environment}HTTPAPI"
  container_definitions = "${data.template_file.cc_api_http_ecs_task.rendered}"
}

resource "aws_ecs_service" "cc_api_http" {
  name                               = "${var.environment}HTTPAPI"
  cluster                            = "${data.terraform_remote_state.core.container_service_cluster_id}"
  task_definition                    = "${aws_ecs_task_definition.cc_api_http.arn}"
  desired_count                      = "${var.cc_api_http_ecs_desired_count}"
  deployment_minimum_healthy_percent = "${var.cc_api_http_ecs_deployment_min_percent}"
  deployment_maximum_percent         = "${var.cc_api_http_ecs_deployment_max_percent}"
  iam_role                           = "${data.terraform_remote_state.core.container_service_cluster_ecs_service_role_name}"

  placement_strategy {
    type  = "spread"
    field = "attribute:ecs.availability-zone"
  }

  load_balancer {
    target_group_arn = "${aws_alb_target_group.cc_api_http.id}"
    container_name   = "nginx"
    container_port   = "80"
  }
}

data "template_file" "cc_api_https_ecs_task" {
  template = "${file("task-definitions/api.json")}"

  vars = {
    api_server_nginx_url             = "${data.terraform_remote_state.core.aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/cc-nginx:${var.git_commit}"
    api_server_django_url            = "${data.terraform_remote_state.core.aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/cc-api:${var.git_commit}"
    api_server_statsd_url            = "${data.terraform_remote_state.core.aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/cc-statsd:${var.git_commit}"
    django_secret_key                = "${var.django_secret_key}"
    rds_host                         = "${data.terraform_remote_state.core.rds_host}"
    rds_database_name                = "${data.terraform_remote_state.core.rds_database_name}"
    rds_username                     = "${data.terraform_remote_state.core.rds_username}"
    rds_password                     = "${data.terraform_remote_state.core.rds_password}"
    ec_memcached_host                = "${data.terraform_remote_state.core.ec_memcached_host}"
    ec_memcached_port                = "${data.terraform_remote_state.core.ec_memcached_port}"
    sqs_queue_name                   = "${data.terraform_remote_state.core.sqs_queue_name}"
    s3_storage_bucket                = "${data.terraform_remote_state.core.s3_storage_bucket}"
    django_allowed_hosts             = "${aws_route53_record.cc_api.fqdn}"
    git_commit                       = "${var.git_commit}"
    rollbar_server_side_access_token = "${var.rollbar_server_side_access_token}"
    environment                      = "${var.environment}"
    cc_api_papertrail_endpoint       = "${data.terraform_remote_state.core.papertrail_host}:${data.terraform_remote_state.core.papertrail_port}"
    aws_region                       = "${var.aws_region}"
  }
}

resource "aws_ecs_task_definition" "cc_api_https" {
  family                = "${var.environment}HTTPSAPI"
  container_definitions = "${data.template_file.cc_api_https_ecs_task.rendered}"

  volume {
    name      = "statsd"
    host_path = "/var/lib/statsd/config.js"
  }
}

resource "aws_ecs_service" "cc_api_https" {
  name                               = "${var.environment}HTTPSAPI"
  cluster                            = "${data.terraform_remote_state.core.container_service_cluster_id}"
  task_definition                    = "${aws_ecs_task_definition.cc_api_https.arn}"
  desired_count                      = "${var.cc_api_https_ecs_desired_count}"
  deployment_minimum_healthy_percent = "${var.cc_api_https_ecs_deployment_min_percent}"
  deployment_maximum_percent         = "${var.cc_api_https_ecs_deployment_max_percent}"
  iam_role                           = "${data.terraform_remote_state.core.container_service_cluster_ecs_service_role_name}"

  placement_strategy {
    type  = "spread"
    field = "attribute:ecs.availability-zone"
  }

  load_balancer {
    target_group_arn = "${aws_alb_target_group.cc_api_https.id}"
    container_name   = "nginx"
    container_port   = "443"
  }
}

data "template_file" "cc_api_management_ecs_task" {
  template = "${file("task-definitions/management.json")}"

  vars {
    management_url                   = "${data.terraform_remote_state.core.aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/cc-api:${var.git_commit}"
    management_statsd_url            = "${data.terraform_remote_state.core.aws_account_id}.dkr.ecr.us-east-1.amazonaws.com/cc-statsd:${var.git_commit}"
    django_secret_key                = "${var.django_secret_key}"
    rds_host                         = "${data.terraform_remote_state.core.rds_host}"
    rds_database_name                = "${data.terraform_remote_state.core.rds_database_name}"
    rds_username                     = "${data.terraform_remote_state.core.rds_username}"
    rds_password                     = "${data.terraform_remote_state.core.rds_password}"
    ec_memcached_host                = "${data.terraform_remote_state.core.ec_memcached_host}"
    ec_memcached_port                = "${data.terraform_remote_state.core.ec_memcached_port}"
    sqs_queue_name                   = "${data.terraform_remote_state.core.sqs_queue_name}"
    s3_storage_bucket                = "${data.terraform_remote_state.core.s3_storage_bucket}"
    django_allowed_hosts             = "${aws_route53_record.cc_api.fqdn}"
    git_commit                       = "${var.git_commit}"
    rollbar_server_side_access_token = "${var.rollbar_server_side_access_token}"
    environment                      = "${var.environment}"
    cc_api_papertrail_endpoint       = "${data.terraform_remote_state.core.papertrail_host}:${data.terraform_remote_state.core.papertrail_port}"
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
