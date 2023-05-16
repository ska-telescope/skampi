# include Makefile for Kubernetes related targets and variables

# PYTHON_SRC is usually defined in python.mk - define if not included
ifndef PYTHON_SRC
PYTHON_SRC ?= src
endif

K8S_INSTALL_CHART := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-k8s-install-chart

K8S_SUPPORT := $(shell dirname $(abspath $(lastword $(MAKEFILE_LIST))))/.make-k8s-support
BASE := $(shell pwd)
K8S_HELM_REPOSITORY ?= https://artefact.skao.int/repository/helm-internal

CAR_OCI_REGISTRY_HOST ?= artefact.skao.int

# Test runner - run to completion job in K8s
# If it's on pipeline add job id
ifeq ($(strip $(CI_JOB_ID)),)
	K8S_TEST_RUNNER ?= test-makefile-runner##name of the pod running the k8s-tests
else
	K8S_TEST_RUNNER ?= test-makefile-runner-$(CI_JOB_ID)##name of the pod running the k8s-tests
endif
K8S_TEST_RUNNER_ADD_ARGS ?= ## Additional arguments passed to the K8S test runner

# LINTING_OUTPUT=$(shell helm lint charts/* | grep ERROR -c | tail -1)
ifeq ($(strip $(PROJECT)),)
  NAME=$(shell basename $(CURDIR))
else
  NAME=$(PROJECT)
endif

HELM_RELEASE ?= test## Helm release
ifneq ($(strip $(CI_JOB_ID)),)
	KUBE_NAMESPACE ?= ci-$(CI_PROJECT_NAME)-$(CI_COMMIT_SHORT_SHA)## Kubernetes Namespace for pipelines
	K8S_TEST_IMAGE_TO_TEST ?= $(CI_REGISTRY_IMAGE)/$(NAME):$(VERSION)-dev.c$(CI_COMMIT_SHORT_SHA)
else
	KUBE_NAMESPACE ?= $(NAME)## Kubernetes Namespace
	K8S_TEST_IMAGE_TO_TEST ?= $(CAR_OCI_REGISTRY_HOST)/$(NAME):$(VERSION)## docker image that will be run for testing purpose
endif
K8S_CHART ?= $(NAME)## selected chart
K8S_CHARTS ?= $(K8S_CHART) ## list of charts
K8S_UMBRELLA_CHART_PATH ?= ./charts/$(K8S_CHART)/ ## path to umbrella chart used for testing
KUBE_APP ?= $(NAME)## Kubernetes app label name
K8S_TIMEOUT ?= 360s ## kubectl wait timeout - 6 minutes
K8S_CHART_PARAMS ?= ## Additional helm chart parameters
K8S_TEST_AUX_DIRS ?= ## Additional directories to transfer to the testpod
K8S_SKIP_NAMESPACE ?= false##Skips namespace related targets if set

MARK ?= all## this variable sets the mark parameter in the pytest
FILE ?= ##this variable sets the execution of a single file in the pytest
COUNT ?= 1## amount of repetition for pytest-repeat

# ST-1258: Define a variable that allows projects importing this module
# that override K8S_TEST_TEST_COMMAND to also define from which folder
# to run the K8S_TEST_TEST_COMMAND from.
K8S_RUN_TEST_FOLDER ?= ./

# NOTE: the command steps back a directory so as to be outside of ./tests
#  when k8s-test is running - this is to bring it into line with python-test
#  behaviour
K8S_TEST_TEST_COMMAND ?= $(PYTHON_VARS_BEFORE_PYTEST) $(PYTHON_RUNNER) \
						pytest \
						$(PYTHON_VARS_AFTER_PYTEST) ./tests \
						 | tee pytest.stdout ## k8s-test test command to run in container
# example alternative using a Makefile located in tests/
# K8S_TEST_TARGET ?= test ## Makefile target fore test in ./tests/Makefile
# K8S_TEST_MAKE_PARAMS ?= ## Parameters to pass into the make target inside k8s-test from ./tests/Makefile
# K8S_TEST_TEST_COMMAND ?= make -s \
# 			$(K8S_TEST_MAKE_PARAMS) \
# 			$(K8S_TEST_TARGET)

