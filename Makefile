# THE FOLLOWING THREE VARIABLES MAY BE OBSOLETE BUT ARE NEEDED IF JIVE IS TO BE USED
THIS_HOST := $(shell (ip a 2> /dev/null || ifconfig) | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)##find IP addresses of this machine, setting THIS_HOST to the first address found
DISPLAY := $(THIS_HOST):0##for GUI applications
XAUTHORITYx ?= ${XAUTHORITY}##for GUI applications
PYTHON_LINE_LENGTH=99# As per ADR-70
VALUES ?= values.yaml# root level values files. This will override the chart values files.
SKIP_HELM_DEPENDENCY_UPDATE ?= 0# don't run "helm dependency update" on upgrade-skampi-chart

CLUSTER_DOMAIN ?= cluster.local## Domain used for naming Tango Device Servers
PYTHON_LINT_TARGET ?= tests/
INGRESS_HOST ?= k8s.stfc.skao.int## default ingress host
KUBE_NAMESPACE ?= integration#namespace to be used
KUBE_NAMESPACE_SDP ?= integration-sdp#namespace to be used
TANGO_DATABASE_DS ?= databaseds-tango-base## Stable name for the Tango DB
TANGO_HOST ?= $(TANGO_DATABASE_DS):10000
TANGO_SERVER_PORT ?= 45450## TANGO_SERVER_PORT - fixed listening port for local server
HELM_RELEASE ?= test## release name of the chart
MINIKUBE ?= true## Minikube or not
UMBRELLA_CHART_PATH ?= ./charts/$(DEPLOYMENT_CONFIGURATION)/##Path of the umbrella chart to install
CONFIG ?= $(error Please specify CONFIG=mid or CONFIG=low)## telescope - mid or low
K8S_CHART ?= ska-$(CONFIG)
DEPLOYMENT_CONFIGURATION ?= ska-$(CONFIG)## umbrella chart to work with
ITANGO_ENABLED ?= false## ITango enabled in ska-tango-base
TARANTA_USER ?= user1## the username for authentication to taranta services
TARANTA_PASSWORD ?= abc123## the password for authentication to taranta services
TARANTA_PASSPORT = $(TARANTA_PASSWORD)## required for ska-ser-skallop
MINIKUBE_RC := $(shell minikube ip 1>/dev/null 2> /dev/null; echo $$?)
ifeq ($(MINIKUBE_RC),0)
MINIKUBE_IP = $(shell minikube ip)
endif
LOADBALANCER_IP ?= $(MINIKUBE_IP)## The IP address of the Kubernetes Ingress Controller (LB)
TARANTA_AUTH_DASHBOARD_ENABLE ?= false## Enable auth and dashboard components for Taranta (Minikube only)
KUBE_HOST ?= $(LOADBALANCER_IP)## Required by Skallop
DOMAIN ?= branch## Required by Skallop
TEL ?= $(CONFIG)## Required by Skallop
KUBE_BRANCH ?= local## Required by Skallop
NAME ?= $(CONFIG)## The name of the telescope
ADDMARKS ?=## Additional Marks to add to pytests
# Dishmark is a synthesis of marks to add to test, it will always start with the tests for the appropriate
# telescope (e.g. TEL=mid or TEL=low) thereafter followed by additional filters
ifneq ($(ADDMARKS),)
DASHMARK ?= ska$(CONFIG) and $(ADDMARKS)
else
DASHMARK ?= ska$(CONFIG)
endif

ARCHWIZARD_VIEW_DBNAME = SKA_ARCHIVER
CONFIG_MANAGER= $(CONFIG)-eda/cm/01
ATTR_CONFIG_FILE = attribute_config_$(CONFIG).yaml
ARCHWIZARD_CONFIG?= $(ARCHWIZARD_VIEW_DBNAME)=tango://$(TANGO_DATABASE_DS).$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN):10000/$(CONFIG_MANAGER)

TESTCOUNT ?= ## Number of times test should run for non-k8s-test jobs
ifneq ($(TESTCOUNT),)
# Dashcount is a synthesis of testcount as input user variable and is used to
# run a paricular test/s multiple times. If no testcount is set then the entire
# --count option is removed
DASHCOUNT ?= --count=$(TESTCOUNT)
else
DASHCOUNT ?=
COUNT ?= 1
endif
PYTHON_VARS_AFTER_PYTEST ?= -m "$(DASHMARK)" $(DASHCOUNT) --no-cov -v -r fEx## use to setup a particular pytest session
CLUSTER_TEST_NAMESPACE ?= default## The Namespace used by the Infra cluster tests

