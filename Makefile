# THE FOLLOWING THREE VARIABLES MAY BE OBSOLETE BUT ARE NEEDED IF JIVE IS TO BE USED
THIS_HOST := $(shell (ip a 2> /dev/null || ifconfig) | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)##find IP addresses of this machine, setting THIS_HOST to the first address found
DISPLAY := $(THIS_HOST):0##for GUI applications
XAUTHORITYx ?= ${XAUTHORITY}##for GUI applications

VALUES ?= values.yaml# root level values files. This will override the chart values files.
SKIP_HELM_DEPENDENCY_UPDATE ?= 0# don't run "helm dependency update" on upgrade-skampi-chart

INGRESS_HOST ?= k8s.stfc.skao.int## default ingress host
KUBE_NAMESPACE ?= integration#namespace to be used
KUBE_NAMESPACE_SDP ?= integration-sdp#namespace to be used
TANGO_DATABASE_DS ?= databaseds-tango-base## Stable name for the Tango DB
TANGO_HOST ?= $(TANGO_DATABASE_DS):10000
TANGO_SERVER_PORT ?= 45450## TANGO_SERVER_PORT - fixed listening port for local server
HELM_RELEASE ?= test## release name of the chart
DEPLOYMENT_CONFIGURATION ?= ska-mid## umbrella chart to work with
MINIKUBE ?= true## Minikube or not
UMBRELLA_CHART_PATH ?= ./charts/$(DEPLOYMENT_CONFIGURATION)/##Path of the umbrella chart to install
CHARTS ?= ska-mid
ITANGO_ENABLED ?= false## ITango enabled in ska-tango-base
WEBJIVE_USER ?= user1## the username for authentication to taranta services
WEBJIVE_PASSWORD ?= abc123## the password for authentication to taranta services
WEBJIVE_PASSPORT = $(WEBJIVE_PASSWORD)# required for ska-ser-skallop
MINIKUBE_RC := $(shell minikube ip 1>/dev/null 2> /dev/null; echo $$?)
ifeq ($(MINIKUBE_RC),0)
MINIKUBE_IP = $(shell minikube ip)
endif
LOADBALANCER_IP ?= $(MINIKUBE_IP) ## The IP address of the Kubernetes Ingress Controller (LB)
WEBJIVE_AUTH_DASHBOARD_ENABLE ?= true## Enable auth and dashboard components for Taranta (Minikube only)
KUBE_HOST ?= $(LOADBALANCER_IP)

CLUSTER_TEST_NAMESPACE ?= default## The Namespace used by the Infra cluster tests
CLUSTER_DOMAIN ?= cluster.local## Domain used for naming Tango Device Servers

# these are the global overrides that get passed into the ska-mid/low deployments

K8S_CHART_PARAMS = --set ska-tango-base.xauthority="$(XAUTHORITYx)" \
	--set global.minikube=$(MINIKUBE) \
	--set global.tango_host=$(TANGO_DATABASE_DS):10000 \
	--set global.cluster_domain=$(CLUSTER_DOMAIN) \
	--set global.device_server_port=$(TANGO_SERVER_PORT) \
	--set ska-tango-base.itango.enabled=$(ITANGO_ENABLED) \
	--set ska-sdp.helmdeploy.namespace=$(KUBE_NAMESPACE_SDP) \
	--set ska-tango-archiver.hostname=$(ARCHIVER_HOST_NAME) \
	--set ska-tango-archiver.dbname=$(ARCHIVER_DBNAME) \
	--set ska-tango-archiver.port=$(ARCHIVER_PORT) \
	--set ska-tango-archiver.dbuser=$(ARCHIVER_DB_USER) \
	--set ska-tango-archiver.dbpassword=$(ARCHIVER_DB_PWD) \
	$(PSI_LOW_SDP_PROXY_VARS)

# add on values.yaml file if it exists
ifneq (,$(wildcard $(VALUES)))
	K8S_CHART_PARAMS += --values $(VALUES)
endif

ifeq ($(strip $(MINIKUBE)),true)
ifeq ($(strip $(WEBJIVE_AUTH_DASHBOARD_ENABLE)),true)
K8S_CHART_PARAMS += --set global.webjive_auth_enabled=true \
										--set global.webjive_dashboard_enabled=true
endif
endif

K8S_CHART ?= ska-mid##Default chart set to Mid for testing purposes
SKAMPI_K8S_CHARTS ?= ska-mid ska-low ska-landingpage

HELM_CHARTS_TO_PUBLISH = $(SKAMPI_K8S_CHARTS)

OCI_IMAGES_TO_PUBLISH =

# KUBE_APP is set to the ska-tango-images base chart value
SKAMPI_KUBE_APP ?= skampi
KUBE_APP = ska-tango-images

# PSI Low Environment need PROXY values to be set
# This code detects environment and sets the variables
ENV_CHECK := $(shell echo $(K8S_CHART) | egrep ska-low)
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

CI_JOB_ID ?= local##local default for ci job id
#
# K8S_TEST_IMAGE_TO_TEST defines the tag of the Docker image to test
K8S_TEST_IMAGE_TO_TEST ?= artefact.skao.int/ska-ser-skallop:2.7.10## docker image that will be run for testing purpose
# Test runner - run to completion job in K8s
K8S_TEST_RUNNER = test-runner-$(CI_JOB_ID)##name of the pod running the k8s_tests
#
# defines a function to copy the ./test-harness directory into the K8s K8S_TEST_RUNNER
# and then runs the requested make target in the container.
# capture the output of the test in a build folder inside the container
#
BIGGER_THAN ?= ## k8s-get-size-images parameter: if not empty check if images are bigger than this (in MB)

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

# Makefile target for test in ./tests/Makefile
K8S_TEST_TARGET = test

# arguments to pass to make in the test runner container
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
	CAR_RAW_REPOSITORY_URL=$(RAW_HOST) \
	WEBJIVE_USER=$(WEBJIVE_USER) \
	WEBJIVE_PASSWORD=$(WEBJIVE_PASSWORD) \
	WEBJIVE_PASSPORT=$(WEBJIVE_PASSPORT) \
	KUBE_HOST=$(KUBE_HOST)

# runs inside the test runner container after cd ./tests
K8S_TEST_TEST_COMMAND = make -s \
			$(K8S_TEST_MAKE_PARAMS) \
			$(K8S_TEST_TARGET)

.DEFAULT_GOAL := help

.PHONY: help

# include makefile targets for interrim image building
-include .make/oci.mk

# include makefile targets for Kubernetes management
-include .make/k8s.mk

# include makefile targets for helm linting
-include .make/helm.mk

# include makefile targets for python
-include .make/python.mk

# include core makefile targets
-include .make/base.mk

# include convenience and legacy make targets
-include resources/localhelpers.mk

# include Skampi extension make targets
-include resources/skampi.mk

python-pre-test: # must pass the current kubeconfig into the test container for infra tests
	pip3 install -r tests/requirements.txt

k8s-pre-test: python-pre-test

# make sure infra test do not run in k8s-test
k8s-test: MARK := not infra

k8s-post-test: # post test hook for processing received reports
	@if ! [[ -f build/status ]]; then \
		echo "k8s-post-test: something went very wrong with the test container (no build/status file) - ABORTING!"; \
		exit 1; \
	fi
	@echo "k8s-post-test: Skampi post processing of core Skampi test reports with scripts/collect_k8s_logs.py"
	@python3 scripts/collect_k8s_logs.py $(KUBE_NAMESPACE) $(KUBE_NAMESPACE_SDP) \
		--pp build/k8s_pretty.txt --dump build/k8s_dump.txt --tests build/k8s_tests.txt
