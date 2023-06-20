# This .mk include contains the Skampi specific make target extensions

skampi-credentials:  ## PIPELINE USE ONLY - allocate credentials for deployment namespaces
	make k8s-namespace
	make k8s-namespace KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)
	curl -s https://gitlab.com/ska-telescope/templates-repository/-/raw/master/scripts/namespace_auth.sh | bash -s $(SERVICE_ACCOUNT) $(KUBE_NAMESPACE) $(KUBE_NAMESPACE_SDP) || true


## TARGET: skampi-vars
## SYNOPSIS: make skampi-vars
## HOOKS: none
## VARS: none
##  runs make k8s-vars and extends with Skampi specific variables

skampi-vars: k8s-vars ## Display Skampi deployment context variables
	@echo "SKA_K8S_TOOLS_DEPLOY_IMAGE: $(SKA_K8S_TOOLS_DEPLOY_IMAGE)"
	@echo "K8S_TEST_IMAGE_TO_TEST:     $(K8S_TEST_IMAGE_TO_TEST)"
	@echo "KUBE_NAMESPACE:             $(KUBE_NAMESPACE)"
	@echo "KUBE_NAMESPACE_SDP:         $(KUBE_NAMESPACE_SDP)"
	@echo "INGRESS_HOST:               $(INGRESS_HOST)"
	@echo "DEPLOYMENT_CONFIGURATION:   $(DEPLOYMENT_CONFIGURATION)"
	@echo "K8S_CHART:                  $(K8S_CHART)"
	@echo "HELM_RELEASE:               $(HELM_RELEASE)"
	@echo "HELM_REPO_NAME:             $(HELM_REPO_NAME) ## (should be empty except on Staging & Production)"
	@echo "VALUES:                     $(VALUES)"
	@echo "TANGO_HOST:                 $(TANGO_HOST)"
	@echo "ARCHIVER_DBNAME:            $(ARCHIVER_DBNAME)"
	@echo "MARK:                       $(MARK)"
	@echo "CONFIG:                     $(CONFIG)"
	@echo "TEL:                        $(TEL)"
	@echo "TEST_ENV:                   $(TEST_ENV)"

## TARGET: skampi-update-chart-versions
## SYNOPSIS: make skampi-update-chart-versions
## HOOKS: none
## VARS:
##       SKAMPI_K8S_CHARTS=<list of helm chart directories under ./charts/>
##       K8S_HELM_REPOSITORY=helm chart repository
##
##  Inspects the list of charts defined in SKAMPI_K8S_CHARTS and then updates
##  the dependencies in Chart.yaml to the latest found in K8S_HELM_REPOSITORY .

