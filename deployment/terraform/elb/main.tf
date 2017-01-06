# ELB Security Group
resource "aws_security_group" "sg_ecs_elb" {
  vpc_id = "${var.vpc_id}"
  description = "Security Group for ELB allows SSL only from public"

  ingress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Terraform does not support adding in-line rules and standalone
  # rule resources. To avoid a circular dependency we set the egress
  # rule to the VPC CIDR block
  egress {
    from_port = 8080
    to_port = 8080
    protocol = "tcp"
    cidr_blocks = ["${var.vpc_cidr_block}"]
  }
}


# Create a new load balancer
resource "aws_elb" "elb_ecs_cluster" {
  name = "elb-web-ecs-cluster-${var.ecs_stack_type}"
  subnets = ["${split(",", var.public_subnet_ids)}"]
  security_groups = ["${aws_security_group.sg_ecs_elb.id}"]

  listener {
    instance_port = 8080
    instance_protocol = "http"
    lb_port = 443
    lb_protocol = "https"
    ssl_certificate_id = "${var.ssl_certificate_arn}"
  }

  health_check {
    healthy_threshold = 2
    unhealthy_threshold = 2
    timeout = 3
    target = "HTTP:8080/healthcheck/"
    interval = 10
  }

  cross_zone_load_balancing = true
  idle_timeout = 120
  connection_draining = true
  connection_draining_timeout = 120

  tags {
    Name = "elbECSCluster"
    StackType = "${var.ecs_stack_type}"
  }
}

# ECS Security Group
resource "aws_security_group" "sg_ecs_asg" {
  vpc_id = "${var.vpc_id}"
  description = "Security Group for ECS Cluster Instances"

  ingress {
    from_port = 8080
    to_port = 8080
    protocol = "tcp"
    security_groups = ["${aws_security_group.sg_ecs_elb.id}"]
  }

  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    security_groups = ["${var.bastion_security_group_id}"]
  }

  egress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # TODO: Once the SG is available in RDS outputs
  # update this to use the security group id
  egress {
    from_port = 5432
    to_port = 5432
    protocol = "tcp"
    cidr_blocks = ["${var.vpc_cidr_block}"]
  }

  egress {
    from_port = "${var.cache_port}"
    to_port = "${var.cache_port}"
    protocol = "tcp"
    security_groups = ["${var.cache_security_group_id}"]
  }
}

# Configuration for Memcached security group
resource "aws_security_group_rule" "memcached_instance_ingress" {
    type = "ingress"
    from_port = "${var.cache_port}"
    to_port = "${var.cache_port}"
    protocol = "tcp"

    security_group_id = "${var.cache_security_group_id}"
    source_security_group_id = "${aws_security_group.sg_ecs_asg.id}"
}

resource "aws_security_group_rule" "memcached_instance_egress" {
    type = "egress"
    from_port = "${var.cache_port}"
    to_port = "${var.cache_port}"
    protocol = "tcp"

    security_group_id = "${var.cache_security_group_id}"
    source_security_group_id = "${aws_security_group.sg_ecs_asg.id}"
}

# Launch Config for ECS Cluster
resource "aws_launch_configuration" "launchconf_ecs_cluster" {
  image_id = "${var.ecs_instance_ami_id}"
  instance_type = "${var.ecs_instance_type}"
  user_data = "${data.template_file.ecs_user_data.rendered}"
  iam_instance_profile = "${var.ecs_iam_profile}"
  security_groups = ["${aws_security_group.sg_ecs_asg.id}"]
  key_name = "${var.key_name}"

  lifecycle {
    create_before_destroy = true
  }
}

# ASG for ECS Cluster
resource "aws_autoscaling_group" "asg_ecs_cluster" {
  name = "asgECS-${var.ecs_stack_type}"
  vpc_zone_identifier = ["${var.private_subnet_ids}"]
  max_size = "${var.max_instances}"
  min_size = "${var.desired_instances}"
  health_check_grace_period = 300
  health_check_type = "EC2"
  desired_capacity = "${var.desired_instances}"
  launch_configuration = "${aws_launch_configuration.launchconf_ecs_cluster.name}"

  lifecycle {
    create_before_destroy = true
  }

  tag {
    key = "StackType"
    value = "${var.ecs_stack_type}"
    propagate_at_launch = true
  }

  tag {
    key = "Name"
    value = "asgEcsCluster"
    propagate_at_launch = true
  }
}

# CloudWatch resources

resource "aws_cloudwatch_metric_alarm" "healthy_hosts" {
  alarm_name = "alarm-${aws_elb.elb_ecs_cluster.name}-healthy"
  alarm_description = "Elastic load balancer healthy hosts"
  comparison_operator = "LessThanThreshold"
  evaluation_periods = "1"
  metric_name = "HealthyHostCount"
  namespace = "AWS/ELB"
  period = "60"
  statistic = "Average"
  threshold = "1"

  dimensions {
    LoadBalancerName = "${aws_elb.elb_ecs_cluster.name}"
  }

  alarm_actions = ["${split(",", var.alarm_actions)}"]
}

resource "aws_cloudwatch_metric_alarm" "5xx_alarm" {
  alarm_name = "alarm-${aws_elb.elb_ecs_cluster.name}-5xx"
  alarm_description = "Elastic load balancer 5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods = "1"
  metric_name = "HTTPCode_Backend_5XX"
  namespace = "AWS/ELB"
  period = "300"
  statistic = "Maximum"
  threshold = "2"

  dimensions {
    LoadBalancerName = "${aws_elb.elb_ecs_cluster.name}"
  }

  alarm_actions = ["${split(",", var.alarm_actions)}"]
}

resource "aws_cloudwatch_metric_alarm" "backend_connection_errs" {
  alarm_name = "alarm-${aws_elb.elb_ecs_cluster.name}-BackendConnectionErrors"
  alarm_description = "Elastic load balancer backend connection errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods = "1"
  metric_name = "BackendConnectionErrors"
  namespace = "AWS/ELB"
  period = "300"
  statistic = "Maximum"
  threshold = "2"

  dimensions {
    LoadBalancerName = "${aws_elb.elb_ecs_cluster.name}"
  }

  alarm_actions = ["${split(",", var.alarm_actions)}"]
}
