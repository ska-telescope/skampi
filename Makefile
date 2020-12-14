# Set dir of Makefile to a variable to use later
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
BASEDIR := $(notdir $(patsubst %/,%,$(dir $(MAKEPATH))))

DEPLOYMENT_CONFIGURATION ?= skamid## umbrella chart to work with
HELM_HOST ?= https://nexus.engageska-portugal.pt## helm host url https
MINIKUBE ?= true## Minikube or not
UMBRELLA_CHART_PATH = ./charts/$(DEPLOYMENT_CONFIGURATION)/##

.DEFAULT_GOAL := help

# include makefile targets for release management
-include .make/release.mk

# include makefile targets for testing
-include test.mk

vars: ## Display variables
	@echo "Namespace: $(KUBE_NAMESPACE)"
	@echo "HELM_RELEASE: $(HELM_RELEASE)"
	@echo "VALUES: $(VALUES)"
	@echo "TANGO_DATABASE_DS: $(TANGO_DATABASE_DS)"

help:  ## show this help.
	@echo "make targets:"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ": .*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""; echo "make vars (+defaults):"
	@grep -E '^[0-9a-zA-Z_-]+ \?=.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = " \\?\\= "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: help
