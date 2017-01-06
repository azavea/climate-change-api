# ECS

Terraform module to deploy an elastic container service cluster

## Usage

```javascript
module "ecs" {
  source = "./ecs"
  ecs_iam_role = "xxx:aaa/role"
  ecs_stack_type = "staging"
  ecs_image_tag = "develop"
  ecs_cluster_name = "cc-api"
  rds_host = "aws-rds-xxxx.com"
  rds_password = "axxxxxxx"
  rds_username = "climate"
  rds_database_name = "climate"
}
```

## Variables
- `ecs_iam_role` - IAM role for ECS service (must be able to modify ELB)
- `ecs_stack_type` - type of stack (e.g. staging, production)
- `ecs_image_tag` - tag of docker image to use (e.g. `develop`, `1.0.0`)
- `ecs_elb_name` - name of load balancer that web service should use
- `ecs_cluster_name` - name of cluster
- `rds_host` - hostname of RDS instance that task definitions should use
- `rds_password` - password of RDS instance (inserted in environment for task definitions)
- `rds_username` - user to access database
- `rds_database_name` - name of database to use
- `ec_memcached_host` - hostname of the ElastiCache Memcached instance
- `ec_memcached_port` - port of the ElastiCache Memcached instance

## Outputs

- `ecs_cluster` - name of ECS cluster
