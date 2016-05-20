COMMIT=$(shell git describe --always)
STACK_TYPE=staging
AWSCLI_OPTS= --profile climate
export COMMIT
export STACK_TYPE

.PHONY: apply destroy templates pullvars pushvars clean

apply: templates updatemodules pullvars
	-aws $(AWSCLI_OPTS) s3 cp s3://terraform.cc-api.azavea.com/terraform.tfstate.$(STACK_TYPE) terraform.tfstate
	-terraform apply -var-file=tfvars.$(STACK_TYPE) -var git_commit=$(COMMIT)
	aws $(AWSCLI_OPTS) s3 mv terraform.tfstate s3://terraform.cc-api.azavea.com/terraform.tfstate.$(STACK_TYPE)

updatemodules:
	terraform get -update=true

destroy: updatemodules
	aws $(AWSCLI_OPTS) s3 mv s3://terraform.cc-api.azavea.com/terraform.tfstate.$(STACK_TYPE) terraform.tfstate
	terraform destroy -var-file=tfvars.$(STACK_TYPE) -var git_commit=$(COMMIT)
	rm terraform.tfstate

templates:
	cd ecs/templates; $(MAKE)

pullvars:
	aws $(AWSCLI_OPTS) s3 cp s3://terraform.cc-api.azavea.com/tfvars.$(STACK_TYPE) tfvars.$(STACK_TYPE)

pushvars:
	aws $(AWSCLI_OPTS) s3 cp tfvars.$(STACK_TYPE) s3://terraform.cc-api.azavea.com/tfvars.$(STACK_TYPE)

clean:
	cd ecs/templates; $(MAKE) clean
