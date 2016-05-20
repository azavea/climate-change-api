# ECS Cluster
resource "aws_ecs_cluster" "ecs_cluster" {
  name = "${var.ecs_cluster_name}-${var.ecs_stack_type}"
}

#
# ECS Task Definitions
#
resource "aws_ecs_task_definition" "cc_web" {
  family = "cc-web-${var.ecs_stack_type}"
  container_definitions = "${template_file.ecs_web_task.rendered}"


}

resource "aws_ecs_task_definition" "cc_management" {
  family = "cc-management-${var.ecs_stack_type}"
  container_definitions = "${template_file.ecs_management_task.rendered}"
}

#
# ECS Services
#
resource "aws_ecs_service" "cc_web" {
  name = "cc-web-${var.ecs_stack_type}"
  cluster = "${aws_ecs_cluster.ecs_cluster.id}"
  task_definition = "${aws_ecs_task_definition.cc_web.family}:${aws_ecs_task_definition.cc_web.revision}"
  desired_count = "${var.desired_instances}"
  iam_role = "${var.ecs_iam_role}"

  deployment_maximum_percent = "${var.deploy_max_instances_pct}"
  deployment_minimum_healthy_percent = "${var.deploy_min_healthy_instances_pct}"

  load_balancer {
    elb_name = "${var.ecs_elb_name}"
    container_name = "django"
    container_port = 8080
  }
}

# CloudWatch resources

resource "aws_cloudwatch_metric_alarm" "cpu" {
  alarm_name = "alarm-${aws_ecs_cluster.ecs_cluster.name}-cpu"
  alarm_description = "Elastic container service CPU utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods = "2"
  metric_name = "CPUUtilization"
  namespace = "AWS/ECS"
  period = "60"
  statistic = "Average"
  threshold = "75"

  dimensions {
    ClusterName = "${aws_ecs_cluster.ecs_cluster.name}"
  }

  alarm_actions = ["${split(",", var.alarm_actions)}"]
}

resource "aws_cloudwatch_metric_alarm" "mem" {
  alarm_name = "alarm-${aws_ecs_cluster.ecs_cluster.name}-mem"
  alarm_description = "Elastic container service memory utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods = "2"
  metric_name = "MemoryUtilization"
  namespace = "AWS/ECS"
  period = "60"
  statistic = "Average"
  threshold = "80"

  dimensions {
    ClusterName = "${aws_ecs_cluster.ecs_cluster.name}"
  }

  alarm_actions = ["${split(",", var.alarm_actions)}"]
}
