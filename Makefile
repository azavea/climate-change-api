COMMIT=$(shell git describe --always)
STACK_TYPE=staging
REPO=784347171332.dkr.ecr.us-east-1.amazonaws.com/cc-api
AWSCLI_OPTS=--profile climate
S3_BUCKET_DOCS="${STACK_TYPE}-us-east-1-climate-docs"
export COMMIT
export STACK_TYPE
export REPO
export AWSCLI_OPTS

test: STACK_TYPE=test
test: build
	docker-compose -f docker-compose.yml -f docker-compose.$(STACK_TYPE).yml run --rm --entrypoint "./manage.py" django "migrate"
	docker-compose -f docker-compose.yml -f docker-compose.$(STACK_TYPE).yml run --rm --entrypoint "./manage.py" django "test" "--settings" "climate_change_api.settings_test"

push: build test login
	docker-compose -f docker-compose.yml -f docker-compose.$(STACK_TYPE).yml run --rm --entrypoint "./manage.py" django "collectstatic" "--noinput"
	docker tag django:$(COMMIT) $(REPO):$(COMMIT)
	docker push $(REPO):$(COMMIT)

build:
	docker-compose -f docker-compose.yml -f docker-compose.$(STACK_TYPE).yml build django

docs:
	./scripts/docs

login:
	`aws $(AWSCLI_OPTS) ecr get-login`

deploy: docs push
	cd deployment/terraform; $(MAKE) apply
	aws s3 sync --delete ./doc/build/html "s3://${S3_BUCKET_DOCS}"

pulltfvars:
	cd deployment/terraform; $(MAKE) pullvars

pushtfvars:
	cd deployment/terraform; $(MAKE) pushvars

clean:
	cd deployment/terraform; $(MAKE) clean
