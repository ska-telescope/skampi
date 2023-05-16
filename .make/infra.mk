# include Makefile for Infra related targets and variables

# do not declare targets if help had been invoked
ifneq (long-help,$(firstword $(MAKECMDGOALS)))
ifneq (help,$(firstword $(MAKECMDGOALS)))

MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))

SHELL=/usr/bin/env bash

# If the first argument is "install"...
ifeq (playbooks,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "playbooks"
  TARGET_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(TARGET_ARGS):;@:)
endif

## TARGET: playbooks
## SYNOPSIS: make playbooks <target name>
## HOOKS: None
## VARS:
##       ENVIRONMENT=<environment> - environment to work with eg: stfctechops, engageska, psimid, psilow
##       TF_HTTP_USERNAME=<gitlab-username> - Gitlab User token name with the API scope
##       TF_HTTP_PASSWORD=<user-token> - GitLab API token
##       TF_EXTRA_VARS=<space separated list of environment vars> - additional environment vars to pass to make call
##
##  Run a target from the ska-ser-ansible-collections git submodule.

playbooks: infra-check-env ## Access Ansible Collections submodule targets
	@if [ -d ska-ser-ansible-collections ]; then \
	cd ska-ser-ansible-collections && \
	$(TF_EXTRA_VARS) $(MAKE) $(TARGET_ARGS); \
	else echo "No ska-ser-ansible-collections submodule."; fi

# If the first argument is "orch"...
ifeq (orch,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "orch"
  TARGET_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(TARGET_ARGS):;@:)
endif

## TARGET: orch
## SYNOPSIS: make orch <target name>
## HOOKS: None
## VARS:
##       ENVIRONMENT=<environment> - environment to work with eg: stfctechops, engageska, psimid, psilow
##       TF_HTTP_USERNAME=<gitlab-username> - Gitlab User token name with the API scope
##       TF_HTTP_PASSWORD=<user-token> - GitLab API token
##       TF_EXTRA_VARS=<space separated list of environment vars> - additional environment vars to pass to make call
##
##  Run a target from the ska-ser-orchestration git submodule.

orch: infra-check-orch ## Access Orchestration submodule targets
	@if [ -d ska-ser-orchestration ]; then \
	cd ska-ser-orchestration && \
	$(TF_EXTRA_VARS) $(MAKE) $(TARGET_ARGS); \
	else echo "No ska-ser-orchestration submodule."; fi

.PHONY: infra-check-env infra-check-orch orch playbooks

infra-check-env: ## Private target: Check environment configuration variables
ifndef DATACENTRE
	$(error DATACENTRE is undefined)
endif
ifndef ENVIRONMENT
	$(error ENVIRONMENT is undefined)
endif

infra-check-orch: infra-check-env ## Private target: Check environment configuration variables for orchestration
ifndef SERVICE
	$(error SERVICE is undefined)
endif
ifndef TF_HTTP_USERNAME
	$(error TF_HTTP_USERNAME is undefined)
endif
ifndef TF_HTTP_PASSWORD
	$(error TF_HTTP_PASSWORD is undefined)
endif

endif
endif
