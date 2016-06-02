# Template for user data
resource "template_file" "ecs_user_data" {
  filename = "${path.module}/templates/ecs-user-data.yml"

  vars {
    stack_type = "${var.ecs_stack_type}"
  }
}
