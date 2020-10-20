

KUBE_NAMESPACE ?= integration#namespace to be used
KUBE_NAMESPACE_SDP ?= integration-sdp#namespace to be used
DOMAIN_TAG ?= test## always set for TANGO_DATABASE_DS
TANGO_DATABASE_DS ?= databaseds-tango-base-$(DOMAIN_TAG) ## Stable name for the Tango DB
RELEASE_NAME ?= test## release name of the chart
DEPLOYMENT_CONFIGURATION ?= skamid## umbrella chart to work with
HELM_HOST ?= https://nexus.engageska-portugal.pt## helm host url https
MINIKUBE ?= true## Minikube or not
UMBRELLA_CHART_PATH = ./charts/$(DEPLOYMENT_CONFIGURATION)/

.DEFAULT_GOAL := help
-include test.mk

vars: ## Display variables 
	@echo "Namespace: $(KUBE_NAMESPACE)"
	@echo "RELEASE_NAME: $(RELEASE_NAME)"
	@echo "VALUES: $(VALUES)"
	@echo "TANGO_DATABASE_DS: $(TANGO_DATABASE_DS)"

k8s: ## Which kubernetes are we connected to
	@echo "Kubernetes cluster-info:"
	@kubectl cluster-info
	@echo ""
	@echo "kubectl version:"
	@kubectl version
	@echo ""
	@echo "Helm version:"
	@$(helm_tiller_prefix) helm version

logs: ## POD logs for descriptor
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l group=example -o=name`; \
	do echo "-------------------"; \
	echo "Logs for $$i"; \
	kubectl -n $(KUBE_NAMESPACE) logs $$i; \
	done


clean: ## clean out references to chart tgz's
	@rm -f ./*/charts/*.tgz ./*/Chart.lock ./*/requirements.lock 

namespace: ## create the kubernetes namespace
	@kubectl describe namespace $(KUBE_NAMESPACE) > /dev/null 2>&1 ; \
		K_DESC=$$? ; \
		if [ $$K_DESC -eq 0 ] ; \
		then kubectl describe namespace $(KUBE_NAMESPACE); \
		else kubectl create namespace $(KUBE_NAMESPACE); \
		fi

namespace_sdp: ## create the kubernetes namespace for SDP dynamic deployments
	@kubectl describe namespace $(KUBE_NAMESPACE_SDP) > /dev/null 2>&1 ; \
 	K_DESC=$$? ; \
	if [ $$K_DESC -eq 0 ] ; \
	then kubectl describe namespace $(KUBE_NAMESPACE_SDP) ; \
	else kubectl create namespace $(KUBE_NAMESPACE_SDP); \
	fi


lint:  ## lint the HELM_CHART of the helm chart
	cd $(UMBRELLA_CHART_PATH); pwd; helm lint;

help:  ## show this help.
	@echo "make targets:"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ": .*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""; echo "make vars (+defaults):"
	@grep -E '^[0-9a-zA-Z_-]+ \?=.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = " \\?\\= "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

publish-chart: ## publish chart in path 
	helm package $(UMBRELLA_CHART_PATH) -u && \
	curl -v -u $(HELM_USERNAME):$(HELM_PASSWORD) --upload-file *.tgz $(HELM_HOST)/repository/helm-chart/

install-chart: namespace namespace_sdp## install the helm chart on the namespace KUBE_NAMESPACE 
	helm install $(RELEASE_NAME) --dependency-update \
	--set minikube=$(MINIKUBE) \
	--set sdp-prototype.helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
	--set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
	--set tango-base.databaseds.domainTag=$(DOMAIN_TAG) \
	 $(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE) 

uninstall-chart: ## uninstall the helm chart on the namespace KUBE_NAMESPACE
	helm template  $(RELEASE_NAME) $(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE)  | kubectl delete -f - ; \
	helm uninstall  $(RELEASE_NAME) --namespace $(KUBE_NAMESPACE) 

reinstall-chart: uninstall-chart install-chart ## reinstall the  helm chart on the namespace KUBE_NAMESPACE

upgrade-chart: ## upgrade the helm chart on the namespace KUBE_NAMESPACE
	helm upgrade --set minikube=$(MINIKUBE) $(RELEASE_NAME) $(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE) 
	
quotas: ## delete and create the kubernetes namespace with quotas
	kubectl describe namespace $(KUBE_NAMESPACE) > /dev/null 2>&1 && kubectl delete namespace $(KUBE_NAMESPACE)
	kubectl create namespace $(KUBE_NAMESPACE)
	kubectl -n $(KUBE_NAMESPACE) apply -f resources/namespace_with_quotas.yaml

poddescribe: ## describe Pods executed from Helm chart
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l release=$(HELM_RELEASE) -o=name`; \
	do echo "---------------------------------------------------"; \
	echo "Describe for $${i}"; \
	echo kubectl -n $(KUBE_NAMESPACE) describe $${i}; \
	echo "---------------------------------------------------"; \
	kubectl -n $(KUBE_NAMESPACE) describe $${i}; \
	echo "---------------------------------------------------"; \
	echo ""; echo ""; echo ""; \
	done
