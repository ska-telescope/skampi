.PHONY: deploy-archiver delete-archiver test-archiver download

HELM_HOST ?= https://nexus.engageska-portugal.pt## helm host url https
DBHOST ?= 192.168.93.137 # DBHOST is the IP address for the cluster machine where archiver database is created
ARCHIVER_RELEASE ?= test
ARCHIVER_NAMESPACE ?= ska-archiver
CONFIGURE_ARCHIVER = test-configure-archiver # Test runner - run to completion the configuration job in K8s
DBNAME ?= default_mvp_archiver_db # Deafult database name used if not provided by user while deploying the archiver
ARCHIVER_CHART = https://nexus.engageska-portugal.pt/repository/helm-chart/ska-archiver-0.1.2.tgz

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

delete_archiver_namespace: ## delete the kubernetes namespace
	@if [ "default" == "$(ARCHIVER_NAMESPACE)" ] || [ "kube-system" == "$(ARCHIVER_NAMESPACE)" ]; then \
	echo "You cannot delete Namespace: $(ARCHIVER_NAMESPACE)"; \
	exit 1; \
	else \
	kubectl describe namespace $(ARCHIVER_NAMESPACE) && kubectl delete namespace $(ARCHIVER_NAMESPACE); \
	fi

# Checks if the Database name is provided by user while deploying the archiver otherwise gives the default name to the database
check-dbname: ## Check if database name is empty
	@if [ "$(DBNAME)" = "default_mvp_archiver_db" ]; then \
	echo "Archiver database name is not provided. Setting archiver database name to default value: default_mvp_archiver_db"; \
	fi

install-or-upgrade-archiver:
	helm history $(ARCHIVER_RELEASE) --namespace $(ARCHIVER_NAMESPACE) > /dev/null 2>&1; \
	K_DESC=$$? ; \
	if [ $$K_DESC -eq 1 ] ; \
	then make deploy-archiver ARCHIVER_NAMESPACE=$(ARCHIVER_NAMESPACE) DBNAME=$(DBNAME); \
	else make upgrade-archiver-chart; \
	fi

upgrade-archiver-chart:
	helm upgrade $(ARCHIVER_RELEASE) \
	--set global.minikube=$(MINIKUBE) \
	--set global.hostname=$(HOSTNAME) \
	--set global.dbname=$(DBNAME) \
	$(ARCHIVER_CHART) --namespace $(ARCHIVER_NAMESPACE);

#Ensure latest archiver chart from nexus is used for installtion 
# deploy-archiver: namespace-archiver check-dbname## install the helm chart on the namespace KUBE_NAMESPACE
deploy-archiver: namespace-archiver check-dbname## install the helm chart on the namespace KUBE_NAMESPACE
	helm repo add nexusPath https://nexus.engageska-portugal.pt/repository/helm-chart/; \
	helm repo update; \
	helm install $(ARCHIVER_RELEASE) \
		--set global.minikube=$(MINIKUBE) \
		--set global.hostname=$(DBHOST) \
		--set global.dbname=$(DBNAME) \
		$(ARCHIVER_CHART) --namespace $(ARCHIVER_NAMESPACE); 

# Deletes the ska-archiver deployment
delete-archiver: ## uninstall the helm chart on the namespace ARCHIVER_NAMESPACE
	@helm template  $(ARCHIVER_RELEASE) $(ARCHIVER_CHART) --namespace $(ARCHIVER_NAMESPACE) | kubectl delete -f - ; \
	helm uninstall  $(ARCHIVER_RELEASE) --namespace $(ARCHIVER_NAMESPACE)

show-archiver: ## show the helm chart
	@helm template $(ARCHIVER_RELEASE) charts/$(HELM_CHART)/ \
		--namespace $(ARCHIVER_NAMESPACE) \
		--set xauthority="$(XAUTHORITYx)" \
		--set display="$(DISPLAY)" 

# Get the database service name from archiver deployment and MVP deployment
get-service:
	$(eval DBMVPSERVICE := $(shell kubectl get svc -n $(KUBE_NAMESPACE) | grep 10000 |  cut -d " " -f 1)) \
	echo $(DBMVPSERVICE); \
	$(eval DBEDASERVICE := $(shell kubectl get svc -n $(ARCHIVER_NAMESPACE) | grep 10000 |  cut -d " " -f 1)) \
	echo $(DBEDASERVICE); \