# Some environments need HTTP(s) requests to go through a proxy server. If http_proxy
# is present we assume all proxy vars are set and pass them through. See
# https://about.gitlab.com/blog/2021/01/27/we-need-to-talk-no-proxy/ for some
# background reading about these variables.
ifneq ($(http_proxy),)
NO_PROXY ?= landingpage,oet-rest-$(HELM_RELEASE),.svc.$(CLUSTER_DOMAIN),${NO_PROXY}
no_proxy ?= landingpage,oet-rest-$(HELM_RELEASE),.svc.$(CLUSTER_DOMAIN),${no_proxy}

PROXY_VALUES = \
		--env=HTTP_PROXY=${HTTP_PROXY} \
		--env=HTTPS_PROXY=${HTTPS_PROXY} \
		--env=NO_PROXY=${NO_PROXY} \
		--env=http_proxy=${http_proxy} \
		--env=https_proxy=${https_proxy} \
		--env=no_proxy=${no_proxy} \

SDP_PROXY_VARS = --set ska-sdp.proxy.server=${http_proxy} \
	--set "ska-sdp.proxy.noproxy={${no_proxy}}"
endif

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
	--set global.exposeAllDS=$(EXPOSE_All_DS) \
	--set ska-tango-archiver.archwizard_config=$(ARCHWIZARD_CONFIG) \
	--set ska-sdp.ska-sdp-qa.zookeeper.clusterDomain=$(CLUSTER_DOMAIN) \
	--set ska-sdp.ska-sdp-qa.kafka.clusterDomain=$(CLUSTER_DOMAIN) \
	--set ska-sdp.ska-sdp-qa.redis.clusterDomain=$(CLUSTER_DOMAIN) \
	$(SDP_PROXY_VARS) \
	$(K8S_EXTRA_PARMS)

K8S_CHART ?= ska-$(CONFIG)##Default chart
SKAMPI_K8S_CHARTS ?= ska-mid ska-low ska-landingpage

HELM_CHARTS_TO_PUBLISH = $(SKAMPI_K8S_CHARTS)

OCI_IMAGES_TO_PUBLISH =

# KUBE_APP is set to the ska-tango-images base chart value
SKAMPI_KUBE_APP ?= skampi
KUBE_APP = ska-tango-images

CI_JOB_ID ?= local##local default for ci job id
#
# K8S_TEST_IMAGE_TO_TEST defines the tag of the Docker image to test
K8S_TEST_IMAGE_TO_TEST ?= artefact.skao.int/ska-ser-skallop:2.19.6## docker image that will be run for testing purpose

# import your personal semi-static config
-include PrivateRules.mak

# add `--values <file>` for each space-separated file in VALUES that exists
ifneq (,$(wildcard $(VALUES)))
	K8S_CHART_PARAMS += $(foreach f,$(wildcard $(VALUES)),--values $(f))
endif

# overwrite values.yaml for OET ingress if OET_INGRESS_ENABLED is defined
ifdef OET_INGRESS_ENABLED
	K8S_CHART_PARAMS += --set ska-oso-oet.rest.ingress.enabled=$(OET_INGRESS_ENABLED)
endif

ifdef ODA_DEPLOYMENT_ENABLED
	K8S_CHART_PARAMS += --set ska-db-oda.enabled=true \
	  --set ska-oso-oet.rest.oda.url=$(ODA_URI) \
	  --set ska-db-oda.rest.backend.type=filesystem \
	  --set ska-db-oda.pgadmin4.enabled=false \
	  --set ska-db-oda.postgresql.enabled=false
endif

ifeq ($(strip $(MINIKUBE)),true)
ifeq ($(strip $(TARANTA_AUTH_DASHBOARD_ENABLE)),true)
K8S_CHART_PARAMS += --set ska-taranta.enabled=true \
										--set ska-taranta.tangogql.replicas=1 \
										--set global.taranta_auth_enabled=true \
										--set global.taranta_dashboard_enabled=true
else
K8S_CHART_PARAMS += --set ska-taranta.enabled=false
DISABLE_TARANTA = and not taranta
endif
else
K8S_CHART_PARAMS += --set ska-taranta.enabled=true
ifeq ($(strip $(TARANTA_AUTH_DASHBOARD_ENABLE)),true)
K8S_CHART_PARAMS += --set global.taranta_auth_enabled=true \
										--set global.taranta_dashboard_enabled=true
endif
endif

# Test runner - run to completion job in K8s
K8S_TEST_RUNNER = test-runner-$(CI_JOB_ID)##name of the pod running the k8s_tests
#
# defines a function to copy the ./test-harness directory into the K8s K8S_TEST_RUNNER
# and then runs the requested make target in the container.
# capture the output of the test in a build folder inside the container
#
BIGGER_THAN ?= ## k8s-get-size-images parameter: if not empty check if images are bigger than this (in MB)

CONFIG_CASED = $(shell echo $(CONFIG) | sed -e "s/\b\(.\)/\u\1/g")
TELESCOPE = 'SKA-$(CONFIG_CASED)'
CENTRALNODE = 'ska_$(CONFIG)/tm_central/central_node'
SUBARRAY = 'ska_$(CONFIG)/tm_subarray_node'

