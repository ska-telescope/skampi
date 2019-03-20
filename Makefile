# Set dir of Makefile to a variable to use later
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
BASEDIR := $(notdir $(patsubst %/,%,$(dir $(MAKEPATH))))

# find IP addresses of this machine, setting THIS_HOST to the first address found
THIS_HOST := $(shell ifconfig | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)
DISPLAY := $(THIS_HOST):0
XAUTHORITY ?= ${XAUTHORITY}
KUBE_NAMESPACE ?= default
HELM_RELEASE = test

# activate remote debugger for VSCode (ptvsd)
REMOTE_DEBUG ?= false

# define overides for above variables in here
-include PrivateRules.mak

.PHONY: vars k8s apply logs rm show deploy delete ls podlogs launch-tiller tiller-acls namespace help
.DEFAULT_GOAL := help

vars: ## Display variables - pass in DISPLAY and XAUTHORITY
	@echo "DISPLAY: $(DISPLAY)"
	@echo "XAUTHORITY: $(XAUTHORITY)"
	@echo "Namespace: $(KUBE_NAMESPACE)"

k8s: ## Which kubernetes are we connected to
	@echo "Kubernetes cluster-info:"
	@kubectl cluster-info
	@echo ""
	@echo "kubectl version:"
	@kubectl version
	@echo ""
	@echo "Helm version:"
	@helm version --tiller-namespace $(KUBE_NAMESPACE)

apply: ## apply resource descriptor k8s.yml
	kubectl apply -n $(KUBE_NAMESPACE) -f k8s.yml

logs: ## POD logs for descriptor
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l group=example -o=name`; \
	do echo "-------------------"; \
	echo "Logs for $$i"; \
	kubectl -n $(KUBE_NAMESPACE) logs $$i; \
	done

rm: ## delete applied resources
	kubectl delete -n $(KUBE_NAMESPACE) -f k8s.yml

namespace: ## create the kubernetes namespace
	kubectl describe namespace $(KUBE_NAMESPACE) || kubectl create namespace $(KUBE_NAMESPACE)

deploy: namespace  ## deploy the helm chart
	@helm template chart/ --name $(HELM_RELEASE) \
				 --namespace $(KUBE_NAMESPACE) \
	             --tiller-namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITY)" \
	             --set tangoexample.debug="$(REMOTE_DEBUG)" | kubectl -n $(KUBE_NAMESPACE) apply -f -

show: ## show the helm chart
	@helm template chart/ --name $(HELM_RELEASE) \
				 --namespace $(KUBE_NAMESPACE) \
	             --tiller-namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITY)" \
	             --set tangoexample.debug="$(REMOTE_DEBUG)"

delete: ## delete the helm chart release
	@helm template chart/ --name $(HELM_RELEASE) \
				 --namespace $(KUBE_NAMESPACE) \
	             --tiller-namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITY)" \
	             --set tangoexample.debug="$(REMOTE_DEBUG)" | kubectl -n $(KUBE_NAMESPACE) delete -f -

poddescribe: ## describe Pods executed from Helm chart
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l release=$(HELM_RELEASE) -o=name`; \
	do echo "-------------------"; \
	echo "Describe for $$i"; \
	kubectl -n $(KUBE_NAMESPACE) describe $$i; \
	done

podlogs: ## show Helm chart POD logs
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l release=$(HELM_RELEASE) -o=name`; \
	do echo "-------------------"; \
	echo "Logs for $$i"; \
	kubectl -n $(KUBE_NAMESPACE) logs $$i; \
	done

help:   ## show this help.
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

