# SQS
resource "aws_sqs_queue" "sqs_queue" {
  name                       = "${var.sqs_queue_name}"
  max_message_size           = "${var.sqs_max_message_size}"
  receive_wait_time_seconds  = "${var.sqs_receive_wait_time_seconds}"
  visibility_timeout_seconds = "${var.sqs_visibility_timeout_seconds}"
}
