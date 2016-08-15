COMMIT=$(shell git describe --always)
STACK_TYPE=staging
REPO=784347171332.dkr.ecr.us-east-1.amazonaws.com/cc-api
AWSCLI_OPTS=--profile climate
export COMMIT
export STACK_TYPE
export REPO
export AWSCLI_OPTS

test: STACK_TYPE=test
test: build
	docker-compose -f docker-compose.yml -f docker-compose.$(STACK_TYPE).yml run --rm --entrypoint "./manage.py" django "migrate"
	docker-compose -f docker-compose.yml -f docker-compose.$(STACK_TYPE).yml run --rm --entrypoint "./manage.py" django "test"

push: build test login
	docker-compose -f docker-compose.yml -f docker-compose.$(STACK_TYPE).yml run --rm --entrypoint "./manage.py" django "collectstatic" "--noinput"
	docker tag django:$(COMMIT) $(REPO):$(COMMIT)
	docker push $(REPO):$(COMMIT)

build:
	docker-compose -f docker-compose.yml -f docker-compose.$(STACK_TYPE).yml build django

login:
	`aws $(AWSCLI_OPTS) ecr get-login`

deploy: push
	cd deployment/terraform; $(MAKE) apply

pulltfvars:
	cd deployment/terraform; $(MAKE) pullvars

pushtfvars:
	cd deployment/terraform; $(MAKE) pushvars

clean:
	cd deployment/terraform; $(MAKE) clean
