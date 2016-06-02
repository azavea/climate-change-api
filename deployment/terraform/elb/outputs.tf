output "elb_sg_id" {
  value = "${aws_security_group.sg_ecs_elb.id}"
}

output "elb_id" {
  value = "${aws_elb.elb_ecs_cluster.id}"
}

output "elb_name" {
  value = "${aws_elb.elb_ecs_cluster.name}"
}
