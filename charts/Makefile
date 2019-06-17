# Set dir of Makefile to a variable to use later
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
BASEDIR := $(notdir $(patsubst %/,%,$(dir $(MAKEPATH))))

# find IP addresses of this machine, setting THIS_HOST to the first address found
THIS_HOST := $(shell ifconfig | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)
DISPLAY := $(THIS_HOST):0
XAUTHORITY ?= $(DISPLAY)
KUBE_NAMESPACE ?= default
HELM_CHART ?= tango-base
HELM_RELEASE = test

# INGRESS_HOST is the host name used in the Ingress resource definition for
# publishing services via the Ingress Controller
INGRESS_HOST ?= $(HELM_RELEASE).$(HELM_CHART).local

SHELL=/bin/bash

# activate remote debugger for VSCode (ptvsd)
REMOTE_DEBUG ?= false

KUBE_CONFIG_BASE64 ?=  ## base64 encoded kubectl credentials for KUBECONFIG
KUBECONFIG ?= /etc/deploy/config ## KUBECONFIG location

# define overides for above variables in here
-include ../PrivateRules.mak

.PHONY: vars k8s logs describe show lint install delete namespace delete_namespace localip helm_dependencies kubectl_dependencies kubeconfig mkcerts help
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
	@helm version --tiller-namespace $(KUBE_NAMESPACE) --client

namespace: ## create the kubernetes namespace
	kubectl describe namespace $(KUBE_NAMESPACE) || kubectl create namespace $(KUBE_NAMESPACE)

deploy: namespace  ## deploy the helm chart
	@helm template $(HELM_CHART)/ --name $(HELM_RELEASE) \
				 --namespace $(KUBE_NAMESPACE) \
	             --tiller-namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITY)" \
	             --set tangoexample.debug="$(REMOTE_DEBUG)" | kubectl -n $(KUBE_NAMESPACE) apply -f -

show: ## show the helm chart
	@helm template $(HELM_CHART)/ --name $(HELM_RELEASE) \
				 --namespace $(KUBE_NAMESPACE) \
	             --tiller-namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITY)" \
	             --set tangoexample.debug="$(REMOTE_DEBUG)"

lint: ## lint check the helm chart
	@helm lint $(HELM_CHART)/ \
		--namespace $(KUBE_NAMESPACE) \
    --tiller-namespace $(KUBE_NAMESPACE) \
		--set ingress.hostname=$(INGRESS_HOST)

install: namespace mkcerts  ## install the helm chart (with Tiller)
	@helm tiller run $(KUBE_NAMESPACE) -- helm install $(HELM_CHART)/ --name $(HELM_RELEASE) \
		--wait \
		--namespace $(KUBE_NAMESPACE) \
    	--tiller-namespace $(KUBE_NAMESPACE) \
		--set ingress.hostname=$(INGRESS_HOST) \
		--set display="$(DISPLAY)" \
		--set xauthority="$(XAUTHORITY)"

delete: ## delete the helm chart release (with Tiller)
	@helm tiller run $(KUBE_NAMESPACE) -- helm delete $(HELM_RELEASE) --purge \
    --tiller-namespace $(KUBE_NAMESPACE)

delete_template: ## delete the helm chart release
	@helm template $(HELM_CHART)/ --name $(HELM_RELEASE) \
				 --namespace $(KUBE_NAMESPACE) \
	             --tiller-namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITYx)" \
	             --set tangoexample.debug="$(REMOTE_DEBUG)" | kubectl -n $(KUBE_NAMESPACE) delete -f -

tests:  ## run Helm chart tests
	@helm tiller run $(KUBE_NAMESPACE) -- helm test $(HELM_RELEASE) --cleanup

delete_namespace: ## delete the kubernetes namespace
	@if [ "default" == "$(KUBE_NAMESPACE)" ] || [ "kube-system" == "$(KUBE_NAMESPACE)" ]; then \
	echo "You cannot delete Namespace: $(KUBE_NAMESPACE)"; \
	exit 1; \
	else \
	kubectl describe namespace $(KUBE_NAMESPACE) && kubectl delete namespace $(KUBE_NAMESPACE); \
	fi

