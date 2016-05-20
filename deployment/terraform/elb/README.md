# ELB

Terraform module to deploy an auto-scaling group and load balancer (meant to be used for an ECS cluster here)

## Usage

```javascript
module "elb" {
  source = "./elb"
  vpc_id = "vpc-12345"
  vpc_cidr_block = "10.0.0.0/16"
  private_subnet_ids = "10.0.1.0/24,10.0.3.0/24"
  public_subnet_ids = "10.0.2.0/24,10.0.4.0/24"
  ssl_certificate_arn = "xxxx:aaaa/arn:ssl"
  ecs_stack_type = "staging"
  ecs_instance_type = "t2.medium"
  ecs_instance_ami_id = "ami-1234"
  key_name = "azavea-climate"
}
```

## Variables
- `vpc_id` - ID for VPC to place elasticache cluster
- `vpc_cidr_block` - CIDR block to allow access from
- `ecs_stack_type` - type of stack this is (e.g. staging, production) used for tags/naming
- `private_subnet_ids` - defines subnet group for auto-scaling group
- `public_subnet_ids` - defines subnet group for load balancer
- `ssl_certificate_arn` - ssl certificate to use for load balancer
- `ecs_instance_type` - instance type to use
- `ecs_instance_ami_id` - ami to use for auto scaling group
- `key_name` - key to use for ssh access

## Outputs

- `elb_sg_id` - security group for load balancer
- `elb_id` - resource ID for load balancer
- `elb_named` - name for load balancer
