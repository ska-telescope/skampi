.DEFAULT_GOAL := help
.PHONY: help

-include .make/base.mk

PYTHON_LINE_LENGTH = 99
PYTHON_LINT_TARGET = tests/

MINIKUBE ?= false
LOADBALANCER_IP ?= 10.100.20.1  # stfc-techops ingress lb
ifeq ($(strip $(MINIKUBE)),true)
LOADBALANCER_IP = $(shell minikube ip)
endif

CLUSTER_DOMAIN ?= cluster.local
KUBE_NAMESPACE ?= integration
KUBE_NAMESPACE_SDP ?= $(KUBE_NAMESPACE)-sdp
HELM_RELEASE ?= test
KUBE_HOST ?= $(LOADBALANCER_IP)

XRAY_UPLOAD_ENABLED ?= true
ALLOWED_CONFIGS ?= mid low
CONFIG ?=
TEST_EXEC_FILE_PATH?=tests/test-exec-$(CONFIG).json

# Run only for k8s targets
ifneq ($(findstring k8s-,$(firstword $(MAKECMDGOALS))),)
ifneq ($(strip $(MINIKUBE)),true)
HELM_RELEASE = $(shell helm list -n $(KUBE_NAMESPACE) 2>/dev/null | grep ska-$(CONFIG) | awk '{print $$1}')
$(info Detected Helm release in namespace '$(KUBE_NAMESPACE)': '$(HELM_RELEASE)')
endif

ifeq ($(filter $(CONFIG),mid low),)
$(error `CONFIG` must be one of $(ALLOWED_CONFIGS))
endif

ifeq ($(strip $(KUBE_NAMESPACE)),)
$(error `KUBE_NAMESPACE` must be provided)
endif

ifeq ($(strip $(HELM_RELEASE)),)
$(error `HELM_RELEASE` must be provided)
endif

endif

TANGO_DATABASE_DS ?= databaseds-tango-base
TANGO_HOST ?= $(TANGO_DATABASE_DS).$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN):10000
TARANTA_ENABLED ?= true
ifeq ($(strip $(MINIKUBE)),true)
TARANTA_ENABLED ?= false
endif

# Skallop library variables
CONFIG_CASED = $(shell echo $(CONFIG) | sed -e "s/\b\(.\)/\u\1/g")
SKA_TELESCOPE = 'SKA-$(CONFIG_CASED)'
CENTRALNODE_FQDN = 'ska_$(CONFIG)/tm_central/central_node'
SUBARRAY_FQDN_PREFIX = 'ska_$(CONFIG)/tm_subarray_node'
TARANTA_USER ?= user1
TARANTA_PASSWORD ?= abc123
JIRA_AUTH ?=
JIRA_USERNAME ?=
JIRA_PASSWORD ?=
CAR_RAW_USERNAME ?=
CAR_RAW_PASSWORD ?=
CAR_RAW_REPOSITORY_URL ?=
DOMAIN ?= branch
ifdef CI_COMMIT_REF_NAME
	GIT_BRANCH = $(CI_COMMIT_REF_NAME)
else
	GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)
endif
SANITIZED_GIT_BRANCH=$(shell echo $(GIT_BRANCH) | tr '-' '_'| tr '.' '_')
KUBE_BRANCH = $(GIT_BRANCH)
KUBE_APP ?= ska-skampi

# Skallop flags
SKALLOP_LOG_FILTER_ERRORS ?= true
DISABLE_MAINTAIN_ON ?= true
USE_OLD_DISH_IDS ?= true
USE_ONLY_POLLING ?= false
DEBUG_WAIT ?= false
USE_POD_KUBECONFIG ?= false
MOCK_SUT ?= false
CHECK_INFRA_PER_TEST ?= false
CHECK_INFRA_PER_SESSION ?= false
# This flags need to be added when set to true because the Python expression
# they are used in do not check the value, but if it is defined
SKALLOP_FLAGS ?= SKALLOP_LOG_FILTER_ERRORS DISABLE_MAINTAIN_ON USE_OLD_DISH_IDS USE_ONLY_POLLING DEBUG_WAIT \
USE_POD_KUBECONFIG MOCK_SUT CHECK_INFRA_PER_TEST CHECK_INFRA_PER_SESSION
# The spaces around SKALLOP_FLAGS are intentional
SKALLOP_SET_FLAGS := $(foreach var," $(SKALLOP_FLAGS) ", $(if $(filter $($(var)),true), $(var)=$($(var))))

# Tests variables
SDP_DATA_PVC_NAME ?= shared
ARCHIVER_DBNAME ?= $(shell echo ${CONFIG}_archiver_db_$(SANITIZED_GIT_BRANCH) | cut -c -50)
ARCHIVER_DB_USER ?=
ARCHIVER_PWD ?=
ARCHIVER_PORT ?=
TEST_ENV ?= BUILD_IN

# Tests flags
DEBUG_ENTRYPOINT ?= true
SHOW_STEP_FUNCTIONS ?= true
ATTR_SYNCH_ENABLED ?= true
ATTR_SYNCH_ENABLED_GLOBALLY ?= true
LIVE_LOGGING_EXTENDED ?= true
LIVE_LOGGING ?= true
REPLAY_EVENTS_AFTERWARDS ?= false
CAPTURE_LOGS ?= true
DEVENV ?= false

# Pytest variables
PYTHON_VARS_AFTER_PYTEST ?=## Aruguments for pytest
PYTEST_MARK ?=## Add custom mark expression
PYTEST_COUNT ?=## Number of times test should run
MARKS = not infra and ska$(CONFIG)
ifneq ($(PYTEST_MARK),)
MARKS += and $(PYTEST_MARK)
endif

