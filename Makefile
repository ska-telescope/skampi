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

# include makefile targets for interrim image building
-include .make/oci.mk

# include makefile targets for Kubernetes management
-include .make/k8s.mk

# include makefile targets for helm linting
-include .make/helm.mk

# ## local custom includes
# # include makefile targets for testing
# -include resources/test.mk

# include makefile targets for EDA deployment
-include resources/archiver.mk

# include core makefile targets
-include .make/base.mk

SKAMPI_K8S_CHART ?= ska-mid
SKAMPI_K8S_CHARTS ?= ska-mid ska-low

CI_JOB_ID?=local
#
# IMAGE_TO_TEST defines the tag of the Docker image to test
IMAGE_TO_TEST = artefact.skao.int/ska-tango-images-pytango-builder-alpine:0.3.0## docker image that will be run for testing purpose
# Test runner - run to completion job in K8s
TEST_RUNNER = test-makefile-runner-$(CI_JOB_ID)##name of the pod running the k8s_tests
#
# defines a function to copy the ./test-harness directory into the K8s TEST_RUNNER
# and then runs the requested make target in the container.
# capture the output of the test in a build folder inside the container
#
MARK ?= fast## this variable allow the mark parameter in the pytest
FILE ?= ##this variable allow to execution of a single file in the pytest
SLEEPTIME ?= 1200s ##amount of sleep time for the smoketest target
COUNT ?= 1## amount of repetition for pytest-repeat
BIGGER_THAN ?= ## get_size_images parameter: if not empty check if images are bigger than this (in MB)

TELESCOPE = 'SKA-Mid'
CENTRALNODE = 'ska_mid/tm_central/central_node'
SUBARRAY = 'ska_mid/tm_subarray_node'
# Define environmenvariables required by OET
ifneq (,$(findstring low,$(KUBE_NAMESPACE)))
	TELESCOPE = 'SKA-Low'
	CENTRALNODE = 'ska_low/tm_central/central_node'
	SUBARRAY = 'ska_low/tm_subarray_node'
endif

PUBSUB = true

-include PrivateRules.mak


K8S_TEST_MAKE_PARAMS = \
	SKUID_URL=ska-ser-skuid-$(HELM_RELEASE)-svc.$(KUBE_NAMESPACE).svc.cluster.local:9870 \
	KUBE_NAMESPACE=$(KUBE_NAMESPACE) \
	HELM_RELEASE=$(HELM_RELEASE) \
	TANGO_HOST=$(TANGO_HOST) \
	CI_JOB_TOKEN=$(CI_JOB_TOKEN) \
	MARK='$(MARK)' \
	COUNT=$(COUNT) \
	FILE='$(FILE)' \
	SKA_TELESCOPE=$(TELESCOPE) \
	CENTRALNODE_FQDN=$(CENTRALNODE) \
	SUBARRAYNODE_FQDN_PREFIX=$(SUBARRAY) \
	OET_READ_VIA_PUBSUB=$(PUBSUB) \
	JIRA_AUTH=$(JIRA_AUTH) \
	CAR_RAW_USERNAME=$(RAW_USER) \
	CAR_RAW_PASSWORD=$(RAW_PASS) \
	CAR_RAW_REPOSITORY_URL=$(RAW_HOST)


vars: ## Display variables
	@echo "SKA_K8S_TOOLS_DEPLOY_IMAGE=$(SKA_K8S_TOOLS_DEPLOY_IMAGE)"
	@echo ""
	@echo "KUBE_NAMESPACE=$(KUBE_NAMESPACE)"
	@echo "KUBE_NAMESPACE_SDP=$(KUBE_NAMESPACE_SDP)"
	@echo "INGRESS_HOST=$(INGRESS_HOST)"
	@echo "DEPLOYMENT_CONFIGURATION=$(DEPLOYMENT_CONFIGURATION)"
	@echo "HELM_RELEASE=$(HELM_RELEASE)"
	@echo "HELM_REPO_NAME=$(HELM_REPO_NAME) ## (should be empty except on Staging & Production)"
	@echo "VALUES=$(VALUES)"
	@echo ""
	@echo "TANGO_DATABASE_DS=$(TANGO_DATABASE_DS)"
	@echo "ARCHIVER_DBNAME=$(ARCHIVER_DBNAME)"
	@echo ""
	@echo "MARK=$(MARK)"

