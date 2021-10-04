THIS_HOST := $(shell (ip a 2> /dev/null || ifconfig) | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)##find IP addresses of this machine, setting THIS_HOST to the first address found
DISPLAY := $(THIS_HOST):0##for GUI applications
XAUTHORITYx ?= ${XAUTHORITY}##for GUI applications
VALUES ?= values.yaml# root level values files. This will override the chart values files.
SKIP_HELM_DEPENDENCY_UPDATE ?= 0# don't run "helm dependency update" on upgrade-skampi-chart

INGRESS_HOST ?= k8s.stfc.skao.int## default ingress host
KUBE_NAMESPACE ?= integration#namespace to be used
KUBE_NAMESPACE_SDP ?= integration-sdp#namespace to be used
DOMAIN_TAG ?= test## always set for TANGO_DATABASE_DS
TANGO_DATABASE_DS ?= databaseds-tango-base-$(DOMAIN_TAG)## Stable name for the Tango DB
USE_NGINX ?= true##Traefik or Nginx
HELM_RELEASE ?= test## release name of the chart
DEPLOYMENT_CONFIGURATION ?= ska-mid## umbrella chart to work with
MINIKUBE ?= true## Minikube or not
UMBRELLA_CHART_PATH ?= ./charts/$(DEPLOYMENT_CONFIGURATION)/##Path of the umbrella chart to install
TANGO_HOST ?= $(TANGO_DATABASE_DS):10000
CHARTS ?= ska-mid

# PSI Low Environment need PROXY values to be set
# This code detects environment and sets the variables
ENV_CHECK := $(shell echo $(CI_ENVIRONMENT_SLUG) | egrep psi-low)
ifneq ($(ENV_CHECK),)
PSI_LOW_PROXY=http://delphoenix.atnf.csiro.au:8888
PSI_LOW_NO_PROXY=localhost,landingpage,oet-rest-$(HELM_RELEASE),127.0.0.1,10.96.0.0/12,192.168.0.0/16,202.9.15.0/24,172.17.0.1/16,.svc.cluster.local
PSI_LOW_PROXY_VALUES = --env=HTTP_PROXY=${PSI_LOW_PROXY} \
				--env=HTTPS_PROXY=${PSI_LOW_PROXY} \
				--env=NO_PROXY=${PSI_LOW_NO_PROXY} \
				--env=http_proxy=${PSI_LOW_PROXY} \
				--env=https_proxy=${PSI_LOW_PROXY} \
				--env=no_proxy=${PSI_LOW_NO_PROXY}

PSI_LOW_SDP_PROXY_VARS= --set ska-sdp.proxy.server=${PSI_LOW_PROXY} \
					--set ska-tango-archiver.enabled=false \
					--set "ska-sdp.proxy.noproxy={${PSI_LOW_NO_PROXY}}"
endif

CI_PROJECT_PATH_SLUG?=skampi##$CI_PROJECT_PATH in lowercase with characters that are not a-z or 0-9 replaced with -. Use in URLs and domain names.
CI_ENVIRONMENT_SLUG?=skampi##The simplified version of the environment name, suitable for inclusion in DNS, URLs, Kubernetes labels, and so on. Available if environment:name is set.
$(shell printf 'global:\n  annotations:\n    app.gitlab.com/app: $(CI_PROJECT_PATH_SLUG)\n    app.gitlab.com/env: $(CI_ENVIRONMENT_SLUG)' > gitlab_values.yaml)

CHART_PARAMS= --set ska-tango-base.xauthority="$(XAUTHORITYx)" \
	--set ska-oso-scripting.ingress.nginx=$(USE_NGINX) \
	--set ska-ser-skuid.ingress.nginx=$(USE_NGINX) \
	--set ska-tango-base.ingress.nginx=$(USE_NGINX) \
	--set ska-webjive.ingress.nginx=$(USE_NGINX) \
	--set global.minikube=$(MINIKUBE) \
	--set ska-sdp.helmdeploy.namespace=$(KUBE_NAMESPACE_SDP) \
	--set global.tango_host=$(TANGO_DATABASE_DS):10000 \
	--set ska-tango-archiver.hostname=$(ARCHIVER_HOST_NAME) \
	--set ska-tango-archiver.dbname=$(ARCHIVER_DBNAME) \
	--set ska-tango-archiver.port=$(ARCHIVER_PORT) \
	--set ska-tango-archiver.dbuser=$(ARCHIVER_DB_USER) \
	--set ska-tango-archiver.dbpassword=$(ARCHIVER_DB_PWD) \
	--values gitlab_values.yaml \
	$(PSI_LOW_SDP_PROXY_VARS)

.DEFAULT_GOAL := help

.PHONY: help

# include makefile targets for release management
-include .make/release.mk
# include makefile targets for Kubernetes management
-include .make/k8s.mk

# include makefile targets for helm linting
-include .make/helm.mk

## local custom includes
# include makefile targets for testing
-include resources/test.mk

# include makefile targets that EDA deployment
-include resources/archiver.mk

