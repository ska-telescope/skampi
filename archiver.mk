.PHONY: deploy-archiver delete-archiver test-archiver download

HELM_HOST ?= https://nexus.engageska-portugal.pt## helm host url https
MINIKUBE ?= true## Minikube or not
MARK ?= all
IMAGE_TO_TEST ?= $(DOCKER_REGISTRY_HOST)/$(DOCKER_REGISTRY_USER)/$(PROJECT):latest## docker image that will be run for testing purpose
TANGO_HOST ?= tango-host-databaseds-from-makefile-$(ARCHIVER_RELEASE):10000## TANGO_HOST is an input!
HOSTNAME ?= 192.168.93.137
# DBNAME ?= hdbpp
ARCHIVER_RELEASE ?= test
ARCHIVER_NAMESPACE ?= ska-archiver
CHARTS ?= ska-archiver

# no need of CHARTS
# CHARTS ?=  ## list of charts to be published on gitlab -- umbrella charts for testing purpose

CI_PROJECT_PATH_SLUG ?= ska-archiver
CI_ENVIRONMENT_SLUG ?= ska-archiver	

.DEFAULT_GOAL := help

# help:  ## show this help.
# 	@echo "Deploy EDA archiver service:"

# # as per discussion same namespace ($(KUBE_NAMESPACE)) is used for EDA pod deployments
# watch:
# 	watch kubectl get all,pv,pvc,ingress -n $(KUBE_NAMESPACE)

# watch:
# 	watch kubectl get all,pv,pvc,ingress -n $(KUBE_NAMESPACE)

namespace-archiver: ## create the kubernetes namespace
	@kubectl describe namespace $(ARCHIVER_NAMESPACE) > /dev/null 2>&1 ; \
		K_DESC=$$? ; \
		if [ $$K_DESC -eq 0 ] ; \
		then kubectl describe namespace $(ARCHIVER_NAMESPACE); \
		else kubectl create namespace $(ARCHIVER_NAMESPACE); \
		fi

delete_archiver: ## delete the kubernetes namespace
	@if [ "default" == "$(ARCHIVER_NAMESPACE)" ] || [ "kube-system" == "$(ARCHIVER_NAMESPACE)" ]; then \
	echo "You cannot delete Namespace: $(ARCHIVER_NAMESPACE)"; \
	exit 1; \ARCHIVER_NAMESPACE
	else \
	kubectl describe namespace $(ARCHIVER_NAMESPACE) && kubectl delete namespace $(ARCHIVER_NAMESPACE); \
	fi

dep-up: ## update dependencies for every charts in the env var CHARTS
	@for i in $(CHARTS); do \
	helm dependency update $${i}; \
	done;

check-dbname: ## Check if database name is empty
	@if [$(DBNAME) == ""]; then \
	echo "Database Name is not provided in make-install."; \
	exit 1; \
	fi

#Enable this target when latest ska-archiver chart is published on nexus
# deploy-archiver: namespace-archiver check-dbname## install the helm chart on the namespace KUBE_NAMESPACE
# 	helm repo add nexusPath https://nexus.engageska-portugal.pt/repository/helm-chart/; \
# 	helm repo update; \
# 	helm install $(ARCHIVER_RELEASE) \
# 		--set global.minikube=$(MINIKUBE) \
# 		--set global.hostname=$(HOSTNAME) \ -- no need to give as it is not changing
# 		--set global.dbname=$(DBNAME) \ -- this needs to be updated as per branch name when running from skampi
# 		https://nexus.engageska-portugal.pt/repository/helm-chart/archiver-0.2.11.tgz --namespace $(ARCHIVER_NAMESPACE); 

# delete-archiver: ## uninstall the helm chart on the namespace KUBE_NAMESPACE
# 	@helm template  $(ARCHIVER_RELEASE) https://nexus.engageska-portugal.pt/repository/helm-chart/archiver-0.2.11.tgz --set global.minikube=$(MINIKUBE) --set global.tango_host=$(TANGO_HOST) --namespace $(ARCHIVER_NAMESPACE) | kubectl delete -f - ; \
# 	helm uninstall  $(ARCHIVER_RELEASE) --namespace $(ARCHIVER_NAMESPACE)

#Enable this target when local ska-archiver chart is used for deployment
deploy-archiver: clean-archiver namespace-archiver check-dbname## install the helm chart on the namespace KUBE_NAMESPACE
	helm dependency update $(ARCHIVER_CHART_PATH);\
	helm install $(ARCHIVER_RELEASE) \
		--set global.minikube=$(MINIKUBE) \
		--set global.tango_host=$(TANGO_HOST) \
		--set global.hostname=$(HOSTNAME) \
		--set global.dbname=$(DBNAME) \
		$(ARCHIVER_CHART_PATH) --namespace $(ARCHIVER_NAMESPACE);

delete-archiver: ## uninstall the helm chart on the namespace KUBE_NAMESPACE
	@helm template  $(ARCHIVER_RELEASE) $(ARCHIVER_CHART_PATH) --set global.minikube=$(MINIKUBE) --set global.tango_host=$(TANGO_HOST) --namespace $(ARCHIVER_NAMESPACE) | kubectl delete -f - ; \
	helm uninstall  $(ARCHIVER_RELEASE) --namespace $(ARCHIVER_NAMESPACE)
	
clean-archiver: ## clean out references to chart tgz's
	@rm -f ./charts/ska-archiver/charts/*.tgz ./charts/ska-archiver/Chart.lock ./charts/ska-archiver/requirements.lock

# reinstall-archiver: delete-archiver deploy-archiver ## reinstall the  helm chart on the namespace KUBE_NAMESPACE

# upgrade-archiver-chart: ## upgrade the tmc-mid helm chart on the namespace tmcprototype
# 	helm upgrade --set minikube=$(MINIKUBE) $(ARCHIVER_RELEASE) $(ARCHIVER_CHART_PATH) --namespace $(KUBE_NAMESPACE) 

# test-archiver:

# wait:## wait for pods to be ready
# 	@echo "Waiting for pods to be ready"
# 	@date
# 	@kubectl -n $(KUBE_NAMESPACE) get pods
# 	@jobs=$$(kubectl get job --output=jsonpath={.items..metadata.name} -n $(KUBE_NAMESPACE)); kubectl wait job --for=condition=complete --timeout=240s $$jobs -n $(KUBE_NAMESPACE)
# 	@kubectl -n $(KUBE_NAMESPACE) wait --for=condition=ready -l app=tmc-prototype --timeout=240s pods
# 	@kubectl get pods -n $(KUBE_NAMESPACE)
# 	@date

# Error in --set
show: ## show the helm chart
	@helm template $(ARCHIVER_RELEASE) charts/$(HELM_CHART)/ \
		--namespace $(ARCHIVER_NAMESPACE) \
		--set xauthority="$(XAUTHORITYx)" \
		--set display="$(DISPLAY)" 

# Linting chart tmc-mid
archiver_chart_lint: ## lint check the helm chart
	@helm lint $(ARCHIVER_CHART_PATH) \
		--namespace $(ARCHIVER_NAMESPACE) 