.PHONY: k8s-vars k8s-namespace k8s-delete-namespace k8s-clean k8s-dep-update k8s-install-chart k8s-template-chart k8s-uninstall-chart k8s-bounce k8s-reinstall-chart k8s-upgrade-chart k8s-wait k8s-watch k8s-describe k8s-podlogs k8s-smoke-test k8s-interactive

## TARGET: k8s-chart-version
## SYNOPSIS: make k8s-chart-version
## HOOKS: none
## VARS:
##       K8S_CHART=<Helm Chart to check> - default is project name (directory)
##       K8S_HELM_REPOSITORY=<Helm Chart repository> - default is https://artefact.skao.int/repository/helm-internal
##
##  Shows the latest version of K8S_CHART in K8S_HELM_REPOSITORY, by default project chart version in Central Artefact Repository. Do not confuse this with the current local version!

k8s-chart-version:  ## get the latest versin number for helm chart K8S_CHART
	@. $(K8S_SUPPORT) ; K8S_HELM_REPOSITORY=$(K8S_HELM_REPOSITORY) k8sChartVersion $(K8S_CHART)

## TARGET: k8s-vars
## SYNOPSIS: make k8s-vars
## HOOKS: none
## VARS: none
##
##  Describe the current Kubernetes context and Helm Chart.

k8s-vars: ## Which kubernetes are we connected to
	@echo "Kubernetes cluster-info:"
	@kubectl cluster-info || true
	@echo ""
	@echo "kubectl version:"
	@kubectl version || true
	@echo ""
	@echo "Helm version:"
	@helm version --client
	@echo "Selected Namespace: $(KUBE_NAMESPACE)"
	@echo "Chart: $(K8S_CHART)"
	@echo "Charts: $(K8S_CHARTS)"
	@echo "Chart params: $(K8S_CHART_PARAMS)"
	@echo "kubectl wait timeout: $(K8S_TIMEOUT)"

## TARGET: k8s-namespace
## SYNOPSIS: make k8s-namespace
## HOOKS: none
## VARS:
##       KUBE_NAMESPACE=<Kubernetes Namespace to allocate> - default is project name (directory)
##		 K8S_SKIP_NAMESPACE=<skip the target> - default is false
##
##  Create the Namespace indicated in KUBE_NAMESPACE.
##  If you don't have enough permissions to create namespace, set K8S_SKIP_NAMESPACE flag

k8s-namespace: ## create the kubernetes namespace
	@if [ "true" == "$(K8S_SKIP_NAMESPACE)" ]; then \
		echo "Namespace checks are skipped!"; \
	else \
		kubectl get namespace $(KUBE_NAMESPACE) > /dev/null 2>&1 ; \
			K_DESC=$$? ; \
			if [ $$K_DESC -eq 0 ] ; then \
				kubectl describe namespace $(KUBE_NAMESPACE); \
			else \
				kubectl create namespace $(KUBE_NAMESPACE); \
			fi; \
	fi

## TARGET: k8s-delete-namespace
## SYNOPSIS: make k8s-delete-namespace
## HOOKS: none
## VARS:
##       KUBE_NAMESPACE=<Kubernetes Namespace to delete> - default is project name (directory)
##		 K8S_SKIP_NAMESPACE=<skip the target> - default is false
##
##  Delete the Namespace indicated in KUBE_NAMESPACE.
##  If you don't have enough permissions to create namespace, set K8S_SKIP_NAMESPACE flag

k8s-delete-namespace: ## delete the kubernetes namespace
	@if [ "true" == "$(K8S_SKIP_NAMESPACE)" ]; then \
		echo "Namespace checks are skipped!"; \
		exit 1; \
	else \
		if [ "default" == "$(KUBE_NAMESPACE)" ] || [ "kube-system" == "$(KUBE_NAMESPACE)" ]; then \
			echo "You cannot delete Namespace: $(KUBE_NAMESPACE)"; \
			exit 1; \
		else \
			kubectl delete --ignore-not-found namespace $(KUBE_NAMESPACE); \
		fi; \
	fi

## TARGET: k8s-clean
## SYNOPSIS: make k8s-clean
## HOOKS: none
## VARS: none
##
##  Purge common temp Helm Chart and Python temp test files.
##  Python temp test files are deleted as they are mostly used in testing against Kubernetes as well.