skampi-update-chart-versions: helm-install-yq ## update Skampi chart dependencies to latest versions eg: ska-tango-base etc.
	@for chart in $(SKAMPI_K8S_CHARTS); do \
		echo "update-chart-versions: inspecting charts/$$chart/Chart.yaml";  \
		for upd in $$(/usr/local/bin/yq e '.dependencies[].name' charts/$$chart/Chart.yaml | grep -v ska-landingpage); do \
			cur_version=$$(cat charts/$$chart/Chart.yaml | /usr/local/bin/yq e ".dependencies[] | select(.name == \"$$upd\") | .version" -); \
			echo "update-chart-versions: finding latest version for $$upd current version: $$cur_version"; \
			upd_version=$$(. $(K8S_SUPPORT) ; K8S_HELM_REPOSITORY=$(K8S_HELM_REPOSITORY) k8sChartVersion $$upd); \
			echo "update-chart-versions: updating $$upd from $$cur_version to $$upd_version"; \
			sed -i.x -e "N;s/\(name: $$upd.*version:\).*/\1 $${upd_version}/;P;D" charts/$$chart/Chart.yaml; \
			rm -f charts/*/Chart.yaml.x; \
		done; \
	done

## TARGET: skampi-upload-test-results
## SYNOPSIS: make skampi-upload-test-results
## HOOKS: none
## VARS:
##		SKALLOP_VERSION=<version of Skallop to install>
##		CAR_PYPI_REPOSITORY_URL=<URL of Central Artefact Repository>
## 	uploads cucumber test results to XTP Jira project using XRAY API implementation in SKALLOP package

TEST_EXEC_FILE_PATH?=tests/test-exec-$(CONFIG).json

skampi-upload-test-results: ## Upload Skampi system acceptance and integration test results
	@echo "Processing XRay uploads using $(TEST_EXEC_FILE_PATH)"
	@if [ -n "$$(ls -A build/cucumber*.json 2>/dev/null)" ]; then \
		bash scripts/gitlab_section.sh install_skallop "Installing Skallop Requirements" pip3 install -U "ska-ser-skallop==$(SKALLOP_VERSION)"  --extra-index-url $(CAR_PYPI_REPOSITORY_URL); \
	fi
	@for cuke in  build/cucumber*.json; do \
		echo "Processing XRay upload of: $$cuke"; \
		if [[ -z "${JIRA_USERNAME}" ]]; then \
			/usr/local/bin/xtp-xray-upload -f $$cuke -i $(TEST_EXEC_FILE_PATH) -v; \
		else \
			echo "Using Jira Username and Password for auth"; \
			xtp-xray-upload -f $$cuke -i $(TEST_EXEC_FILE_PATH) -v -u ${JIRA_USERNAME} -p ${JIRA_PASSWORD}; \
		fi; \
	done; \


## TARGET: tango-wait-all
## SYNOPSIS: make tango-wait-all
## HOOKS: none
##  For the ping command to succeed for all registered devices
tango-wait-all:
	sleep 3 && \
	TANGO_HOST="$(TANGO_DATABASE_DS).$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN):10000" python3 scripts/wait_ping_devices.py

## TARGET: skampi-wait-all
## SYNOPSIS: make skampi-wait-all
## HOOKS: none
## VARS:
##       SKAMPI_YQ_VERSION=yq version to install
##  Introspects the chosen chart and look for sub-charts.  Iterate over these
##  and k8s-wait for each one.

skampi-wait-all: helm-install-yq k8s-wait ## iterate over sub-charts and wait for each one
	make k8s-wait SKA_TANGO_OPERATOR=false

# Set up of the testing pod. This goes through the following steps:
# 1. Create the pod, piping the contents of $(k8s_test_folder) in. This is
#    run in the background, with stdout left attached - albeit slightly
#    de-cluttered by removing pytest's live logs.
# 2. In parallel we wait for the testing pod to become ready.
# 3. Once it is there, we attempt to pull the results from the FIFO queue.
#    This blocks until the testing pod script writes it (see above).
skampi-k8s-do-test:
	@rm -fr build; mkdir build
	@find ./$(k8s_test_folder) -name "*.pyc" -type f -delete
	@echo "skampi-k8s-test: start test runner: $(k8s_test_runner)"
	@echo "skampi-k8s-test: sending test folder: tar -cz $(k8s_test_folder)/"
	( cd $(BASE); tar --exclude $(k8s_test_folder)/integration  --exclude $(k8s_test_folder)/resources  --exclude $(k8s_test_folder)/unit  --exclude $(k8s_test_folder)/conftest.py  --exclude $(k8s_test_folder)/pytest.ini -cz $(k8s_test_folder)/ \
	  | kubectl run $(k8s_test_kubectl_run_args) -iq -- $(k8s_test_command) 2>&1 \
	  | grep -vE "^(1\||-+ live log)" --line-buffered &); \
	sleep 1; \
	echo "skampi-k8s-test: waiting for test runner to boot up: $(k8s_test_runner)"; \
	( \
	kubectl wait pod $(k8s_test_runner) --for=condition=ready --timeout=$(K8S_TIMEOUT); \
	wait_status=$$?; \
	if ! [[ $$wait_status -eq 0 ]]; then echo "Wait for Pod $(k8s_test_runner) failed - aborting"; exit 1; fi; \
	 ) && \
		echo "skampi-k8s-test: $(k8s_test_runner) is up, now waiting for tests to complete" && \
		(kubectl exec $(k8s_test_runner) -- cat results-pipe | tar --directory=$(BASE) -xz); \
	\
	cd $(BASE)/; \
	(kubectl get all,job,pv,pvc,ingress,cm -n $(KUBE_NAMESPACE) -o yaml > build/k8s_manifest.txt); \
	echo "skampi-k8s-test: test run complete, processing files"; \
	kubectl --namespace $(KUBE_NAMESPACE) delete --ignore-not-found pod $(K8S_TEST_RUNNER) --wait=false
	@echo "skampi-k8s-test: the test run exit code is ($$(cat build/status))"
	@exit `cat build/status`

skampi-k8s-pre-test:

skampi-k8s-post-test:

## TARGET: skampi-k8s-test
## SYNOPSIS: make skampi-k8s-test
## HOOKS: skampi-k8s-pre-test, skampi-k8s-post-test
## VARS:
##       K8S_TEST_TEST_COMMAND=<a command passed into the test Pod> - see K8S_TEST_TEST_COMMAND
##       KUBE_NAMESPACE=<Kubernetes Namespace to deploy to> - default is project name (directory)
##       K8S_TEST_RUNNER=<name of test runner container>
##       K8S_TIMEOUT=<timeout value> - defaults to 360s
##       PYTHON_RUNNER=<python executor> - defaults to empty, but could pass something like python -m
##       PYTHON_VARS_BEFORE_PYTEST=<environment variables defined before pytest in run> - default empty
##       PYTHON_VARS_AFTER_PYTEST=<additional switches passed to pytest> - default empty
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
##  						 | tee pytest.stdout; ## skampi-k8s-test test command to run in container
## NOTE the command steps back a directory so as to be outside of ./tests when skampi-k8s-test is
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

skampi-k8s-test: skampi-k8s-pre-test skampi-k8s-do-test skampi-k8s-post-test  ## run the defined test cycle against Kubernetes

## TARGET: skampi-component-tests
## SYNOPSIS: make skampi-component-tests
## HOOKS: none
## VARS: none
##  introspects the Makefile looking for targets starting with skampi-test-*
##  and then executes them in sorted order.
##  These tests are run directly after k8s-test.
##  The report.xml and cucumber.json are concatenated across the test runs.

skampi-component-tests:  ## iterate over Skampi component tests defined as make targets
	@which junitparser >/dev/null 2>&1 || pip3 install junitparser
	@mkdir -p build.previous build
	@if compgen -G "build/*" > /dev/null; then \
 		echo "skampi-component-tests: copying old build files to previous"; \
		cp -r build/* build.previous/; \
	fi
	@for component in `grep -E '^skampi-test-[0-9a-zA-Z_-]+:.*$$' $(MAKEFILE_LIST) | sed 's/^[^:]*://' | sed 's/:.*$$//' | sort`; do \
		echo "skampi-component-tests: Running test in Component: $$component"; \
		rm -rf build/*; \
		make $$component K8S_TEST_RUNNER=test-$$component; \
		if ! [[ -f build/status ]]; then \
			echo "skampi-component-tests: something went very wrong with the test container (no build/status file) - ABORTING!"; \
			exit 1; \
		fi; \
		echo "skampi-component-tests: result for Component: $$component is ($$(cat build/status))"; \
		echo "skampi-component-tests: process reports for Component: $$component"; \
		if [[ -f build.previous/report.xml ]] && [[ -f build/report.xml ]]; then \
			junitparser merge build.previous/report.xml build/report.xml report.xml; \
			mv report.xml build.previous/report.xml; \
		fi; \
		if [[ -f build/cucumber.json ]]; then \
			cp -f build/cucumber.json build.previous/cucumber-$$component.json; \
		fi; \
		if [[ -f build/status ]]; then \
			cp -f build/status build.previous/$$component-status; \
		fi; \
	done
	@rm -rf build
	@mv build.previous build
	@if [[ -n "$$(grep -v '0' build/*status)" ]]; then \
		echo "skampi-component-tests: Errors occurred in tests - ABORTING!"; \
		exit 1; \
	fi

## TARGET: skampi-test-01centralnode
## SYNOPSIS: make skampi-test-01centralnode
## HOOKS: none
## VARS: none
##  make target for running the Central Node specific tests against Skampi

# skampi-test-01centralnode:  ## launcher for centralnode tests
# 	@version=$$(helm dependency list charts/$(DEPLOYMENT_CONFIGURATION) | awk '$$1 == "ska-tmc-centralnode" {print $$2}'); \
# 	telescope=$$(echo $(DEPLOYMENT_CONFIGURATION) | sed s/-/_/ | sed s/ska/SKA/); \
# 	make skampi-k8s-test K8S_TEST_IMAGE_TO_TEST=artefact.skao.int/ska-tmc-centralnode:$$version MARK="$$telescope and acceptance"