# Makefile target for test in ./tests/Makefile
K8S_TEST_TARGET = test

# arguments to pass to make in the test runner container
K8S_TEST_MAKE_PARAMS = \
	SKUID_URL=ska-ser-skuid-$(HELM_RELEASE)-svc.$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN):9870 \
	KUBE_NAMESPACE=$(KUBE_NAMESPACE) \
	HELM_RELEASE=$(HELM_RELEASE) \
	CI_JOB_TOKEN=$(CI_JOB_TOKEN) \
	MARK='$(MARK)' \
	COUNT=$(COUNT) \
	FILE='$(FILE)' \
	SKA_TELESCOPE=$(TELESCOPE) \
	CENTRALNODE_FQDN=$(CENTRALNODE) \
	SUBARRAYNODE_FQDN_PREFIX=$(SUBARRAY) \
	JIRA_AUTH=$(JIRA_AUTH) \
	CAR_RAW_USERNAME=$(RAW_USER) \
	CAR_RAW_PASSWORD=$(RAW_PASS) \
	CAR_RAW_REPOSITORY_URL=$(RAW_HOST) \
	TARANTA_USER=$(TARANTA_USER) \
	TARANTA_PASSWORD=$(TARANTA_PASSWORD) \
	TARANTA_PASSPORT=$(TARANTA_PASSPORT) \
	KUBE_HOST=$(KUBE_HOST) \
	TANGO_HOST=$(TANGO_DATABASE_DS).$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN):10000 \
	DISABLE_MAINTAIN_ON='$(DISABLE_MAINTAIN_ON)' \
	TEST_ENV='$(TEST_ENV)' \
	DEBUG_ENTRYPOINT=$(DEBUG_ENTRYPOINT) \
	LIVE_LOGGING=$(LIVE_LOGGING) \
	LIVE_LOGGING_EXTENDED=$(LIVE_LOGGING_EXTENDED) \
	REPLAY_EVENTS_AFTERWARDS=$(REPLAY_EVENTS_AFTERWARDS) \
	CAPTURE_LOGS=$(CAPTURE_LOGS)



# runs inside the test runner container after cd ./tests
K8S_RUN_TEST_FOLDER = ./tests
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
-include resources/archiver.mk

k8s_test_command = /bin/bash -o pipefail -c "\
	mkfifo results-pipe && tar zx --warning=all && \
        ( if [[ -f pyproject.toml ]]; then poetry export --format requirements.txt --output poetry-requirements.txt --without-hashes --dev; echo 'k8s-test: installing poetry-requirements.txt';  pip install -qUr poetry-requirements.txt; cd $(k8s_test_folder); else if [[ -f $(k8s_test_folder)/requirements.txt ]]; then echo 'k8s-test: installing $(k8s_test_folder)/requirements.txt'; pip install -qUr $(k8s_test_folder)/requirements.txt; fi; fi ) && \
				 cd $(k8s_test_folder) && \
		export PYTHONPATH=${PYTHONPATH}:/app/src$(k8s_test_src_dirs) && \
		mkdir -p build && \
	( \
	$(K8S_TEST_TEST_COMMAND) \
	); \
	echo \$$? > build/status; pip list > build/pip_list.txt; \
	echo \"k8s_test_command: test command exit is: \$$(cat build/status)\"; \
	tar zcf ../results-pipe build;"

# use hook to create SDP namespace
k8s-pre-install-chart:
	@echo "k8s-pre-install-chart: creating the SDP namespace $(KUBE_NAMESPACE_SDP)"
	@make namespace-sdp KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)

# use hook to create SDP namespace
k8s-pre-install-chart-car:
	@echo "k8s-pre-install-chart-car: creating the SDP namespace $(KUBE_NAMESPACE_SDP)"
	@make namespace-sdp KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)

# use hook to delete SDP namespace
k8s-post-uninstall-chart:
	@echo "k8s-post-uninstall-chart: deleting the SDP namespace $(KUBE_NAMESPACE_SDP)"
	@make delete-sdp-namespace KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)

# make sure infra test do not run in k8s-test
k8s-test: MARK := not infra and $(DASHMARK) $(DISABLE_TARANTA)

k8s-test-runner: MARK := not infra and $(DASHMARK) $(DISABLE_TARANTA)

k8s-post-test: # post test hook for processing received reports
	@if ! [[ -f build/status ]]; then \
		echo "k8s-post-test: something went very wrong with the test container (no build/status file) - ABORTING!"; \
		exit 1; \
	fi;
	@[[ $$(cat build/status) == 0 ]] || KUBE_NAMESPACE=$(KUBE_NAMESPACE) source scripts/were_pods_throttled.sh;

foo:
	@echo $(CASED_CONFIG)