k8s-clean: ## clean out temp files
	@rm -rf ./charts/*/charts/*.tgz \
		./charts/*/Chart.lock \
		./charts/*/requirements.lock \
		./repository/* \
		./.eggs \
		./charts/build \
		./build \
		./docs/build \
		./dist \
		./*.egg-info \
		tests/.pytest_cache \
		tests/unit/__pycache__ \
		tests/__pycache__ \
		tests/*/__pycache__ \
		$(PYTHON_SRC)/*/__pycache__ \
		$(PYTHON_SRC)/*/*/__pycache__ \
		.pytest_cache \
		.coverage


## TARGET: k8s-dep-update
## SYNOPSIS: make k8s-dep-update
## HOOKS: k8s-pre-dep-update, k8s-post-dep-update
## VARS:
##       K8S_CHARTS=<list of chart names for ./charts directory> - defaults to repository name
##
##  Iterate over K8S_CHARTS list of chart names and pull and update the sub-chart
##  dependencies described in each respective Chart.yaml file.

k8s-pre-dep-update:

k8s-post-dep-update:

k8s-do-dep-update:
	@echo "k8s-dep-update: updating dependencies"
	@cd charts; \
	for i in $(K8S_CHARTS); do \
		echo "+++ Updating $${i} chart +++"; \
		helm dependency update $${i}; \
	done;

k8s-dep-update: k8s-pre-dep-update k8s-do-dep-update k8s-post-dep-update ## update dependencies for every charts in the env var K8S_CHARTS


## TARGET: k8s-install-chart
## SYNOPSIS: make k8s-install-chart
## HOOKS: k8s-pre-install-chart, k8s-post-install-chart
## VARS:
##       HELM_RELEASE=<Helm relase name> - default 'test'
##       K8S_UMBRELLA_CHART_PATH=<a Helm compatible path name for a chart to install> - default ./charts/$(K8S_CHART)/
##       KUBE_NAMESPACE=<Kubernetes Namespace to deploy to> - default is project name (directory)
##       KUBE_APP=<a value for the app label> - defaults to project name
##       K8S_CHART_PARAMS=<list of additional parameters to pass to helm> - default empty
##
##  Deploy an instance (HELM_RELEASE) of a given Helm Chart into a specified Kubernetes
##  Namespace (KUBE_NAMESPACE), with a configurable set of parameters (K8S_CHART_PARAMS).

k8s-pre-install-chart:

k8s-post-install-chart:

k8s-do-install-chart: k8s-clean k8s-dep-update k8s-namespace
	@echo "install-chart: install $(K8S_UMBRELLA_CHART_PATH) release: $(HELM_RELEASE) in Namespace: $(KUBE_NAMESPACE) with params: $(K8S_CHART_PARAMS)"
	helm upgrade --install $(HELM_RELEASE) \
	$(K8S_CHART_PARAMS) \
	 $(K8S_UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE)

k8s-install-chart: k8s-pre-install-chart k8s-do-install-chart k8s-post-install-chart ## install the helm chart with name HELM_RELEASE and path K8S_UMBRELLA_CHART_PATH on the namespace KUBE_NAMESPACE

## TARGET: k8s-install-chart-car
## SYNOPSIS: make k8s-install-chart-car
## HOOKS: k8s-pre-install-chart-car:, k8s-post-install-chart-car
## VARS:
##       KUBE_NAMESPACE=<Kubernetes Namespace to deploy to> - default is project name (directory)
##       K8S_CHART_PARAMS=<list of additional parameters to pass to helm> - default empty
##       K8S_CHART=chart name - default on the repository's Makefile
##       K8S_HELM_REPOSITORY= Helm repository to retrieve the chart - defaults to 'https://artefact.skao.int/repository/helm-internal'
##
##  Deploys a chart from CAR(https://artefact.skao.int/repository/helm-internal)

k8s-pre-install-chart-car:

k8s-post-install-chart-car:

k8s-do-install-chart-car: k8s-clean k8s-dep-update k8s-namespace
	@. $(K8S_INSTALL_CHART); K8S_CHART_PARAMS="$(K8S_CHART_PARAMS)" \
	KUBE_NAMESPACE=$(KUBE_NAMESPACE) \
	K8S_HELM_REPOSITORY=$(K8S_HELM_REPOSITORY) \
	HELM_RELEASE=$(HELM_RELEASE) \
	K8S_CHART=$(K8S_CHART) \
	k8sChartInstall

