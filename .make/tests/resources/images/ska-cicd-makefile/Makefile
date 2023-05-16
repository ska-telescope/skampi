DOCKERFILE ?= Dockerfile.alpine
DOCKER_BUILD_ARGS ?= --build-arg base_image="python:3.9.5-alpine"
NAME ?= ex02-echo
IMG ?= ska-$(NAME)
TAG ?= 0.1.0
BASE = $(shell pwd)

.DEFAULT_GOAL := help

.PHONY: reqs run test lint clean image help

# define private rules and additional makefiles
-include PrivateRules.mak

reqs:  ## install the requirements for project
	poetry install

image: ## Build image with podman
	poetry export > requirements.txt
	docker build --pull $(DOCKER_BUILD_ARGS) -f $(DOCKERFILE) --tag "$(IMG):$(TAG)" .

test:  ## Run the app natively under poetry
	poetry run python echo.py

run: stop  ## Run the app in docker
	docker run  --name $(NAME) --publish 8082:8080 -d $(IMG):$(TAG)
	@echo "Now, point your browser at: http://0.0.0.0:8082/blah/blah"

stop:  ## Stop the running container
	docker inspect $(NAME) >/dev/null 2>&1 && docker rm -f $(NAME) || true

logs:  ## output container logs
	docker logs $(NAME)

echo:  ## Test the echo server
	curl http://0.0.0.0:8082/blah/blah

fmt:  ## reformat code using black
	poetry run black echo.py
	poetry run isort echo.py

lint:  ## Lint check echo server
	poetry run pylint --output-format=parseable echo.py
	poetry run flake8 echo.py

help:  ## show this help.
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
