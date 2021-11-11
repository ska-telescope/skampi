# This .mk include contains the Skampi specific make target extensions

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

## TARGET: skampi-update-chart-versions
## SYNOPSIS: make skampi-update-chart-versions
## HOOKS: none
## VARS:
##       SKAMPI_K8S_CHARTS=<list of helm chart directories under ./charts/>
##       K8S_HELM_REPOSITORY=helm chart repository
##
##  Inspects the list of charts defined in SKAMPI_K8S_CHARTS and then updates
##  the dependencies in Chart.yaml to the latest found in K8S_HELM_REPOSITORY .

skampi-update-chart-versions:  ## update Skampi chart dependencies to latest versions eg: ska-tango-base etc.
	@[[ ! -f "/usr/local/bin/yq" ]] || (echo "/usr/local/bin/jq not installed - see https://github.com/mikefarah/yq/"; exit 1;)
	@for chart in $(SKAMPI_K8S_CHARTS); do \
		echo "update-chart-versions: inspecting charts/$$chart/Chart.yaml";  \
		for upd in $$(/usr/local/bin/yq e '.dependencies[].name' charts/$$chart/Chart.yaml); do \
			cur_version=$$(cat charts/$$chart/Chart.yaml | /usr/local/bin/yq e ".dependencies[] | select(.name == \"$$upd\") | .version"); \
			echo "update-chart-versions: finding latest version for $$upd current version: $$cur_version"; \
			upd_version=$$(. $(K8S_SUPPORT) ; K8S_HELM_REPOSITORY=$(K8S_HELM_REPOSITORY) k8sChartVersion $$upd); \
			echo "update-chart-versions: updating $$upd from $$cur_version to $$upd_version"; \
			sed -i.x -e "N;s/\(name: $$upd.*version:\).*/\1 $${upd_version}/;P;D" charts/$$chart/Chart.yaml; \
			rm -f charts/*/Chart.yaml.x; \
		done; \
	done

## TARGET: skampi-wait-all
## SYNOPSIS: make skampi-wait-all
## HOOKS: none
## VARS: none
##  Introspects the chosen chart and look for sub-charts.  Iterate over these
##  and k8s-wait for each one.

skampi-wait-all:  ## iterate over sub-charts and wait for each one
	for chart in `helm inspect chart $(K8S_UMBRELLA_CHART_PATH) | /usr/local/bin/yq e '.dependencies[].name' - | grep -v ska-tango-util`; do \
		echo "Waiting for sub-chart: $${chart}"; \
		make k8s-wait KUBE_APP=$${chart}; \
	done

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
	@mkdir -p build.previous
	@cp -r build/* build.previous/
	@for component in `grep -E '^skampi-test-[0-9a-zA-Z_-]+:.*$$' $(MAKEFILE_LIST) | sed 's/^[^:]*://' | sed 's/:.*$$//' | sort`; do \
		echo "Running test in Component: $$component"; \
		rm -rf build/*; \
		make $$component K8S_TEST_RUNNER=test-$$component; \
		if [[ -f build.previous/report.xml ]] && [[ -f build/report.xml ]]; then \
			junitparser merge build.previous/report.xml build/report.xml report.xml; \
			mv report.xml build.previous/report.xml; \
		fi; \
		if [[ -f build.previous/cucumber.json ]] && [[ -f build/cucumber.json ]]; then \
			cat build.previous/cucumber.json | sed 's/]$$/,/' > cucumber1.json; \
			cat build/cucumber.json | sed 's/^\[//' > cucumber2.json; \
			cat cucumber1.json cucumber2.json > build.previous/cucumber.json; \
			rm -f cucumber1.json cucumber2.json; \
		fi; \
	done
	@rm -rf build
	@mv build.previous build

## TARGET: skampi-test-01centralnode
## SYNOPSIS: make skampi-test-01centralnode
## HOOKS: none
## VARS: none
##  make target for running the Central Node specific tests against Skampi

skampi-test-01centralnode:  ## launcher for centralnode tests
	@version=$$(helm dependency list charts/$(DEPLOYMENT_CONFIGURATION) | awk '$$1 == "ska-tmc-centralnode" {print $$2}'); \
	telescope=$$(echo $(DEPLOYMENT_CONFIGURATION) | sed s/-/_/ | sed s/ska/SKA/); \
	make k8s-test K8S_TEST_IMAGE_TO_TEST=artefact.skao.int/ska-tmc-centralnode:$$version MARK="$$telescope and acceptance"