k8s-install-chart-car: k8s-pre-install-chart-car k8s-do-install-chart-car k8s-post-install-chart-car

k8s-pre-template-chart:

k8s-post-template-chart:

k8s-do-template-chart: k8s-clean k8s-dep-update
	@echo "template-chart: install $(K8S_UMBRELLA_CHART_PATH) release: $(HELM_RELEASE) in Namespace: $(KUBE_NAMESPACE) with params: $(K8S_CHART_PARAMS)"
	kubectl create ns $(KUBE_NAMESPACE) --dry-run=client -o yaml | tee manifests.yaml; \
	helm template $(HELM_RELEASE) \
	$(K8S_CHART_PARAMS) \
	--debug \
	 $(K8S_UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE) | tee -a manifests.yaml

## TARGET: k8s-template-chart
## SYNOPSIS: make k8s-template-chart
## HOOKS: k8s-pre-template-chart, k8s-post-template-chart
## VARS:
##       HELM_RELEASE=<Helm relase name> - default 'test'
##       K8S_UMBRELLA_CHART_PATH=<a Helm compatible path name for a chart to template> - default ./charts/$(K8S_CHART)/
##       KUBE_NAMESPACE=<Kubernetes Namespace to deploy to> - default is project name (directory)
##       KUBE_APP=<a value for the app label> - defaults to project name
##       K8S_CHART_PARAMS=<list of additional parameters to pass to helm> - default empty
##
##  Render a given Helm Chart(HELM_RELEASE) for a specified Kubernetes Namespace(KUBE_NAMESPACE), with a configurable
##  set of parameters(K8S_CHART_PARAMS), as a set of YAML manifest files.

k8s-template-chart: k8s-pre-template-chart k8s-do-template-chart k8s-post-template-chart ## template the helm chart with name HELM_RELEASE and path K8S_UMBRELLA_CHART_PATH on the namespace KUBE_NAMESPACE

k8s-bounce: ## restart all statefulsets by scaling them down and up
	echo "stopping ..."; \
	kubectl -n $(KUBE_NAMESPACE) scale --replicas=0 statefulset.apps -l app=$(KUBE_APP); \
	echo "starting ..."; \
	kubectl -n $(KUBE_NAMESPACE) scale --replicas=1 statefulset.apps -l app=$(KUBE_APP); \
	echo "WARN: 'make k8s-wait' for terminating pods not possible. Use 'make k8s-watch'"


k8s-pre-uninstall-chart:

k8s-post-uninstall-chart:

k8s-do-uninstall-chart:
	@echo "uninstall-chart: release: $(HELM_RELEASE) in Namespace: $(KUBE_NAMESPACE)"
	@helm uninstall  $(HELM_RELEASE) --namespace $(KUBE_NAMESPACE) || true

## TARGET: k8s-uninstall-chart
## SYNOPSIS: make k8s-uninstall-chart
## HOOKS: k8s-pre-uninstall-chart, k8s-post-uninstall-chart
## VARS:
##       HELM_RELEASE=<Helm relase name> - default 'test'
##       KUBE_NAMESPACE=<Kubernetes Namespace to deploy to> - default is project name (directory)
##
##  Teardown an instance (HELM_RELEASE) of a given Helm Chart from a specified
##  Kubernetes Namespace, with a configurable set of parameters.

k8s-uninstall-chart: k8s-pre-uninstall-chart k8s-do-uninstall-chart k8s-post-uninstall-chart ## uninstall the helm chart with name HELM_RELEASE on the namespace KUBE_NAMESPACE

k8s-reinstall-chart: k8s-uninstall-chart k8s-install-chart ## reinstall test-parent helm chart on the namespace ska-tango-examples

k8s-upgrade-chart: k8s-install-chart ## upgrade the test-parent helm chart on the namespace ska-tango-examples

