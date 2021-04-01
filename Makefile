# Set dir of Makefile to a variable to use later
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
BASEDIR := $(notdir $(patsubst %/,%,$(dir $(MAKEPATH))))

# find IP addresses of this machine, setting THIS_HOST to the first address found
THIS_HOST := $(shell (ip a 2> /dev/null || ifconfig) | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)
DISPLAY := $(THIS_HOST):0
XAUTHORITYx ?= ${XAUTHORITY}
INGRESS_HOST ?= integration.engageska-portugal.pt# Ingress HTTP hostname
USE_NGINX ?= true# Use NGINX as the Ingress Controller
API_SERVER_IP ?= $(THIS_HOST)# Api server IP of k8s
API_SERVER_PORT ?= 6443# Api server port of k8s
EXTERNAL_IP ?= $(THIS_HOST)# For traefik installation
CLUSTER_NAME ?= integration.cluster# For the gangway kubectl setup
CLIENT_ID ?= 417ea12283741e0d74b22778d2dd3f5d0dcee78828c6e9a8fd5e8589025b8d2f# For the gangway kubectl setup, taken from Gitlab
CLIENT_SECRET ?= 27a5830ca37bd1956b2a38d747a04ae9414f9f411af300493600acc7ebe6107f# For the gangway kubectl setup, taken from Gitlab
CHART_SET ?=#for additional flags you want to set when deploying (default empty)
VALUES ?= values.yaml# root level values files. This will override the chart values files.

KUBE_NAMESPACE ?= integration#namespace to be used
ARCHIVER_NAMESPACE ?= ska-archiver#archiver namespace
CONFIGURE_ARCHIVER = test-configure-archiver # Test runner - run to completion the configuration job in K8s
KUBE_NAMESPACE_SDP ?= integration-sdp#namespace to be used
DOMAIN_TAG ?= test## always set for TANGO_DATABASE_DS
TANGO_DATABASE_DS ?= databaseds-tango-base-$(DOMAIN_TAG)## Stable name for the Tango DB
HELM_RELEASE ?= test## release name of the chart
DEPLOYMENT_CONFIGURATION ?= skamid## umbrella chart to work with
HELM_HOST ?= https://nexus.engageska-portugal.pt## helm host url https
MINIKUBE ?= true## Minikube or not
UMBRELLA_CHART_PATH ?= ./charts/$(DEPLOYMENT_CONFIGURATION)/##

# PSI Low Environment need PROXY values to be set
# This code detects environment and sets the variables
ENV_CHECK := $(shell echo $(CI_ENVIRONMENT_SLUG) | egrep psi-low)
ifneq ($(ENV_CHECK),)
PSI_LOW_PROXY=http://delphinus.atnf.csiro.au:8888
PSI_LOW_NO_PROXY=localhost,127.0.0.1,10.96.0.0/12,192.168.0.0/16,202.9.15.0/24,172.17.0.1/16,.svc.cluster.local
PSI_LOW_PROXY_VALUES = --env=HTTP_PROXY=${PSI_LOW_PROXY} \
				--env=HTTPS_PROXY=${PSI_LOW_PROXY} \
				--env=NO_PROXY=${PSI_LOW_NO_PROXY} \
				--env=http_proxy=${PSI_LOW_PROXY} \
				--env=https_proxy=${PSI_LOW_PROXY} \
				--env=no_proxy=${PSI_LOW_NO_PROXY}

PSI_LOW_SDP_PROXY_VARS= --set sdp.proxy.server=${PSI_LOW_PROXY} \
					--set "sdp.proxy.noproxy={${PSI_LOW_NO_PROXY}}"
endif


.DEFAULT_GOAL := help

# include makefile targets for release management
-include .make/release.mk

# include makefile targets for testing
-include .make/test.mk

# include makefile targets that wrap helm
-include .make/helm.mk

# include makefile targets that EDA deployment
-include .make/archiver.mk

vars: ## Display variables
	@echo "Namespace: $(KUBE_NAMESPACE)"
	@echo "HELM_RELEASE: $(HELM_RELEASE)"
	@echo "VALUES: $(VALUES)"
	@echo "TANGO_DATABASE_DS: $(TANGO_DATABASE_DS)"

