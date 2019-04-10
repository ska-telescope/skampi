# Set dir of Makefile to a variable to use later
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
BASEDIR := $(notdir $(patsubst %/,%,$(dir $(MAKEPATH))))

# find IP addresses of this machine, setting THIS_HOST to the first address found
THIS_HOST := $(shell ifconfig | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)
DISPLAY := $(THIS_HOST):0
XAUTHORITYx ?= ${XAUTHORITY}
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
	@echo "XAUTHORITY: $(XAUTHORITYx)"
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
	             --set xauthority="$(XAUTHORITYx)" \
	             --set tangoexample.debug="$(REMOTE_DEBUG)" | kubectl -n $(KUBE_NAMESPACE) apply -f -

show: ## show the helm chart
	@helm template chart/ --name $(HELM_RELEASE) \
				 --namespace $(KUBE_NAMESPACE) \
	             --tiller-namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITYx)" \
	             --set tangoexample.debug="$(REMOTE_DEBUG)"

delete: ## delete the helm chart release
	@helm template chart/ --name $(HELM_RELEASE) \
				 --namespace $(KUBE_NAMESPACE) \
	             --tiller-namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITYx)" \
	             --set tangoexample.debug="$(REMOTE_DEBUG)" | kubectl -n $(KUBE_NAMESPACE) delete -f -


poddescribe: ## describe Pods executed from Helm chart
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l release=$(HELM_RELEASE) -o=name`; \
	do echo "---------------------------------------------------"; \
	echo "Describe for $${i}"; \
	echo kubectl -n $(KUBE_NAMESPACE) describe $${i}; \
	echo "---------------------------------------------------"; \
	kubectl -n $(KUBE_NAMESPACE) describe $${i}; \
	echo "---------------------------------------------------"; \
	echo ""; echo ""; echo ""; \
	done

podlogs: ## show Helm chart POD logs
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

#mkcerts:  ## Make dummy certificates for integration.engageska-portugal.pt and Ingress
#	openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 \
#	   -keyout chart/data/tls.key \
#		 -out chart/data/tls.crt \
#		 -subj "/CN=integration.engageska-portugal.pt/O=Integration"

help:   ## show this help.
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