## The following should be standard includes
# include makefile targets for make submodule
-include .make/make.mk
# include makefile targets for Makefile help
-include .make/help.mk
# include your own private variables for custom deployment configuration
-include PrivateRules.mak
vars: ## Display variables
	@echo "SKA_K8S_TOOLS_DEPLOY_IMAGE=$(SKA_K8S_TOOLS_DEPLOY_IMAGE)"
	@echo ""
	@echo "KUBE_NAMESPACE=$(KUBE_NAMESPACE)"
	@echo "KUBE_NAMESPACE_SDP=$(KUBE_NAMESPACE_SDP)"
	@echo "INGRESS_HOST=$(INGRESS_HOST)"
	@echo ""
	@echo "CONFIG=$(CONFIG)"
	@echo "DEPLOYMENT_CONFIGURATION=$(DEPLOYMENT_CONFIGURATION)"
	@echo "HELM_RELEASE=$(HELM_RELEASE)"
	@echo "HELM_REPO_NAME=$(HELM_REPO_NAME) ## (should be empty except on Staging & Production)"
	@echo "VALUES=$(VALUES)"
	@echo ""
	@echo "TANGO_DATABASE_DS=$(TANGO_DATABASE_DS)"
	@echo "ARCHIVER_DBNAME=$(ARCHIVER_DBNAME)"
	@echo ""
	@echo "MARK=$(MARK)"

namespace_sdp: ## create the kubernetes namespace for SDP dynamic deployments
	@kubectl describe namespace $(KUBE_NAMESPACE_SDP) > /dev/null 2>&1 ; \
	K_DESC=$$? ; \
	if [ $$K_DESC -eq 0 ] ; \
	then kubectl describe namespace $(KUBE_NAMESPACE_SDP) ; \
	else kubectl create namespace $(KUBE_NAMESPACE_SDP); \
	fi

delete_sdp_namespace: ## delete the kubernetes SDP namespace
	@if [ "default" = "$(KUBE_NAMESPACE_SDP)" ] || [ "kube-system" = "$(KUBE_NAMESPACE_SDP)" ] ; then \
	echo "You cannot delete Namespace: $(KUBE_NAMESPACE_SDP)"; \
	exit 1; \
	else \
		if [ -n "$$(kubectl get ns | grep "$(KUBE_NAMESPACE_SDP)")" ]; then \
			echo "Deleting namespace $(KUBE_NAMESPACE_SDP)" \
			kubectl describe namespace $(KUBE_NAMESPACE_SDP) && kubectl delete namespace $(KUBE_NAMESPACE_SDP); \
		else \
			echo "Namespace $(KUBE_NAMESPACE_SDP) doesn't exist"; \
		fi \
	fi

lint_all:  lint## lint ALL of the helm chart

lint:  ## lint the HELM_CHART of the helm chart
	cd charts; \
	for i in *; do helm dependency update ./$${i}; done; \
	helm lint *

install: clean namespace namespace_sdp check-archiver-dbname upgrade-skampi-chart## install the helm chart on the namespace KUBE_NAMESPACE

uninstall: ## uninstall the helm chart on the namespace KUBE_NAMESPACE
	K_DESC=$$? ; \
	if [ $$K_DESC -eq 0 ] ; \
	then helm uninstall $(HELM_RELEASE) --namespace $(KUBE_NAMESPACE) || true; \
	fi

reinstall-chart: uninstall install ## reinstall the  helm chart on the namespace KUBE_NAMESPACE

upgrade-skampi-chart: ## upgrade the helm chart on the namespace KUBE_NAMESPACE
	@if [ "" == "$(HELM_REPO_NAME)" ]; then \
		echo "Installing Helm charts from current ref of git repository..."; \
		test "$(SKIP_HELM_DEPENDENCY_UPDATE)" == "1" || helm dependency update $(UMBRELLA_CHART_PATH); \
	else \
		echo "Deploying from artefact repository..."; \
		helm repo add $(HELM_REPO_NAME) $(CAR_HELM_REPOSITORY_URL); \
		helm search repo $(HELM_REPO_NAME) | grep DESCRIPTION; \
		helm search repo $(HELM_REPO_NAME) | grep $(UMBRELLA_CHART_PATH); \
	fi
	helm upgrade $(HELM_RELEASE) --install --wait \
		$(CHART_PARAMS) \
		--values $(VALUES) \
		$(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE);

install-or-upgrade: upgrade-skampi-chart## install or upgrade the release

quotas: namespace## delete and create the kubernetes namespace with quotas
	kubectl -n $(KUBE_NAMESPACE) apply -f resources/namespace_with_quotas.yaml

get_pods: ##lists the pods deployed for a particular namespace. @param: KUBE_NAMESPACE
	kubectl get pods -n $(KUBE_NAMESPACE)

get_versions: ## lists the container images used for particular pods
	kubectl get pods -l release=$(HELM_RELEASE) -n $(KUBE_NAMESPACE) -o jsonpath="{range .items[*]}{.metadata.name}{'\n'}{range .spec.containers[*]}{.name}{'\t'}{.image}{'\n\n'}{end}{'\n'}{end}{'\n'}"

links: ## attempt to create the URLs with which to access
	@echo "############################################################################"
	@echo "#            Access the landing page here:"
	@echo "#            https://$(INGRESS_HOST)/$(KUBE_NAMESPACE)/start/"
	@echo "############################################################################"