## TARGET: k8s-wait
## SYNOPSIS: make k8s-wait
## HOOKS: none
## VARS:
##       HELM_RELEASE=<Helm relase name> - default 'test'
##       KUBE_NAMESPACE=<Kubernetes Namespace to deploy to> - default is project name (directory)
##       KUBE_APP=<a value for the app label> - defaults to project name
##       K8S_TIMEOUT=<timeout value> - defaults to 360s
##
##  Wait for the the Jobs and Pods deployed to a given KUBE_NAMESPACE with an app
##  label of KUBE_APP.  Will generate a log of Job/Pod logs and events if
##  the wait times outs.

k8s-wait: ## wait for Jobs and Pods to be ready in KUBE_NAMESPACE
	@. $(K8S_SUPPORT) ; K8S_TIMEOUT=$(K8S_TIMEOUT) \
		KUBE_APP=$(KUBE_APP) \
		k8sWait $(KUBE_NAMESPACE) $(SKA_TANGO_OPERATOR)

## TARGET: k8s-watch
## SYNOPSIS: make k8s-watch
## HOOKS: none
## VARS:
##       KUBE_NAMESPACE=<Kubernetes Namespace to deploy to> - default is project name (directory)
##
##  watch resources in KUBE_NAMESPACE using kubectl.

k8s-watch: ## watch all resources in the KUBE_NAMESPACE
	@kubectl get deviceservers.tango.tango-controls.org > /dev/null 2>&1; ret=$$?; \
	if [[ $$ret -eq 0 ]]; then \
		watch kubectl get deviceservers.tango.tango-controls.org,all,pv,pvc,ingress -n $(KUBE_NAMESPACE); \
	else \
		watch kubectl get all,pv,pvc,ingress -n $(KUBE_NAMESPACE); \
	fi

## TARGET: k8s-describe
## SYNOPSIS: make k8s-describe
## HOOKS: none
## VARS:
##       KUBE_NAMESPACE=<Kubernetes Namespace to deploy to> - default is project name (directory)
##       KUBE_APP=<a value for the app label> - defaults to project name
##
##  describe resources in KUBE_NAMESPACE using kubectl.with an app label of KUBE_APP.

k8s-describe: ## describe Pods executed from Helm chart
	@. $(K8S_SUPPORT) ; K8S_HELM_REPOSITORY=$(K8S_HELM_REPOSITORY) k8sDescribe $(KUBE_NAMESPACE) $(KUBE_APP)

## TARGET: k8s-podlogs
## SYNOPSIS: make k8s-podlogs
## HOOKS: none
## VARS:
##       KUBE_NAMESPACE=<Kubernetes Namespace to deploy to> - default is project name (directory)
##       KUBE_APP=<a value for the app label> - defaults to project name
##
##  Get Pod logs in KUBE_NAMESPACE using kubectl.with an app label of KUBE_APP.

k8s-podlogs: ## show Helm chart POD logs
	@. $(K8S_SUPPORT) ; K8S_HELM_REPOSITORY=$(K8S_HELM_REPOSITORY) k8sPodLogs $(KUBE_NAMESPACE) $(KUBE_APP)

k8s-get-pods: ##lists the pods deployed for a particular namespace. @param: KUBE_NAMESPACE
	kubectl get pods -n $(KUBE_NAMESPACE)

k8s-pod-versions: ## lists the container images used for particular pods
	kubectl get pods -l app=${KUBE_APP} -n $(KUBE_NAMESPACE) -o jsonpath="{range .items[*]}{.metadata.name}:{' '}{range .spec.containers[*]}{.image}{end}{'\n'}{end}{'\n'}"

k8s-kubeconfig: ## export current KUBECONFIG as base64 ready for KUBE_CONFIG_BASE64
	@KUBE_CONFIG_BASE64=`kubectl config view --flatten | base64`; \
	echo "KUBE_CONFIG_BASE64: $$(echo $${KUBE_CONFIG_BASE64} | cut -c 1-40)..."; \
	echo "appended to: PrivateRules.mak"; \
	echo -e "\n\n# base64 encoded from: kubectl config view --flatten\nKUBE_CONFIG_BASE64 = $${KUBE_CONFIG_BASE64}" >> PrivateRules.mak

