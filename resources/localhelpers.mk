# This .mk file include contains convenience and legacy targets

vars: skampi-vars

namespace-sdp: KUBE_NAMESPACE := $(KUBE_NAMESPACE_SDP)
namespace-sdp: ## create the kubernetes namespace for SDP dynamic deployments
	@make k8s-namespace KUBE_NAMESPACE=$(KUBE_NAMESPACE)

delete-sdp-namespace: KUBE_NAMESPACE := $(KUBE_NAMESPACE_SDP)
delete-sdp-namespace: ## delete the kubernetes SDP namespace
	@make k8s-delete-namespace KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)

PYTHON_VARS_BEFORE_PYTEST +=  LOADBALANCER_IP=${LOADBALANCER_IP} CLUSTER_TEST_NAMESPACE=$(CLUSTER_TEST_NAMESPACE)
verify-minikube: # Run only infra tests on local minikube cluster as precursor
	@make python-test LOADBALANCER_IP=$(shell minikube ip) PYTHON_VARS_AFTER_PYTEST=' -m infra'
	@make k8s-delete-namespace KUBE_NAMESPACE=$(CLUSTER_TEST_NAMESPACE)

# install: k8s-clean k8s-namespace namespace-sdp check-archiver-dbname k8s-install-chart## install the helm chart on the namespace KUBE_NAMESPACE
install: k8s-clean k8s-namespace namespace-sdp## install the helm chart on the namespace KUBE_NAMESPACE and wait for completion of jobs
	make k8s-install-chart \
		TARANTA_AUTH_DASHBOARD_ENABLE=$(TARANTA_AUTH_DASHBOARD_ENABLE) \
		KUBE_NAMESPACE=$(KUBE_NAMESPACE) \
		KUBE_NAMESPACE_SDP=$(KUBE_NAMESPACE_SDP) \
		CONFIG=$(CONFIG) \
	k8s-wait

uninstall: k8s-uninstall-chart ## uninstall the helm chart on the namespace KUBE_NAMESPACE

reinstall-chart: uninstall install ## reinstall the  helm chart on the namespace KUBE_NAMESPACE

install-or-upgrade: k8s-install-chart## install or upgrade the release

quotas: k8s-namespace## delete and create the kubernetes namespace with quotas
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
		$(K8S_CHART_PARAMS) \
		--values $(VALUES) \
		$(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE);

## TARGET: skampi-links
## SYNOPSIS: make skampi-links
## HOOKS: none
## VARS: none
##  make target for generating the URLs for accessing a Skampi deployment

skampi-links: ## Create the URLs with which to access Skampi if it is available
	@echo ${CI_JOB_NAME}
	@echo "############################################################################"
	@echo "#            Access the Skampi landing page here:"
	@echo "#            https://$(INGRESS_HOST)/$(KUBE_NAMESPACE)/start/"
	@echo "############################################################################"
	@if [[ -z "${LOADBALANCER_IP}" ]]; then exit 0; \
	elif [[ "${CI_JOB_NAME}" == "psi_mid_deploy_on_demand" ]]; then echo "NOTE: Above link will only work if you can reach $(INGRESS_HOST)" && exit 0; \
	elif [[ $(shell curl -I -s -o /dev/null -I -w \'%{http_code}\' http$(S)://$(LOADBALANCER_IP)/$(KUBE_NAMESPACE)/start/) != '200' ]]; then \
		echo "ERROR: http://$(LOADBALANCER_IP)/$(KUBE_NAMESPACE)/start/ unreachable"; exit 10; \
	fi