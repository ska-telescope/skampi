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
KUBE_APP ?= ska-skampi

ifdef CI_COMMIT_REF_NAME
	GIT_BRANCH = $(CI_COMMIT_REF_NAME)
else
	GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)
endif
ifdef CI_COMMIT_REF_SLUG
	GIT_BRANCH_SLUG = $(CI_COMMIT_REF_SLUG)
else
	GIT_BRANCH_SLUG = $(shell echo $(GIT_BRANCH) | tr '[:upper:]' '[:lower:]' | tr '-' '_'| tr '.' '_')
endif

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
ARCHIVER_DBNAME ?= $(shell echo $(CONFIG)_archiver_db_$(GIT_BRANCH_SLUG) | head -c 59)
# Sanitize ARCHIVER_DBNAME: Postgres DB name maxes at 59 chars
ARCHIVER_DBNAME := $(shell echo $(ARCHIVER_DBNAME) | tr '-' '_'| tr '.' '_' | head -c 59)
ARCHIVER_PORT ?= 5432
ARCHIVER_DB_USER ?= admin
ARCHIVER_PWD ?=
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
PYTHONPATH ?= .:./tests:./tests/resources:./tests/integration:./tests/resources/models/csp_model

# Pytest variables
PYTHON_VARS_AFTER_PYTEST ?=## Aruguments for pytest
PYTEST_MARK ?= not infra and ska$(CONFIG) ## pytest mark for the full telescope test set
PYTEST_SUBSYS_MARK ?=## Add custom mark expression to select subsystem tests from the whole
PYTEST_COUNT ?= 1## Number of times test should run

ifneq ($(PYTEST_SUBSYS_MARK),)
PYTEST_MARK += and $(PYTEST_SUBSYS_MARK)
endif

ifneq ($(strip $(TARANTA_ENABLED)),true)
PYTEST_MARK += and not taranta
endif

PYTHON_VARS_AFTER_PYTEST += -m "$(PYTEST_MARK)"

ifneq ($(PYTEST_COUNT),)
PYTHON_VARS_AFTER_PYTEST += --count=$(PYTEST_COUNT)
endif

PYTHON_VARS_AFTER_PYTEST += -v -r fEx --disable-pytest-warnings --repeat-scope session

CI_JOB_TOKEN ?=
CI_JOB_ID ?= local##local default for ci job id
SKALLOP_VERSION ?= 2.24.2
K8S_TEST_IMAGE_TO_TEST ?= artefact.skao.int/ska-ser-skallop:$(SKALLOP_VERSION)
K8S_TEST_RUNNER = test-runner-$(CI_JOB_ID)

SECRET_VARS = TARANTA_PASSWORD JIRA_AUTH JIRA_PASSWORD CAR_RAW_PASSWORD ARCHIVER_PWD

PYTHON_VARS_BEFORE_PYTEST ?= \
	KUBE_HOST=$(KUBE_HOST) \
	KUBE_APP=$(KUBE_APP) \
	KUBE_NAMESPACE=$(KUBE_NAMESPACE) \
	KUBE_NAMESPACE_SDP=$(KUBE_NAMESPACE_SDP) \
	TANGO_HOST=$(TANGO_HOST) \
	TEL=$(CONFIG) \
	SKA_TELESCOPE=$(SKA_TELESCOPE) \
	CENTRALNODE_FQDN=$(CENTRALNODE_FQDN) \
	SUBARRAY_FQDN_PREFIX=$(SUBARRAY_FQDN_PREFIX) \
	TARANTA_USER=$(TARANTA_USER) \
	TARANTA_PASSWORD=$(TARANTA_PASSWORD) \
	JIRA_AUTH=$(JIRA_AUTH) \
	JIRA_USERNAME=$(JIRA_USERNAME) \
	JIRA_PASSWORD=$(JIRA_PASSWORD) \
	CAR_RAW_USERNAME=$(CAR_RAW_USERNAME) \
	CAR_RAW_PASSWORD=$(CAR_RAW_PASSWORD) \
	CAR_RAW_REPOSITORY_URL=$(CAR_RAW_REPOSITORY_URL) \
	DOMAIN=$(DOMAIN) \
	KUBE_BRANCH=$(KUBE_BRANCH) \
	$(SKALLOP_SET_FLAGS) \
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

VARS := \
	$(foreach pair,$(shell echo $(PYTHON_VARS_BEFORE_PYTEST)),\
		$(eval key_value := $(subst =, ,$(pair)))\
		$(eval key := $(word 1,$(key_value)))\
		$(eval value := $(word 2,$(key_value)))\
		$(if $(filter $(key),$(SECRET_VARS)),\
			$(if $(value),\
				VAR_$(key)=***,\
				VAR_$(key)=\
			),\
			VAR_$(key)=$(value)\
		)\
	)

