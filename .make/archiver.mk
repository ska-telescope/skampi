.PHONY: check-archiver-dbname configure-archiver get-service download

HELM_HOST ?= https://nexus.engageska-portugal.pt## helm host url https
ARCHIVER_RELEASE ?= test
ARCHIVER_NAMESPACE ?= ska-archiver
CONFIGURE_ARCHIVER = test-configure-archiver # Test runner - run to completion the configuration job in K8s
# ARCHIVER_CHART = https://nexus.engageska-portugal.pt/repository/helm-chart/ska-archiver-0.1.2.tgz
ARCHIVER_DBNAME ?= default_mvp_archiver_db # Deafult database name used if not provided by user while deploying the archiver
# ARCHIVER_DBHOST ?= 192.168.99.229 # ARCHIVER_DBHOST is the IP address for the cluster machine where archiver database is created
# ARCHIVER_PORT ?= 3306
# ARCHIVER_DBUSER ?= eda_admin
# ARCHIVER_DBPASSWORD ?= @v3ng3rs@ss3mbl3
ARCHIVER_CONFIG_FILE ?= $(DEPLOYMENT_CONFIGURATION)/configuration.json## archiver attribute configure json file for MVP-mid to work with

# Checks if the Database name is provided by user while deploying the archiver and notifies the user
check-archiver-dbname:
	@if [ "$(ARCHIVER_DBNAME)" = "default_mvp_archiver_db" ]; then \
	echo "Archiver database name is not provided. Setting archiver database name to default value: default_mvp_archiver_db"; \
	fi

# Get the database service name from MVP deployment
get-service:
	$(eval DBMVPSERVICE := $(shell kubectl get svc -n $(KUBE_NAMESPACE) | grep 10000 |  cut -d " " -f 1)) \
	echo $(DBMVPSERVICE);

# Runs a pod to execute a script. 
# This script configures the archiver for attribute archival defined in json file. Once script is executed, pod is deleted.
configure-archiver:  get-service ##configure attributes to archive
		tar -c resources/archiver/ | \
		kubectl run $(CONFIGURE_ARCHIVER) \
		--namespace $(KUBE_NAMESPACE) -i --wait --restart=Never \
		--image-pull-policy=IfNotPresent \
		--image="nexus.engageska-portugal.pt/ska-docker/tango-dsconfig:1.5.0.3" -- \
		/bin/bash -c "sudo tar xv && \
		sudo curl https://gitlab.com/ska-telescope/ska-archiver/-/raw/master/charts/ska-archiver/data/configure_hdbpp.py -o /resources/archiver/configure_hdbpp.py && \
		cd /resources/archiver && \
		ls -all && \
		sudo python configure_hdbpp.py \
            --cm=tango://$(TANGO_DATABASE_DS):10000/archiving/hdbpp/confmanager01 \
            --es=tango://$(TANGO_DATABASE_DS):10000/archiving/hdbpp/eventsubscriber01 \
            --attrfile=$(ARCHIVER_CONFIG_FILE) \
            --th=tango://$(TANGO_DATABASE_DS):10000 \
			--ds=$(DBMVPSERVICE) \
			--ns=$(KUBE_NAMESPACE)" && \
		kubectl --namespace $(KUBE_NAMESPACE) delete pod $(CONFIGURE_ARCHIVER);
