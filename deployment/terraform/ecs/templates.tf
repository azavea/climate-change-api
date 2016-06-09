/* template files for task definitions */

resource "template_file" "ecs_web_task" {
  filename = "${path.module}/templates/web.json"

  vars {
    stack_type = "${var.ecs_stack_type}"
    git_commit = "${var.git_commit}"
    rds_host = "${var.rds_host}"
    rds_password = "${var.rds_password}"
    rds_username = "${var.rds_username}"
    rds_database_name = "${var.rds_database_name}"
    django_secret_key = "${var.django_secret_key}"
    sqs_queue_name = "${var.sqs_queue_name}"
  }
}

resource "template_file" "ecs_management_task" {
  filename = "${path.module}/templates/management.json"

  vars {
    stack_type = "${var.ecs_stack_type}"
    git_commit = "${var.git_commit}"
    rds_host = "${var.rds_host}"
    rds_password = "${var.rds_password}"
    rds_username = "${var.rds_username}"
    rds_database_name = "${var.rds_database_name}"
    django_secret_key = "${var.django_secret_key}"
    sqs_queue_name = "${var.sqs_queue_name}"
  }
}