k8s: ## Which kubernetes are we connected to
	@echo "Kubernetes cluster-info:"
	@kubectl cluster-info
	@echo ""
	@echo "kubectl version:"
	@kubectl version
	@echo ""
	@echo "Helm version:"
	@$(helm_tiller_prefix) helm version

logs: ## POD logs for descriptor
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l group=example -o=name`; \
	do echo "-------------------"; \
	echo "Logs for $$i"; \
	kubectl -n $(KUBE_NAMESPACE) logs $$i; \
	done


clean: ## clean out references to chart tgz's
	@rm -f ./charts/*/charts/*.tgz ./charts/*/Chart.lock ./charts/*/requirements.lock

namespace: ## create the kubernetes namespace
	@kubectl describe namespace $(KUBE_NAMESPACE) > /dev/null 2>&1 ; \
		K_DESC=$$? ; \
		if [ $$K_DESC -eq 0 ] ; \
		then kubectl describe namespace $(KUBE_NAMESPACE); \
		else kubectl create namespace $(KUBE_NAMESPACE); \
		fi

namespace_sdp: ## create the kubernetes namespace for SDP dynamic deployments
	@kubectl describe namespace $(KUBE_NAMESPACE_SDP) > /dev/null 2>&1 ; \
	K_DESC=$$? ; \
	if [ $$K_DESC -eq 0 ] ; \
	then kubectl describe namespace $(KUBE_NAMESPACE_SDP) ; \
	else kubectl create namespace $(KUBE_NAMESPACE_SDP); \
	fi

delete_namespace: ## delete the kubernetes namespace
	@if [ "default" = "$(KUBE_NAMESPACE)" ] || [ "kube-system" = "$(KUBE_NAMESPACE)" ] ; then \
	echo "You cannot delete Namespace: $(KUBE_NAMESPACE)"; \
	exit 1; \
	else \
	kubectl describe namespace $(KUBE_NAMESPACE) && kubectl delete namespace $(KUBE_NAMESPACE); \
	fi

delete_sdp_namespace: ## delete the kubernetes SDP namespace
	@if [ "default" = "$(KUBE_NAMESPACE_SDP)" ] || [ "kube-system" = "$(KUBE_NAMESPACE_SDP)" ] ; then \
	echo "You cannot delete Namespace: $(KUBE_NAMESPACE_SDP)"; \
	exit 1; \
	else \
	kubectl describe namespace $(KUBE_NAMESPACE_SDP) && kubectl delete namespace $(KUBE_NAMESPACE_SDP); \
	fi

lint_all:  lint## lint ALL of the helm chart

lint:  ## lint the HELM_CHART of the helm chart
	cd $(UMBRELLA_CHART_PATH); pwd; helm lint;

help:  ## show this help.
	@echo "make targets:"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ": .*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""; echo "make vars (+defaults):"
	@grep -E '^[0-9a-zA-Z_-]+ \?=.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = " \\?\\= "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: clean namespace namespace_sdp## install the helm chart on the namespace KUBE_NAMESPACE
	@if [ "" = "$(HELM_REPO_NAME)" ]; then \
	echo "Installing from git repository"; \
	helm dependency update $(UMBRELLA_CHART_PATH); \
	else \
	helm repo add $(HELM_REPO_NAME) $(HELM_HOST)/repository/helm-chart; \
	helm search repo $(HELM_REPO_NAME) | grep DESCRIPTION; \
	helm search repo $(HELM_REPO_NAME) | grep $(UMBRELLA_CHART_PATH); \
	fi; \
	helm install $(HELM_RELEASE) \
        --set tango-base.xauthority="$(XAUTHORITYx)" \
    	--set logging.ingress.hostname=$(INGRESS_HOST) \
        --set logging.ingress.nginx=$(USE_NGINX) \
        --set oet-scripts.ingress.hostname=$(INGRESS_HOST) \
        --set oet-scripts.ingress.nginx=$(USE_NGINX) \
        --set skuid.ingress.hostname=$(INGRESS_HOST) \
        --set skuid.ingress.nginx=$(USE_NGINX) \
        --set tango-base.ingress.hostname=$(INGRESS_HOST) \
        --set tango-base.ingress.nginx=$(USE_NGINX) \
        --set webjive.ingress.hostname=$(INGRESS_HOST) \
        --set webjive.ingress.nginx=$(USE_NGINX) \
		--set minikube=$(MINIKUBE) \
		--set global.minikube=$(MINIKUBE) \
		--set sdp.helmdeploy.namespace=$(KUBE_NAMESPACE_SDP) \
		--set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
		--set oet-scripts.tangoDatabaseDS=$(TANGO_DATABASE_DS) \
		--set global.tango_host=$(TANGO_DATABASE_DS):10000 \
		--set tango-base.databaseds.domainTag=$(DOMAIN_TAG) \
		--set tango-base.ingress.hostname=$(INGRESS_HOST) \
		--set webjive.ingress.hostname=$(INGRESS_HOST) \
		$(PSI_LOW_SDP_PROXY_VARS) \
		--values $(VALUES) \
		$(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE);

uninstall: ## uninstall the helm chart on the namespace KUBE_NAMESPACE
	K_DESC=$$? ; \
	if [ $$K_DESC -eq 0 ] ; \
	then helm uninstall  $(HELM_RELEASE) --namespace $(KUBE_NAMESPACE); \
	fi

reinstall-chart: uninstall install ## reinstall the  helm chart on the namespace KUBE_NAMESPACE

upgrade-chart: ## upgrade the helm chart on the namespace KUBE_NAMESPACE
	helm dependency update $(UMBRELLA_CHART_PATH); \
	helm upgrade $(HELM_RELEASE) \
        --set tango-base.xauthority="$(XAUTHORITYx)" \
    	--set logging.ingress.hostname=$(INGRESS_HOST) \
        --set logging.ingress.nginx=$(USE_NGINX) \
        --set oet-scripts.ingress.hostname=$(INGRESS_HOST) \
        --set oet-scripts.ingress.nginx=$(USE_NGINX) \
        --set skuid.ingress.hostname=$(INGRESS_HOST) \
        --set skuid.ingress.nginx=$(USE_NGINX) \
        --set tango-base.ingress.hostname=$(INGRESS_HOST) \
        --set tango-base.ingress.nginx=$(USE_NGINX) \
        --set webjive.ingress.hostname=$(INGRESS_HOST) \
        --set webjive.ingress.nginx=$(USE_NGINX) \
		--set minikube=$(MINIKUBE) \
		--set global.minikube=$(MINIKUBE) \
		--set sdp.helmdeploy.namespace=$(KUBE_NAMESPACE_SDP) \
		--set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
		--set oet-scripts.tangoDatabaseDS=$(TANGO_DATABASE_DS) \
		--set global.tango_host=$(TANGO_DATABASE_DS):10000 \
		--set tango-base.databaseds.domainTag=$(DOMAIN_TAG) \
		--set tango-base.ingress.hostname=$(INGRESS_HOST) \
		--set webjive.ingress.hostname=$(INGRESS_HOST) \
		$(PSI_LOW_SDP_PROXY_VARS) \
		--values $(VALUES) \
		$(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE);

template-chart: clean ## template the helm chart on the namespace KUBE_NAMESPACE
	helm dependency update $(UMBRELLA_CHART_PATH); \
	helm template $(HELM_RELEASE) \
        --set tango-base.xauthority="$(XAUTHORITYx)" \
    	--set logging.ingress.hostname=$(INGRESS_HOST) \
        --set logging.ingress.nginx=$(USE_NGINX) \
        --set oet-scripts.ingress.hostname=$(INGRESS_HOST) \
        --set oet-scripts.ingress.nginx=$(USE_NGINX) \
        --set skuid.ingress.hostname=$(INGRESS_HOST) \
        --set skuid.ingress.nginx=$(USE_NGINX) \
        --set tango-base.ingress.hostname=$(INGRESS_HOST) \
        --set tango-base.ingress.nginx=$(USE_NGINX) \
        --set webjive.ingress.hostname=$(INGRESS_HOST) \
        --set webjive.ingress.nginx=$(USE_NGINX) \
		--set minikube=$(MINIKUBE) \
		--set global.minikube=$(MINIKUBE) \
		--set sdp.helmdeploy.namespace=$(KUBE_NAMESPACE_SDP) \
		--set sdp.tango-base.enabled=false \
		--set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
		--set oet-scripts.tangoDatabaseDS=$(TANGO_DATABASE_DS) \
		--set global.tango_host=$(TANGO_DATABASE_DS):10000 \
		--set tango-base.databaseds.domainTag=$(DOMAIN_TAG) \
		--set tango-base.ingress.hostname=$(INGRESS_HOST) \
		--set webjive.ingress.hostname=$(INGRESS_HOST) \
		$(PSI_LOW_SDP_PROXY_VARS) \
		--values $(VALUES) \
		$(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE);

install-or-upgrade: ## install or upgrade the release
	helm history $(HELM_RELEASE) --namespace $(KUBE_NAMESPACE) > /dev/null 2>&1; \
	K_DESC=$$? ; \
	if [ $$K_DESC -eq 1 ] ; \
	then make install; \
	else make upgrade-chart; \
	fi

# Get the database service name from archiver deployment and MVP deployment
get-service:
	$(eval DBMVPSERVICE := $(shell kubectl get svc -n $(KUBE_NAMESPACE) | grep 10000 |  cut -d " " -f 1)) \
	echo $(DBMVPSERVICE); \
	$(eval DBEDASERVICE := $(shell kubectl get svc -n $(ARCHIVER_NAMESPACE) | grep 10000 |  cut -d " " -f 1)) \
	echo $(DBEDASERVICE); \

# Runs a pod to execute a script. 
# This script configures the archiver for attribute archival defined in json file. Once script is executed, pod is deleted.
configure-archiver: get-service ##configure attributes to archive
		tar -c resources/archiver/ | \
		kubectl run $(CONFIGURE_ARCHIVER) \
		--namespace $(KUBE_NAMESPACE) -i --wait --restart=Never \
		--image-pull-policy=IfNotPresent \
		--image="nexus.engageska-portugal.pt/ska-docker/tango-dsconfig:1.5.0.3" -- \
		/bin/bash -c "sudo tar xv && \
		sudo curl https://gitlab.com/ska-telescope/ska-archiver/-/raw/master/charts/ska-archiver/data/configure_hdbpp.py -o /resources/archiver/configure_hdbpp.py && \
		cd /resources/archiver && \
		sudo python configure_hdbpp.py \
            --cm=tango://$(DBEDASERVICE).$(KUBE_NAMESPACE).svc.cluster.local:10000/archiving/hdbpp/confmanager01 \
            --es=tango://$(DBEDASERVICE).$(KUBE_NAMESPACE).svc.cluster.local:10000/archiving/hdbpp/eventsubscriber01 \
            --attrfile=configuation_low_file.json \
            --th=tango://$(DBEDASERVICE).$(KUBE_NAMESPACE).svc.cluster.local:10000 \
			--ds=$(DBMVPSERVICE) \
			--ns=$(KUBE_NAMESPACE)" && \
		kubectl --namespace $(KUBE_NAMESPACE) delete pod $(CONFIGURE_ARCHIVER);



quotas: namespace## delete and create the kubernetes namespace with quotas
	kubectl -n $(KUBE_NAMESPACE) apply -f resources/namespace_with_quotas.yaml

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
get_pods: ##lists the pods deploued for a particular namespace. @param: KUBE_NAMESPACE
	kubectl get pods -n $(KUBE_NAMESPACE)

get_versions: ## lists the container images used for particular pods
	kubectl get pods -l release=$(HELM_RELEASE) -n $(KUBE_NAMESPACE) -o jsonpath="{range .items[*]}{.metadata.name}{'\n'}{range .spec.containers[*]}{.name}{'\t'}{.image}{'\n\n'}{end}{'\n'}{end}{'\n'}"

set_context: ## Set current kubectl context. @param: KUBE_NAMESPACE
	kubectl config set-context $$(kubectl config current-context) --namespace $${NAMESPACE:-$(KUBE_NAMESPACE)}

get_status:
	kubectl get pod,svc,deployments,pv,pvc,ingress -n $(KUBE_NAMESPACE)

redeploy: delete_all deploy_ordered get_status
wait:
	pods=$$( kubectl get pods -n $(KUBE_NAMESPACE) -o=jsonpath="{range .items[*]}{.metadata.name}{' '}{end}" ) && \
	for pod in $$pods ;  do \
		phase=$$(kubectl get pod -n $(KUBE_NAMESPACE) $$pod -o=jsonpath='{.status.phase}'); \
		if [ "$$phase" = "Succeeded" ]; then \
			echo $$pod $$phase; else \
			kubectl wait --for=condition=Ready -n $(KUBE_NAMESPACE) pod/$$pod; \
		fi; \
	done

.PHONY: help
