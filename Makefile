# Set dir of Makefile to a variable to use later
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
BASEDIR := $(notdir $(patsubst %/,%,$(dir $(MAKEPATH))))

# find IP addresses of this machine, setting THIS_HOST to the first address found
THIS_HOST := $(shell (ip a 2> /dev/null || ifconfig) | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)
DISPLAY := $(THIS_HOST):0
XAUTHORITYx ?= ${XAUTHORITY}
HELM_CHART ?= skampi# Helm Chart to install (see ./charts)
DEPLOYMENT_CONFIGURATION ?= skamid#
SUB_CHART ?= tmc-proto# SubChart to install/uninstall
HELM_CHART_TEST ?= tests# Helm Chart to install (see ./charts)
INGRESS_HOST ?= integration.engageska-portugal.pt# Ingress HTTP hostname
USE_NGINX ?= false# Use NGINX as the Ingress Controller
API_SERVER_IP ?= $(THIS_HOST)# Api server IP of k8s
API_SERVER_PORT ?= 6443# Api server port of k8s
EXTERNAL_IP ?= $(THIS_HOST)# For traefik installation
CLUSTER_NAME ?= integration.cluster# For the gangway kubectl setup
CLIENT_ID ?= 417ea12283741e0d74b22778d2dd3f5d0dcee78828c6e9a8fd5e8589025b8d2f# For the gangway kubectl setup, taken from Gitlab
CLIENT_SECRET ?= 27a5830ca37bd1956b2a38d747a04ae9414f9f411af300493600acc7ebe6107f# For the gangway kubectl setup, taken from Gitlab
CHART_SET ?=#for additional flags you want to set when deploying (default empty)
VALUES ?= values.yaml# root level values files. This will override the chart values files.
DEPLOYMENT_ORDER ?= tango-base cbf-proto csp-proto sdp-prototype tmc-proto oet webjive archiver dsh-lmc-prototype logging skuid## list of charts that will be deployed in order
CHART_FILE ?= post-deployment/exploration/chart_sets.txt # for using an input file of subcharts to deploy one after the other

KUBE_NAMESPACE ?= integration#namespace to be used
KUBE_NAMESPACE_SDP ?= integration-sdp#namespace to be used
DOMAIN_TAG ?= test## always set for TANGO_DATABASE_DS
TANGO_DATABASE_DS ?= databaseds-tango-base-$(DOMAIN_TAG) ## Stable name for the Tango DB
HELM_RELEASE ?= test## release name of the chart
DEPLOYMENT_CONFIGURATION ?= skamid## umbrella chart to work with
HELM_HOST ?= https://nexus.engageska-portugal.pt## helm host url https
MINIKUBE ?= false## Minikube or not
UMBRELLA_CHART_PATH = ./charts/$(DEPLOYMENT_CONFIGURATION)/

.DEFAULT_GOAL := help
-include test.mk

# include makefile targets that wrap helm
 -include helm.mk

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
	@rm -f ./*/charts/*.tgz ./*/Chart.lock ./*/requirements.lock

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

lint_all:  lint## lint ALL of the helm chart

lint:  ## lint the HELM_CHART of the helm chart
	cd $(UMBRELLA_CHART_PATH); pwd; helm lint;

help:  ## show this help.
	@echo "make targets:"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ": .*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""; echo "make vars (+defaults):"
	@grep -E '^[0-9a-zA-Z_-]+ \?=.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = " \\?\\= "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

publish-chart: ## publish chart in path
	helm package $(UMBRELLA_CHART_PATH) -u && \
	curl -v -u $(HELM_USERNAME):$(HELM_PASSWORD) --upload-file *.tgz $(HELM_HOST)/repository/helm-chart/

install: namespace namespace_sdp## install the helm chart on the namespace KUBE_NAMESPACE
	helm history $(HELM_RELEASE) --namespace $(KUBE_NAMESPACE) > /dev/null 2>&1; \
	K_DESC=$$? ; \
	if [ $$K_DESC -eq 1 ] ; \
	then helm install $(HELM_RELEASE) --dependency-update \
		--set tango-base.display="$(DISPLAY)" \
		--set tango-base.xauthority="$(XAUTHORITYx)" \
		--set archiver.display="$(DISPLAY)" \
		--set archiver.xauthority="$(XAUTHORITYx)" \
		--set minikube=$(MINIKUBE) \
		--set sdp-prototype.helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
		--set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
		--set tango-base.databaseds.domainTag=$(DOMAIN_TAG) \
        --set oet.ingress.hostname=$(INGRESS_HOST) \
        --set oet.ingress.nginx=$(USE_NGINX) \
        --set skuid.ingress.hostname=$(INGRESS_HOST) \
        --set skuid.ingress.nginx=$(USE_NGINX) \
        --set tango-base.ingress.hostname=$(INGRESS_HOST) \
        --set tango-base.ingress.nginx=$(USE_NGINX) \
        --set webjive.ingress.hostname=$(INGRESS_HOST) \
        --set webjive.ingress.nginx=$(USE_NGINX) \
		$(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE); \
	fi

uninstall: ## uninstall the helm chart on the namespace KUBE_NAMESPACE
	helm history $(HELM_RELEASE) --namespace $(KUBE_NAMESPACE) > /dev/null 2>&1; \
	K_DESC=$$? ; \
	if [ $$K_DESC -eq 0 ] ; \
	then helm template  $(HELM_RELEASE) $(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE)  | kubectl delete -f - ; helm uninstall  $(HELM_RELEASE) --namespace $(KUBE_NAMESPACE) ;\
    sleep 90s ;\
	fi

reinstall-chart: uninstall-chart install-chart ## reinstall the  helm chart on the namespace KUBE_NAMESPACE

upgrade-chart: ## upgrade the helm chart on the namespace KUBE_NAMESPACE
	helm upgrade $(HELM_RELEASE) \
		--set minikube=$(MINIKUBE) \
		--set sdp-prototype.helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
		--set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
		--set tango-base.databaseds.domainTag=$(DOMAIN_TAG) \
		$(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE);

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
