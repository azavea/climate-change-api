# Template for user data
data "template_file" "ecs_user_data" {
  template = "${file("${path.module}/templates/ecs-user-data.yml")}"

  vars {
    stack_type = "${var.ecs_stack_type}"
  }
}