podlogs: ## show Helm chart POD logs
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l release=$(RELEASE_NAME) -o=name`; \
	do \
	echo "---------------------------------------------------"; \
	echo "Logs for $${i}"; \
	echo kubectl -n $(KUBE_NAMESPACE) logs $${i}; \
	echo kubectl -n $(KUBE_NAMESPACE) get $${i} -o jsonpath="{.spec.initContainers[*].name}"; \
	echo "---------------------------------------------------"; \
	for j in `kubectl -n $(KUBE_NAMESPACE) get $${i} -o jsonpath="{.spec.initContainers[*].name}"`; do \
	RES=`kubectl -n $(KUBE_NAMESPACE) logs $${i} -c $${j} 2>/dev/null`; \
	echo "initContainer: $${j}"; echo "$${RES}"; \
	echo "---------------------------------------------------";\
	done; \
	echo "Main Pod logs for $${i}"; \
	echo "---------------------------------------------------"; \
	for j in `kubectl -n $(KUBE_NAMESPACE) get $${i} -o jsonpath="{.spec.containers[*].name}"`; do \
	RES=`kubectl -n $(KUBE_NAMESPACE) logs $${i} -c $${j} 2>/dev/null`; \
	echo "Container: $${j}"; echo "$${RES}"; \
	echo "---------------------------------------------------";\
	done; \
	echo "---------------------------------------------------"; \
	echo ""; echo ""; echo ""; \
	done
get_pods: ##lists the pods deploued for a particular namespace. @param: KUBE_NAMESPACE
	kubectl get pods -n $(KUBE_NAMESPACE)

get_versions: ## lists the container images used for particular pods
	kubectl get pods -l release=$(RELEASE_NAME) -n $(KUBE_NAMESPACE) -o jsonpath="{range .items[*]}{.metadata.name}{'\n'}{range .spec.containers[*]}{.name}{'\t'}{.image}{'\n\n'}{end}{'\n'}{end}{'\n'}"

set_context: ## Set current kubectl context. @param: KUBE_NAMESPACE
	kubectl config set-context $$(kubectl config current-context) --namespace $${NAMESPACE:-$(KUBE_NAMESPACE)}

get_status:
	kubectl get pod,svc,deployments,pv,pvc,ingress -n $(KUBE_NAMESPACE)

redeploy: delete_all deploy_ordered get_status
wait:
	pods=$$( kubectl get pods -n $(KUBE_NAMESPACE) -o=jsonpath="{range .items[*]}{.metadata.name}{' '}{end}" ) && \
	for pod in $$pods ;  do \
		phase=$$(kubectl get pod -n $(KUBE_NAMESPACE) $$pod -o=jsonpath='{.status.phase}'); \
		if [ "$$phase" = "Succeeded" ]; then \
			echo $$pod $$phase; else \
			kubectl wait --for=condition=Ready -n $(KUBE_NAMESPACE) pod/$$pod; \
		fi; \
	done

.PHONY: help