-include .make/python.mk
-include .make/k8s.mk

-include PrivateRules.mak

vars:
	$(info ##### SKAMPI test vars)
	@echo "$(VARS)" | sed "s#VAR_#\n#g"

k8s-pre-test:
	$(info ##### Running SKAMPI tests)
	$(info ** CONFIG=$(CONFIG))
	$(info ** KUBE_NAMESPACE=$(KUBE_NAMESPACE))
	$(info ** HELM_RELEASE=$(HELM_RELEASE))
	$(info ** PYTEST_MARK=$(PYTEST_MARK))
	$(info )

check-pod-throttling:  # check if pods in a namespace have been throttled
	@echo "Check throttling information at the following link:"; \
	echo "https://k8s.stfc.skao.int/grafana/d/6581e46e4e5c7ba40a07646395ef7b23/kubernetes-compute-resources-pod?orgId=1&refresh=10s&var-datasource=default&var-cluster=stfc-ska-monitor&var-namespace=$(KUBE_NAMESPACE)&var-pod=databaseds-tangodb-databaseds-tango-base-0&from=now-1h&to=now"


# Note that in tests/test-exec-*.json files the chart_info field is changed to
# auto generated dependency information from runtime configuration (builds/chart_config.yaml)
# instead of the local repo chart file (charts/ska-mid|low/Chart.yaml)
# This is a hack at best to keep the same functionality without breaking skallop or
# requiring extra work. This is expected to change in future once 
# more requirements regarding config management is known
upload-test-results: extract-chart-config## uploads tests results
	@if ! [[ -f build/status ]]; then \
		echo "k8s-post-test: something went very wrong with the test container (no build/status file) - ABORTING!"; \
		exit 1; \
	fi;
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

k8s-post-test: check-pod-throttling upload-test-results

itango:
	@echo "## Connecting to TANGO at '$(TANGO_HOST)'"
	@TANGO_HOST=$(TANGO_HOST) itango3

python-do-lint:
	@mkdir -p build/reports;
	PYTHONPATH=$(PYTHONPATH) $(PYTHON_RUNNER) isort --check-only --profile black --line-length $(PYTHON_LINE_LENGTH) $(PYTHON_SWITCHES_FOR_ISORT) $(PYTHON_LINT_TARGET)
	PYTHONPATH=$(PYTHONPATH) $(PYTHON_RUNNER) black --exclude .+\.ipynb --check --line-length $(PYTHON_LINE_LENGTH) $(PYTHON_SWITCHES_FOR_BLACK) $(PYTHON_LINT_TARGET)
	PYTHONPATH=$(PYTHONPATH) $(PYTHON_RUNNER) flake8 --show-source --statistics --max-line-length $(PYTHON_LINE_LENGTH) $(PYTHON_SWITCHES_FOR_FLAKE8) $(PYTHON_LINT_TARGET)
	PYTHONPATH=$(PYTHONPATH) $(PYTHON_RUNNER) pylint --output-format=parseable,parseable:build/code_analysis.stdout,pylint_junit.JUnitReporter:build/reports/linting-python.xml --max-line-length $(PYTHON_LINE_LENGTH) $(PYTHON_SWITCHES_FOR_PYLINT) $(PYTHON_LINT_TARGET)
	@make --no-print-directory join-lint-reports

extract-chart-config:
	@echo "Deleting existing config exporters..."
	@helm uninstall -n $(KUBE_NAMESPACE) ska-config-exporter && kubectl -n $(KUBE_NAMESPACE) delete --ignore-not-found pod/ska-config-export
	@echo "Installing config exporter from artefact.skao.int/ska-config-exporter:0.0.3..."
	@echo " This is needed to define the access roles"
	@helm repo add skatelescope $(CAR_HELM_REPOSITORY_URL) && helm repo update
	@helm install -n $(KUBE_NAMESPACE) ska-config-exporter skatelescope/ska-config-exporter:0.0.3 --set persistentService=false
	@echo "Exporting config into build/deploy_config.json"
	@kubectl run -q -n $(KUBE_NAMESPACE) --rm -i --tty --restart=Never --image "artefact.skao.int/ska-k8s-config-exporter:0.0.3" \
	--env TANGO_HOST=$(TANGO_HOST) --env NAMESPACE=$(KUBE_NAMESPACE) config-export -- ska-config-export -a '["versionId", "buildState"]' > deploy_config.json
	@echo "Extracting chart config into build/chart_info.yml"
	@cat build/deploy_config.json | jq -r '.helm | to_entries[1].value | { "apiVersion": "v2", "name": .chart_name, "description": "", "type": "application", "version": .chart_version, "appVersion": .app_version, "dependencies": .dependencies }' | yq -Pyo > build/chart_info.yml
	@echo "Done!"
.PHONY: extract-chart-config