#
# API ALB security group resources
#
resource "aws_security_group_rule" "alb_cc_api_http_ingress" {
  type        = "ingress"
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = "${var.cc_api_alb_ingress_cidr_block}"

  security_group_id = "${aws_security_group.cc_api_alb.id}"
}

resource "aws_security_group_rule" "alb_cc_api_https_ingress" {
  type        = "ingress"
  from_port   = 443
  to_port     = 443
  protocol    = "tcp"
  cidr_blocks = "${var.cc_api_alb_ingress_cidr_block}"

  security_group_id = "${aws_security_group.cc_api_alb.id}"
}

resource "aws_security_group_rule" "alb_cc_api_nat_http_ingress" {
  count = "${length(data.terraform_remote_state.core.private_subnet_ids)}"

  type        = "ingress"
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = ["${element(data.terraform_remote_state.core.nat_gateway_ips, count.index)}/32"]

  security_group_id = "${aws_security_group.cc_api_alb.id}"
}

resource "aws_security_group_rule" "alb_cc_api_nat_https_ingress" {
  count = "${length(data.terraform_remote_state.core.private_subnet_ids)}"

  type        = "ingress"
  from_port   = 443
  to_port     = 443
  protocol    = "tcp"
  cidr_blocks = ["${element(data.terraform_remote_state.core.nat_gateway_ips, count.index)}/32"]

  security_group_id = "${aws_security_group.cc_api_alb.id}"
}

resource "aws_security_group_rule" "alb_cc_api_container_instance_all_egress" {
  type      = "egress"
  from_port = 0
  to_port   = 65535
  protocol  = "tcp"

  security_group_id        = "${aws_security_group.cc_api_alb.id}"
  source_security_group_id = "${data.terraform_remote_state.core.container_instance_security_group_id}"
}

#
# Container instance security group resources
#
resource "aws_security_group_rule" "container_instance_alb_cc_api_all_ingress" {
  type      = "ingress"
  from_port = 0
  to_port   = 65535
  protocol  = "tcp"

  security_group_id        = "${data.terraform_remote_state.core.container_instance_security_group_id}"
  source_security_group_id = "${aws_security_group.cc_api_alb.id}"
}

resource "aws_security_group_rule" "container_instance_alb_cc_api_all_egress" {
  type      = "egress"
  from_port = 0
  to_port   = 65535
  protocol  = "tcp"

  security_group_id        = "${data.terraform_remote_state.core.container_instance_security_group_id}"
  source_security_group_id = "${aws_security_group.cc_api_alb.id}"
}