describe: ## describe Pods executed from Helm chart
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l release=$(HELM_RELEASE) -o=name`; \
	do echo "---------------------------------------------------"; \
	echo "Describe for $${i}"; \
	echo kubectl -n $(KUBE_NAMESPACE) describe $${i}; \
	echo "---------------------------------------------------"; \
	kubectl -n $(KUBE_NAMESPACE) describe $${i}; \
	echo "---------------------------------------------------"; \
	echo ""; echo ""; echo ""; \
	done

logs: ## show Helm chart POD logs
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l release=$(HELM_RELEASE) -o=name`; \
	do \
	echo "---------------------------------------------------"; \
	echo "Logs for $${i}"; \
	echo kubectl -n $(KUBE_NAMESPACE) logs $${i}; \
	echo kubectl -n $(KUBE_NAMESPACE) get $${i} -o jsonpath="{.spec.initContainers[*].name}"; \
	echo "---------------------------------------------------"; \
	for j in `kubectl -n $(KUBE_NAMESPACE) get $${i} -o jsonpath="{.spec.initContainers[*].name}"`; do \
	RES=`kubectl -n $(KUBE_NAMESPACE) logs $${i} -c $${j} 2>/dev/null`; \
	echo "initContainer: $${j}"; echo "$${RES}"; \
	echo "---------------------------------------------------";\
	done; \
	echo "Main Pod logs for $${i}"; \
	echo "---------------------------------------------------"; \
	for j in `kubectl -n $(KUBE_NAMESPACE) get $${i} -o jsonpath="{.spec.containers[*].name}"`; do \
	RES=`kubectl -n $(KUBE_NAMESPACE) logs $${i} -c $${j} 2>/dev/null`; \
	echo "Container: $${j}"; echo "$${RES}"; \
	echo "---------------------------------------------------";\
	done; \
	echo "---------------------------------------------------"; \
	echo ""; echo ""; echo ""; \
	done

localip:  ## set local Minikube IP in /etc/hosts file for apigateway
	@new_ip=`minikube ip` && \
	existing_ip=`grep integration.engageska-portugal.pt /etc/hosts || true` && \
	echo "New IP is: $${new_ip}" && \
	echo "Existing IP: $${existing_ip}" && \
	if [ -z "$${existing_ip}" ]; then echo "$${new_ip} integration.engageska-portugal.pt" | sudo tee -a /etc/hosts; \
	else sudo perl -i -ne "s/\d+\.\d+.\d+\.\d+/$${new_ip}/ if /integration.engageska-portugal.pt/; print" /etc/hosts; fi && \
	echo "/etc/hosts is now: " `grep integration.engageska-portugal.pt /etc/hosts`

mkcerts:  ## Make dummy certificates for $(INGRESS_HOST) and Ingress
	@if [ ! -f $(HELM_CHART)//secrets/tls.key ]; then \
	openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 \
	   -keyout $(HELM_CHART)/secrets/tls.key \
		 -out $(HELM_CHART)/secrets/tls.crt \
		 -subj "/CN=$(INGRESS_HOST)/O=Minikube"; \
	else \
	echo "SSL cert already exits in $(HELM_CHART)/secrets ... skipping"; \
	fi

# Utility target to install Helm dependencies
helm_dependencies:
	@which helm ; rc=$$?; \
	if [[ $$rc != 0 ]]; then \
	curl "https://kubernetes-helm.storage.googleapis.com/helm-$(HELM_VERSION)-linux-amd64.tar.gz" | tar zx; \
	mv linux-amd64/helm /usr/bin/; \
	helm init --client-only; \
	fi
	@helm init --client-only
	@if [ ! -d $$HOME/.helm/plugins/helm-tiller ]; then \
	echo "installing tiller plugin..."; \
	helm plugin install https://github.com/rimusz/helm-tiller; \
	fi
	helm version --client
	@helm tiller stop 2>/dev/null || true

# Utility target to install K8s dependencies
kubectl_dependencies:
	@([ -n "$(KUBE_CONFIG_BASE64)" ] && [ -n "$(KUBECONFIG)" ]) || (echo "unset variables [KUBE_CONFIG_BASE64/KUBECONFIG] - abort!"; exit 1)
	@which kubectl ; rc=$$?; \
	if [[ $$rc != 0 ]]; then \
		curl -L -o /usr/bin/kubectl "https://storage.googleapis.com/kubernetes-release/release/$(KUBERNETES_VERSION)/bin/linux/amd64/kubectl"; \
		chmod +x /usr/bin/kubectl; \
		mkdir -p /etc/deploy; \
		echo $(KUBE_CONFIG_BASE64) | base64 -d > $(KUBECONFIG); \
	fi
	@echo -e "\nkubectl client version:"
	@kubectl version --client
	@echo -e "\nkubectl config view:"
	@kubectl config view
	@echo -e "\nkubectl config get-contexts:"
	@kubectl config get-contexts
	@echo -e "\nkubectl version:"
	@kubectl version

kubeconfig: ## export current KUBECONFIG as base64 ready for KUBE_CONFIG_BASE64
	@KUBE_CONFIG_BASE64=`kubectl config view --flatten | base64 -w 0`; \
	echo "KUBE_CONFIG_BASE64: $$(echo $${KUBE_CONFIG_BASE64} | cut -c 1-40)..."; \
	echo "appended to: ../PrivateRules.mak"; \
	echo -e "\n\n# base64 encoded from: kubectl config view --flatten\nKUBE_CONFIG_BASE64 = $${KUBE_CONFIG_BASE64}" >> ../PrivateRules.mak

help:  ## show this help.
	@echo "make targets:"
	@grep -hE '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""; echo "make vars (+defaults):"
	@grep -hE '^[0-9a-zA-Z_-]+ \?=.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = " \?\= "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' | sed -e 's/\#\#/  \#/'