namespace_sdp: KUBE_NAMESPACE := $(KUBE_NAMESPACE_SDP)
namespace_sdp: ## create the kubernetes namespace for SDP dynamic deployments
	@make namespace KUBE_NAMESPACE=$(KUBE_NAMESPACE)

delete-sdp-namespace: KUBE_NAMESPACE := $(KUBE_NAMESPACE_SDP)
delete-sdp-namespace: ## delete the kubernetes SDP namespace
	@make delete-namespace KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)

update-chart-versions:
	@which yq || (echo "yq not installed - you must 'pip3 install yq'"; exit 1;)
	for chart in $(SKAMPI_K8S_CHARTS); do \
		echo "update-chart-versions: inspecting charts/$$chart/Chart.yaml";  \
		for upd in $$(yq -r '.dependencies[].name' charts/$$chart/Chart.yaml); do \
			echo "update-chart-versions: finding latest version for $$upd"; \
			upd_version=$$(. $(K8S_SUPPORT) ; K8S_HELM_REPOSITORY=$(K8S_HELM_REPOSITORY) k8sChartVersion $$upd); \
			echo "update-chart-versions: updating $$upd to $$upd_version"; \
			sed -i.x -e "N;s/\(name: $$upd.*version:\).*/\1 $${upd_version}/;P;D" charts/$$chart/Chart.yaml; \
			rm -f charts/*/Chart.yaml.x; \
		done; \
	done



install: clean namespace namespace_sdp check-archiver-dbname install-chart## install the helm chart on the namespace KUBE_NAMESPACE

uninstall: uninstall-chart ## uninstall the helm chart on the namespace KUBE_NAMESPACE

reinstall-chart: uninstall install ## reinstall the  helm chart on the namespace KUBE_NAMESPACE

# upgrade-chart: ## upgrade the helm chart on the namespace KUBE_NAMESPACE
# 	@if [ "" == "$(HELM_REPO_NAME)" ]; then \
# 		echo "Installing Helm charts from current ref of git repository..."; \
# 		test "$(SKIP_HELM_DEPENDENCY_UPDATE)" == "1" || helm dependency update $(UMBRELLA_CHART_PATH); \
# 	else \
# 		echo "Deploying from artefact repository..."; \
# 		helm repo add $(HELM_REPO_NAME) $(CAR_HELM_REPOSITORY_URL); \
# 		helm search repo $(HELM_REPO_NAME) | grep DESCRIPTION; \
# 		helm search repo $(HELM_REPO_NAME) | grep $(UMBRELLA_CHART_PATH); \
# 	fi
# 	helm upgrade $(HELM_RELEASE) --install --wait \
# 		$(CHART_PARAMS) \
# 		--values $(VALUES) \
# 		$(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE);

# template-chart: clean ## template the helm chart on the namespace KUBE_NAMESPACE
# 	helm dependency update $(UMBRELLA_CHART_PATH); \
# 	helm template $(HELM_RELEASE) \
#         $(CHART_PARAMS) \
# 		--values $(VALUES) \
# 		$(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE);

install-or-upgrade: install-chart## install or upgrade the release

quotas: namespace## delete and create the kubernetes namespace with quotas
	kubectl -n $(KUBE_NAMESPACE) apply -f resources/namespace_with_quotas.yaml


upgrade-skampi-chart: ## upgrade the helm chart on the namespace KUBE_NAMESPACE
	@echo "THIS IS A SKAMPI SPECIFIC MAKE TARGET"
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

links: ## attempt to create the URLs with which to access
	@echo "############################################################################"
	@echo "#            Access the landing page here:"
	@echo "#            https://$(INGRESS_HOST)/$(KUBE_NAMESPACE)/start/"
	@echo "############################################################################"