ifneq ($(strip $(TARANTA_ENABLED)),true)
MARKS += and not taranta
endif

PYTHON_VARS_AFTER_PYTEST += -m "$(MARKS)"

ifneq ($(PYTEST_COUNT),)
PYTHON_VARS_AFTER_PYTEST += --count=$(PYTEST_COUNT)
endif

PYTHON_VARS_AFTER_PYTEST += -v -r fEx --disable-pytest-warnings --repeat-scope session

CI_JOB_TOKEN ?=
CI_JOB_ID ?= local##local default for ci job id
SKALLOP_VERSION ?= 2.24.2
K8S_TEST_IMAGE_TO_TEST ?= artefact.skao.int/ska-ser-skallop:$(SKALLOP_VERSION)
K8S_TEST_RUNNER = test-runner-$(CI_JOB_ID)



PYTHON_VARS_BEFORE_PYTEST ?= \
	KUBE_HOST=$(KUBE_HOST) \
	KUBE_APP=$(KUBE_APP) \
	KUBE_NAMESPACE=$(KUBE_NAMESPACE) \
	KUBE_NAMESPACE_SDP=$(KUBE_NAMESPACE_SDP) \
	TANGO_HOST=$(TANGO_HOST) \
	\
	TEL=$(CONFIG) \
	SKA_TELESCOPE=$(SKA_TELESCOPE) \
	CENTRALNODE_FQDN=$(CENTRALNODE_FQDN) \
	SUBARRAY_FQDN_PREFIX=$(SUBARRAY_FQDN_PREFIX) \
	TARANTA_USER=$(TARANTA_USER) \
	TARANTA_PASSWORD=$(TARANTA_PASSWORD) \
	JIRA_AUTH=$(JIRA_AUTH) \
	CAR_RAW_USERNAME=$(CAR_RAW_USERNAME) \
	CAR_RAW_PASSWORD=$(CAR_RAW_PASSWORD) \
	CAR_RAW_REPOSITORY_URL=$(CAR_RAW_REPOSITORY_URL) \
	DOMAIN=$(DOMAIN) \
	KUBE_BRANCH=$(KUBE_BRANCH) \
	$(SKALLOP_SET_FLAGS) \
	\
	SDP_DATA_PVC_NAME=$(SDP_DATA_PVC_NAME) \
	LOADBALANCER_IP=$(LOADBALANCER_IP) \
	ARCHIVER_DBNAME=$(ARCHIVER_DBNAME) \
	ARCHIVER_DB_USER=$(ARCHIVER_DB_USER) \
	ARCHIVER_PWD=$(ARCHIVER_PWD) \
	ARCHIVER_PORT=$(ARCHIVER_PORT) \
	TEST_ENV=$(TEST_ENV) \
	DEBUG_ENTRYPOINT=$(DEBUG_ENTRYPOINT) \
	CHECK_INFRA_PER_TEST=$(CHECK_INFRA_PER_TEST) \
	SHOW_STEP_FUNCTIONS=$(SHOW_STEP_FUNCTIONS) \
	ATTR_SYNCH_ENABLED=$(ATTR_SYNCH_ENABLED) \
	ATTR_SYNCH_ENABLED_GLOBALLY=$(ATTR_SYNCH_ENABLED_GLOBALLY) \
	LIVE_LOGGING_EXTENDED=$(LIVE_LOGGING_EXTENDED) \
	LIVE_LOGGING=$(LIVE_LOGGING) \
	REPLAY_EVENTS_AFTERWARDS=$(REPLAY_EVENTS_AFTERWARDS) \
	CAPTURE_LOGS=$(CAPTURE_LOGS) \
	DEVENV=$(DEVENV)

-include .make/python.mk
-include .make/k8s.mk

-include PrivateRules.mak

k8s-pre-test:
	$(info Running SKAMPI tests)
	$(info ** CONFIG=$(CONFIG))
	$(info ** KUBE_NAMESPACE=$(KUBE_NAMESPACE))
	$(info ** HELM_RELEASE=$(HELM_RELEASE))
	$(info ** MARKS=$(MARKS))
	$(info )

k8s-post-test: # post test hook for processing received reports
	@if ! [[ -f build/status ]]; then \
		echo "k8s-post-test: something went very wrong with the test container (no build/status file) - ABORTING!"; \
		exit 1; \
	fi;
	@KUBE_NAMESPACE=$(KUBE_NAMESPACE) source scripts/check_pod_throttling.sh;
	@\
	if [ "$(XRAY_UPLOAD_ENABLED)" = "true" ]; then \
		echo "Processing XRay uploads using $(TEST_EXEC_FILE_PATH)"; \
		for cuke in build/cucumber*.json; do \
			echo "Processing XRay upload of: $$cuke"; \
			if [[ -z "${JIRA_USERNAME}" ]]; then \
				/usr/local/bin/xtp-xray-upload -f $$cuke -i $(TEST_EXEC_FILE_PATH) -v; \
			else \
				echo "Using Jira Username and Password for auth"; \
				xtp-xray-upload -f $$cuke -i $(TEST_EXEC_FILE_PATH) -v -u ${JIRA_USERNAME} -p ${JIRA_PASSWORD}; \
			fi; \
		done; \
	fi

itango:
	@echo "## Connecting to TANGO at '$(TANGO_HOST)'"
	@TANGO_HOST=$(TANGO_HOST) itango3