# Bash script to run inside the testing pod. This does the following:
# 1. Create a FIFO to push the results to
# 2. Extract "$(k8s_test_folder)" folder (and possibly "$(k8s_test_src_dir)" if it exists),
#    the contents of which should be piped in through stdin
# 3. Install tests/requirements.txt if it exists
# 4. Invoke $(K8S_TEST_TEST_COMMAND) which defaults to pytest but could be a Makefile
#    located in tests/ - see above definition of K8S_TEST_TEST_COMMAND
# 5. Pipe results back through the FIFO (including make's return code)
k8s_test_src_modules = $(shell if [ -d $(PYTHON_SRC) ]; then cd $(PYTHON_SRC); ls -d */ 2>/dev/null  | grep -v .egg-info; fi)
k8s_test_src_dirs = $(shell if [ -n "$(k8s_test_src_modules)" ]; then for pkg in $(k8s_test_src_modules); do echo -n ":/app/$$pkg"; done; fi)
k8s_test_folder = tests
k8s_test_src_dir = $(shell if [ -d $(PYTHON_SRC) ]; then echo "$(PYTHON_SRC)/"; fi)

k8s_test_command = /bin/bash -o pipefail -c "\
	mkfifo results-pipe && tar zx --warning=all && \
        ( if [[ -f pyproject.toml ]]; then poetry export --format requirements.txt --output poetry-requirements.txt --without-hashes --dev; echo 'k8s-test: installing poetry-requirements.txt';  pip install -qUr poetry-requirements.txt; else if [[ -f $(k8s_test_folder)/requirements.txt ]]; then echo 'k8s-test: installing $(k8s_test_folder)/requirements.txt'; pip install -qUr $(k8s_test_folder)/requirements.txt; fi; fi ) && \
		export PYTHONPATH=${PYTHONPATH}:/app/$(PYTHON_SRC)$(k8s_test_src_dirs) && \
		mkdir -p build && \
	( \
	$(K8S_TEST_TEST_COMMAND); \
	); \
	echo \$$? > build/status; pip list > build/pip_list.txt; \
	echo \"k8s_test_command: test command exit is: \$$(cat build/status)\"; \
	tar zcf results-pipe build;"

k8s_test_runner = $(K8S_TEST_RUNNER) -n $(KUBE_NAMESPACE)
k8s_test_kubectl_run_args = \
	$(k8s_test_runner) --restart=Never --pod-running-timeout=$(K8S_TIMEOUT) \
	--image-pull-policy=IfNotPresent --image=$(K8S_TEST_IMAGE_TO_TEST) \
	--env=INGRESS_HOST=$(INGRESS_HOST) $(PROXY_VALUES) $(K8S_TEST_RUNNER_ADD_ARGS)

# Set up of the testing pod. This goes through the following steps:
# 1. Create the pod, piping the contents of $(k8s_test_folder) in. This is
#    run in the background, with stdout left attached - albeit slightly
#    de-cluttered by removing pytest's live logs.
# 2. In parallel we wait for the testing pod to become ready.
# 3. Once it is there, we attempt to pull the results from the FIFO queue.
#    This blocks until the testing pod script writes it (see above).
k8s-do-test:
	@rm -fr build; mkdir build
	@find ./$(k8s_test_folder) -name "*.pyc" -type f -delete
	@echo "k8s-test: start test runner: $(k8s_test_runner)"
	@echo "k8s-test: sending test folder: tar -cz $(k8s_test_src_dir) $(k8s_test_folder) $(K8S_TEST_AUX_DIRS)"
	( cd $(BASE); tar -cz $(k8s_test_src_dir) $(k8s_test_folder) $(K8S_TEST_AUX_DIRS) \
	  | kubectl run $(k8s_test_kubectl_run_args) -iq -- $(k8s_test_command) 2>&1 \
	  | grep -vE "^(1\||-+ live log)" --line-buffered &); \
	sleep 1; \
	echo "k8s-test: waiting for test runner to boot up: $(k8s_test_runner)"; \
	( \
	kubectl wait pod $(k8s_test_runner) --for=condition=ready --timeout=$(K8S_TIMEOUT); \
	wait_status=$$?; \
	if ! [[ $$wait_status -eq 0 ]]; then echo "Wait for Pod $(k8s_test_runner) failed - aborting"; exit 1; fi; \
	 ) && \
		echo "k8s-test: $(k8s_test_runner) is up, now waiting for tests to complete" && \
		(kubectl exec $(k8s_test_runner) -- cat results-pipe | tar --directory=$(BASE) -xz); \
	\
	cd $(BASE)/; \
	(kubectl get all,job,pv,pvc,ingress,cm -n $(KUBE_NAMESPACE) -o yaml > build/k8s_manifest.txt); \
	echo "k8s-test: test run complete, processing files"; \
	kubectl --namespace $(KUBE_NAMESPACE) delete --ignore-not-found pod $(K8S_TEST_RUNNER) --wait=false
	@echo "k8s-test: the test run exit code is ($$(cat build/status))"
	@exit `cat build/status`

