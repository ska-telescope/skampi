.PHONY: deploy-archiver delete-archiver test-archiver download

HELM_HOST ?= https://nexus.engageska-portugal.pt## helm host url https
MINIKUBE ?= true## Minikube or not
MARK ?= all
IMAGE_TO_TEST ?= $(DOCKER_REGISTRY_HOST)/$(DOCKER_REGISTRY_USER)/$(PROJECT):latest## docker image that will be run for testing purpose
# TANGO_DATABASE_DS ?= databaseds-tango-base-$(ARCHIVER_RELEASE) ## Stable name for the Tango DB , as per SKAMPI variable name
# TANGO_DATABASE_DS ?= tango-host-databaseds-$(ARCHIVER_RELEASE) ## Stable name for the Tango DB
TANGO_HOST ?= tango-host-databaseds-from-makefile-$(ARCHIVER_RELEASE):10000## TANGO_HOST is an input!
HOSTNAME ?= ska-archiver-hdbppdb-db
DBNAME ?= hdbpp
ARCHIVER_RELEASE ?= archivertest

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


# clean job has to be updated to only clean archiver charts and not other SKAMPI charts
# clean: ## clean out references to chart tgz's
# 	@rm -f ./charts/*/charts/*.tgz ./charts/*/Chart.lock ./charts/*/requirements.lock ./repository/*

# watch:
# 	watch kubectl get all,pv,pvc,ingress -n $(KUBE_NAMESPACE)

# namespace: ## create the kubernetes namespace
# 	@kubectl describe namespace $(KUBE_NAMESPACE) > /dev/null 2>&1 ; \
# 		K_DESC=$$? ; \
# 		if [ $$K_DESC -eq 0 ] ; \
# 		then kubectl describe namespace $(KUBE_NAMESPACE); \
# 		else kubectl create namespace $(KUBE_NAMESPACE); \
# 		fi

# namespace_sdp: ## create the kubernetes namespace for SDP dynamic deployments
# 	@kubectl describe namespace $(SDP_KUBE_NAMESPACE) > /dev/null 2>&1 ; \
#  	K_DESC=$$? ; \
# 	if [ $$K_DESC -eq 0 ] ; \
# 	then kubectl describe namespace $(SDP_KUBE_NAMESPACE) ; \
# 	else kubectl create namespace $(SDP_KUBE_NAMESPACE); \
# 	fi

# delete_namespace: ## delete the kubernetes namespace
# 	@if [ "default" == "$(KUBE_NAMESPACE)" ] || [ "kube-system" == "$(KUBE_NAMESPACE)" ]; then \
# 	echo "You cannot delete Namespace: $(KUBE_NAMESPACE)"; \
# 	exit 1; \
# 	else \
# 	kubectl describe namespace $(KUBE_NAMESPACE) && kubectl delete namespace $(KUBE_NAMESPACE); \
# 	fi

# delete_namespace-sdp: ## delete the kubernetes namespace
# 	@if [ "default" == "$(SDP_KUBE_NAMESPACE)" ] || [ "kube-system" == "$(SDP_KUBE_NAMESPACE)" ]; then \
# 	echo "You cannot delete Namespace: $(SDP_KUBE_NAMESPACE)"; \
# 	exit 1; \
# 	else \
# 	kubectl describe namespace $(SDP_KUBE_NAMESPACE) && kubectl delete namespace $(SDP_KUBE_NAMESPACE); \
# 	fi

# check if required
# dep-up: ## update dependencies for every charts in the env var CHARTS
# 	@cd charts; \
# 	for i in $(CHARTS); do \
# 	echo "+++ Updating $${i} chart +++"; \
# 	helm dependency update $${i}; \
# 	done; 
	

# download:

#     echo "downloading charts"; \
# 	helm pull [https://nexus.engageska-portugal.pt/repository/helm-chart/archiver-0.2.11.tgz] [--untar = true] \
#     echo "Succeeded";

clean-archiver: ## clean out references to chart tgz's
	@rm -f ./charts/ska-archiver/charts/*.tgz ./charts/ska-archiver/Chart.lock ./charts/ska-archiver/requirements.lock

deploy-archiver: clean-archiver namespace namespace_sdp ## install the helm chart on the namespace KUBE_NAMESPACE
	helm dependency update $(ARCHIVER_CHART_PATH); \
	@sed -e 's/CI_PROJECT_PATH_SLUG/$(CI_PROJECT_PATH_SLUG)/' ci-values.yaml > generated_values.yaml; \
	sed -e 's/CI_ENVIRONMENT_SLUG/$(CI_ENVIRONMENT_SLUG)/' generated_values.yaml > values.yaml; \
	helm install $(ARCHIVER_RELEASE) \
		--set global.minikube=$(MINIKUBE) \
		--set global.tango_host=$(TANGO_HOST) \
		--set global.hostname=$(HOSTNAME) \
		--set global.dbname=$(DBNAME) \
		--values values.yaml \
		$(ARCHIVER_CHART_PATH) --namespace $(KUBE_NAMESPACE); 

delete-archiver: ## uninstall the helm chart on the namespace KUBE_NAMESPACE
	@helm template  $(ARCHIVER_RELEASE) $(ARCHIVER_CHART_PATH) --set global.minikube=$(MINIKUBE) --set global.tango_host=$(TANGO_HOST) --namespace $(KUBE_NAMESPACE) | kubectl delete -f - ; \
	helm uninstall  $(ARCHIVER_RELEASE) --namespace $(KUBE_NAMESPACE)

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
		--namespace $(KUBE_NAMESPACE) \
		--set xauthority="$(XAUTHORITYx)" \
		--set display="$(DISPLAY)" 

# Linting chart tmc-mid
archiver_chart_lint: ## lint check the helm chart
	@helm lint $(ARCHIVER_CHART_PATH) \
		--namespace $(KUBE_NAMESPACE) 


