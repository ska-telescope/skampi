KUBE_NAMESPACE ?= integration#namespace to be used
KUBE_NAMESPACE_SDP ?= integration-sdp#namespace to be used
DOMAIN_TAG ?= test## always set for TANGO_DATABASE_DS
TANGO_DATABASE_DS ?= databaseds-tango-base-$(DOMAIN_TAG) ## Stable name for the Tango DB
RELEASE_NAME ?= test## release name of the chart
DEPLOYMENT_CONFIGURATION ?= skalow## Path of the umbrella chart to work with
HELM_HOST ?= https://nexus.engageska-portugal.pt## helm host url https
MINIKUBE ?= true## Minikube or not
UMBRELLA_CHART_PATH = ./charts/$(DEPLOYMENT_CONFIGURATION)/

.DEFAULT_GOAL := help

clean: ## clean out references to chart tgz's
	@rm -f ./*/charts/*.tgz ./*/Chart.lock ./*/requirements.lock ../repository/*

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

help:  ## show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

publish-chart: ## publish chart in path UMBRELLA_CHART_PATH 
	helm package $(UMBRELLA_CHART_PATH) -u && \
	curl -v -u $(HELM_USERNAME):$(HELM_PASSWORD) --upload-file *.tgz $(HELM_HOST)/repository/helm-chart/

install-chart: namespace namespace_sdp## install the helm chart with name RELEASE_NAME and path UMBRELLA_CHART_PATH on the namespace KUBE_NAMESPACE 
	helm install $(RELEASE_NAME) --dependency-update \
	--set minikube=$(MINIKUBE) \
	--set sdp-prototype.helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
	--set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
	--set tango-base.databaseds.domainTag=$(DOMAIN_TAG) \
	 $(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE) 

uninstall-chart: ## uninstall the helm chart on the namespace KUBE_NAMESPACE
	helm template  $(RELEASE_NAME) $(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE)  | kubectl delete -f - ; \
	helm uninstall  $(RELEASE_NAME) --namespace $(KUBE_NAMESPACE) 

reinstall-chart: uninstall-chart install-chart ## reinstall the  helm chart on the namespace KUBE_NAMESPACE

upgrade-chart: ## upgrade the helm chart on the namespace KUBE_NAMESPACE
	helm upgrade --set minikube=$(MINIKUBE) $(RELEASE_NAME) $(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE) 

.PHONY: help