.PHONY: deploy-archiver delete-archiver test-archiver download

HELM_HOST ?= https://nexus.engageska-portugal.pt## helm host url https
MINIKUBE ?= true## Minikube or not
MARK ?= all
TANGO_HOST ?= tango-host-databaseds-from-makefile-$(ARCHIVER_RELEASE):10000## TANGO_HOST is an input!
HOSTNAME = 192.168.93.137
ARCHIVER_RELEASE ?= test
ARCHIVER_NAMESPACE ?= ska-archiver
CONFIGURE_ARCHIVER = test-configure-archiver-$(CI_JOB_ID)
DBNAME ?= default_mvp_archiver_db

CI_PROJECT_PATH_SLUG ?= ska-archiver
CI_ENVIRONMENT_SLUG ?= ska-archiver	

.DEFAULT_GOAL := help-archiver

help-archiver:  ## show this help.
	@echo "Deploy EDA archiver service:"

watch-archiver:
	watch kubectl get all,pv,pvc,ingress -n $(ARCHIVER_NAMESPACE)

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


check-dbname: ## Check if database name is empty
	@if [ "$(DBNAME)" = "default_mvp_archiver_db" ]; then \
	echo "Archiver database name is not provided. Setting archiver database name to default value: default_mvp_archiver_db"; \
	fi

#Ensure latest archiver chart from nexus is used for installtion 
deploy-archiver: namespace-archiver check-dbname## install the helm chart on the namespace KUBE_NAMESPACE
	helm repo add nexusPath https://nexus.engageska-portugal.pt/repository/helm-chart/; \
	helm repo update; \
	helm install $(ARCHIVER_RELEASE) \
		--set global.minikube=$(MINIKUBE) \
		--set global.hostname=$(HOSTNAME) \
		--set global.dbname=$(DBNAME) \
		https://nexus.engageska-portugal.pt/repository/helm-chart/ska-archiver-0.1.1.tgz --namespace $(ARCHIVER_NAMESPACE); 

delete-archiver: ## uninstall the helm chart on the namespace KUBE_NAMESPACE
	@helm template  $(ARCHIVER_RELEASE) https://nexus.engageska-portugal.pt/repository/helm-chart/ska-archiver-0.1.1.tgz --set global.minikube=$(MINIKUBE) --set global.tango_host=$(TANGO_HOST) --namespace $(ARCHIVER_NAMESPACE) | kubectl delete -f - ; \
	helm uninstall  $(ARCHIVER_RELEASE) --namespace $(ARCHIVER_NAMESPACE)

show-archiver: ## show the helm chart
	@helm template $(ARCHIVER_RELEASE) charts/$(HELM_CHART)/ \
		--namespace $(ARCHIVER_NAMESPACE) \
		--set xauthority="$(XAUTHORITYx)" \
		--set display="$(DISPLAY)" 

configure-archiver:  ##configure attributes to archive
		tar -c resources/archiver/ | \
		kubectl run $(CONFIGURE_ARCHIVER) \
		--namespace $(KUBE_NAMESPACE)  -i --wait --restart=Never \
		--image-pull-policy=IfNotPresent \
		--image="nexus.engageska-portugal.pt/ska-docker/tango-dsconfig:1.5.0.3" -- \
		/bin/bash -c "echo 'inside archivr container' && \
		sudo tar xv && \
		sudo curl https://gitlab.com/ska-telescope/ska-archiver/-/raw/master/charts/ska-archiver/data/configure_hdbpp.py -o /resources/archiver/configure_hdbpp.py && \
		cd /resources/archiver && \
		sudo python configure_hdbpp.py \
            --cm=tango://databaseds-tango-base-test.$(ARCHIVER_NAMESPACE).svc.cluster.local:10000/archiving/hdbpp/confmanager01 \
            --es=tango://databaseds-tango-base-test.$(ARCHIVER_NAMESPACE).svc.cluster.local:10000/archiving/hdbpp/eventsubscriber01 \
            --attrfile=configuation_file.json \
            --th=tango://databaseds-tango-base-test.$(ARCHIVER_NAMESPACE).svc.cluster.local:10000" && \
		kubectl --namespace $(KUBE_NAMESPACE) delete pod $(CONFIGURE_ARCHIVER); 