k8s-do-test-runner:
##  Cleanup
	@rm -fr build; mkdir build
	@find ./$(k8s_test_folder) -name "*.pyc" -type f -delete

##  Install requirements
	if [[ -f pyproject.toml ]]; then \
		poetry config virtualenvs.create false; \
		echo 'k8s-test: installing poetry dependencies';  \
		poetry install; \
	else if [[ -f $(k8s_test_folder)/requirements.txt ]]; then \
			echo 'k8s-test: installing $(k8s_test_folder)/requirements.txt'; \
			pip install -qUr $(k8s_test_folder)/requirements.txt; \
		fi; \
	fi;

##  Run tests
	export PYTHONPATH=${PYTHONPATH}:/app/src$(k8s_test_src_dirs)
	mkdir -p build
	cd $(K8S_RUN_TEST_FOLDER) && $(K8S_TEST_TEST_COMMAND); echo $$? > $(BASE)/build/status

##  Post tests reporting
	pip list > build/pip_list.txt
	@echo "k8s_test_command: test command exit is: $$(cat build/status)"

k8s-pre-test:

k8s-post-test:

## TARGET: k8s-test
## SYNOPSIS: make k8s-test
## HOOKS: k8s-pre-test, k8s-post-test
## VARS:
##       K8S_TEST_TEST_COMMAND=<a command passed into the test Pod> - see K8S_TEST_TEST_COMMAND
##       KUBE_NAMESPACE=<Kubernetes Namespace to deploy to> - default is project name (directory)
##       K8S_TEST_RUNNER=<name of test runner container>
##       K8S_TIMEOUT=<timeout value> - defaults to 360s
##       PYTHON_RUNNER=<python executor> - defaults to empty, but could pass something like python -m
##       PYTHON_VARS_BEFORE_PYTEST=<environment variables defined before pytest in run> - default empty
##       PYTHON_VARS_AFTER_PYTEST=<additional switches passed to pytest> - default empty
##       K8S_TEST_AUX_DIRS=<a list of extra directories to transfer to the test Pod> - default empty
##
##  Launch a K8S_TEST_RUNNER in the target Kubernetes Namespace, to run the tests against a
##  deployed environment in the same way that python-test runs in a local context.
##  The default configuration runs pytest against the tests defined in ./tests.
##  By default, this will pickup any pytest specific configuration set in pytest.ini,
##  setup.cfg etc. located in ./tests.
##  This test harness, is highly configurable, in that it is essentially a mechanism that enables
##  remote execution of a oneline shell command, that is started in a copy of the current ./tests
##  directory, and on completion, the contents of the ./build directory is returned.  This is suited
##  to the standard pytest runtime.
##  With this in mind, the default configuration for the oneline shellscript looks like:
##  K8S_TEST_TEST_COMMAND ?= cd .. && $(PYTHON_VARS_BEFORE_PYTEST) $(PYTHON_RUNNER) \
##  						pytest \
##  						$(PYTHON_VARS_AFTER_PYTEST) ./tests \
##  						 | tee pytest.stdout; ## k8s-test test command to run in container
## NOTE the command steps back a directory so as to be outside of ./tests when k8s-test is
##   running - this is to bring it into line with python-test behaviour.
##
##  This can be replaced with essentially any executable application - for example, the one
##  configured in Skampi is based on make:.
##  K8S_TEST_TEST_COMMAND = make -s \
##  			$(K8S_TEST_MAKE_PARAMS) \
##  			$(K8S_TEST_TARGET)
##
##  The test runner Pod is launched, and the contents of ./tests is piped in before the
##  K8S_TEST_TEST_COMMAND is executed.  This is expected to generate output into a ./build
##  directory with a specifc set of files containing the test report output - the same as python-test.

