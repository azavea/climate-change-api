variable "vpc_id" { }
variable "vpc_cidr_block" { }
variable "public_subnet_ids" { }
variable "private_subnet_ids" { }
variable "ecs_stack_type" { }
variable "ecs_iam_profile" { }
variable "ssl_certificate_arn" { }
variable "ecs_instance_ami_id" { }
variable "ecs_instance_type" { }
variable "key_name" { }
variable "alarm_actions" { }

variable "desired_instances" { }
variable "max_instances" { }
variable "bastion_security_group_id" { }
