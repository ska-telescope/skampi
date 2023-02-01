# This .mk file include contains convenience and legacy targets

vars: skampi-vars

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

quotas: k8s-namespace## delete and create the kubernetes namespace with quotas
	kubectl -n $(KUBE_NAMESPACE) apply -f resources/namespace_with_quotas.yaml

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
	elif [[ "${CI_JOB_NAME}" == "psi_mid_on_demand_deploy" ]]; then echo "NOTE: Above link will only work if you can reach $(INGRESS_HOST)" && exit 0; \
	elif [[ $(shell curl -I -s -o /dev/null -I -w \'%{http_code}\' http$(S)://$(LOADBALANCER_IP)/$(KUBE_NAMESPACE)/start/) != '200' ]]; then \
		echo "ERROR: http://$(LOADBALANCER_IP)/$(KUBE_NAMESPACE)/start/ unreachable"; exit 10; \
	fi