# Runs a pod to execute a script. 
# This script configures the archiver for attribute archival defined in json file. Once script is executed, pod is deleted.
configure-archiver: get-service ##configure attributes to archive
		tar -c resources/archiver/ | \
		kubectl run $(CONFIGURE_ARCHIVER) \
		--namespace $(KUBE_NAMESPACE) -i --wait --restart=Never \
		--image-pull-policy=IfNotPresent \
		--image="nexus.engageska-portugal.pt/ska-docker/tango-dsconfig:1.5.0.3" -- \
		/bin/bash -c "sudo tar xv && \
		sudo curl https://gitlab.com/ska-telescope/ska-archiver/-/raw/master/charts/ska-archiver/data/configure_hdbpp.py -o /resources/archiver/configure_hdbpp.py && \
		cd /resources/archiver && \
		sudo python configure_hdbpp.py \
            --cm=tango://$(DBEDASERVICE).$(ARCHIVER_NAMESPACE).svc.cluster.local:10000/archiving/hdbpp/confmanager01 \
            --es=tango://$(DBEDASERVICE).$(ARCHIVER_NAMESPACE).svc.cluster.local:10000/archiving/hdbpp/eventsubscriber01 \
            --attrfile=configuation_file.json \
            --th=tango://$(DBEDASERVICE).$(ARCHIVER_NAMESPACE).svc.cluster.local:10000 \
			--ds=$(DBMVPSERVICE) \
			--ns=$(KUBE_NAMESPACE)" && \
		kubectl --namespace $(KUBE_NAMESPACE) delete pod $(CONFIGURE_ARCHIVER);

# get the tango host of archiver deployment
get_archiver_tango_host:
	$(eval ARCHIVER_TANGO_HOST := $(shell kubectl get svc -n $(ARCHIVER_NAMESPACE) | grep 10000 |  cut -d " " -f 1)) \
	echo $(ARCHIVER_TANGO_HOST);

#
# defines a function to copy the ./test-harness directory into the K8s TEST_RUNNER
# and then runs the requested make target in the container.
# capture the output of the test in a tar file
# stream the tar file base64 encoded to the Pod logs
#
archiver_k8s_test = tar -c post-deployment/ | \
		kubectl run $(TEST_RUNNER) \
		--namespace $(KUBE_NAMESPACE) -i --wait --restart=Never \
		--image-pull-policy=IfNotPresent \
		--image=$(IMAGE_TO_TEST) \
		--limits='cpu=1000m,memory=500Mi' \
		--requests='cpu=900m,memory=400Mi' \
		--env=ARCHIVER_TANGO_HOST=$2 \
		--env=ARCHIVER_NAMESPACE=$3 \
		--env=INGRESS_HOST=$(INGRESS_HOST) \
		$(PSI_LOW_PROXY_VALUES) -- \
		/bin/bash -c "mkdir skampi && tar xv --directory skampi --strip-components 1 --warning=all && cd skampi && \
		make SKUID_URL=skuid-skuid-$(KUBE_NAMESPACE)-$(HELM_RELEASE).$(KUBE_NAMESPACE).svc.cluster.local:9870 KUBE_NAMESPACE=$(KUBE_NAMESPACE) HELM_RELEASE=$(HELM_RELEASE) TANGO_HOST=$(TANGO_HOST) MARK='$(MARK)' FILE='$(FILE)' $1 && \
		tar -czvf /tmp/build.tgz build && \
		echo '~~~~BOUNDARY~~~~' && \
		cat /tmp/build.tgz | base64 && \
		echo '~~~~BOUNDARY~~~~'" \
		2>&1

archiver_k8s_test: get_archiver_tango_host smoketest## test the application on K8s
	$(call archiver_k8s_test,test,$(ARCHIVER_TANGO_HOST),$(ARCHIVER_NAMESPACE)); \
		status=$$?; \
		rm -fr build; \
		kubectl --namespace $(KUBE_NAMESPACE) logs $(TEST_RUNNER) | \
		perl -ne 'BEGIN {$$on=0;}; if (index($$_, "~~~~BOUNDARY~~~~")!=-1){$$on+=1;next;}; print if $$on % 2;' | \
		base64 -d | tar -xzf -; mkdir -p build; \
		python3 scripts/collect_k8s_logs.py $(KUBE_NAMESPACE) $(KUBE_NAMESPACE_SDP) \
			--pp build/k8s_pretty.txt --dump build/k8s_dump.txt --tests build/k8s_tests.txt; \
		kubectl --namespace $(KUBE_NAMESPACE) delete pod $(TEST_RUNNER); \
		exit $$status