k8s-test: k8s-pre-test k8s-do-test k8s-post-test  ## run the defined test cycle against Kubernetes

## TARGET: k8s-test-runner
## SYNOPSIS: make k8s-test-runner
## HOOKS: k8s-pre-test, k8s-post-test
## VARS:
##       K8S_TEST_TEST_COMMAND=<a command passed into the test Pod> - see K8S_TEST_TEST_COMMAND
##       K8S_RUN_TEST_FOLDER=<folder from which to execute K8S_TEST_TEST_COMMAND> - defaults to ./
##       KUBE_NAMESPACE=<Kubernetes Namespace to deploy to> - default is project name (directory)
##       K8S_TEST_RUNNER=<name of test runner container>
##       K8S_TIMEOUT=<timeout value> - defaults to 360s
##       PYTHON_RUNNER=<python executor> - defaults to empty, but could pass something like python -m
##       PYTHON_VARS_BEFORE_PYTEST=<environment variables defined before pytest in run> - default empty
##       PYTHON_VARS_AFTER_PYTEST=<additional switches passed to pytest> - default empty
##       K8S_TEST_AUX_DIRS=<a list of extra directories to transfer to the test Pod> - default empty
##
##  Run the tests on the runner pod against a deployed environment in the same way that 
##  python-test runs in a local context.
##  The default configuration runs pytest against the tests defined in ./tests.
##  By default, this will pickup any pytest specific configuration set in pytest.ini,
##  setup.cfg etc. located in ./tests.
##  This test harness, is highly configurable, in that it is essentially a mechanism that enables
##  remote execution of a oneline shell command, that is started in a copy of the current ./tests
##  directory, and on completion, the contents of the ./build directory is returned.  This is suited
##  to the standard pytest runtime.
##  With this in mind, the default configuration for the oneline shellscript looks like:
##  K8S_TEST_TEST_COMMAND ?= cd .. && $(PYTHON_VARS_BEFORE_PYTEST) $(PYTHON_RUNNER) \
##  						pytest \
##  						$(PYTHON_VARS_AFTER_PYTEST) ./tests \
##  						 | tee pytest.stdout; ## k8s-test test command to run in container
## NOTE the command steps back a directory so as to be outside of ./tests when k8s-test is
##   running - this is to bring it into line with python-test behaviour.
##
##  This can be replaced with essentially any executable application - for example, the one
##  configured in Skampi is based on make:.
##  K8S_TEST_TEST_COMMAND = make -s \
##  			$(K8S_TEST_MAKE_PARAMS) \
##  			$(K8S_TEST_TARGET)
##
##  This is expected to generate output into a ./build directory with a specifc set of files 
##  containing the test report output - the same as python-test.

k8s-test-runner: k8s-pre-test k8s-do-test-runner k8s-post-test  ## run the defined test cycle against Kubernetes

k8s-smoke-test: k8s-wait ## wait target

k8s-get-size-images: ## get a list of images together with their size (both local and compressed) in the namespace KUBE_NAMESPACE
	@for p in `kubectl get pods -n $(KUBE_NAMESPACE) -o jsonpath="{range .items[*]}{range .spec.containers[*]}{.image}{'\n'}{end}{range .spec.initContainers[*]}{.image}{'\n'}{end}{end}" | sort | uniq`; do \
		docker pull $$p > /dev/null; \
		B=`docker inspect -f "{{ .Size }}" $$p`; \
		if [ ! -z "$$BIGGER_THAN" ] ; then \
			MB=$$(((B)/1024/1024)); \
			if [ $$MB -lt $$BIGGER_THAN ] ; then \
				continue; \
			fi; \
		fi; \
		MB=$$(((B)/1000000)); \
		cB=`docker manifest inspect $$p | jq '[.layers[].size] | add'`; \
		cMB=$$(((cB)/1000000)); \
		echo $$p: $$B B \($$MB MB\), $$cB \($$cMB MB\); \
	done;

k8s-interactive: ## run the ipython command in the itango console available with the tango-base chart
	@kubectl exec -it ska-tango-base-itango-console -c itango -n $(KUBE_NAMESPACE) -- itango3
