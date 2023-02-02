.PHONY: configure-archiver 


ARCHIVER_DBNAME ?= default_mvp_archiver_db # Deafult database name used if not provided by user while deploying the archiver


OPTION ?= "add"


# This script configures the archiver for attribute archival defined in yaml.
# It will run a job to configure attributes using yaml2archiving tool.
# Requries paramater KUBECONFIG,ATTR_CONFIG_FILE,KUBE_NAMESPACE
# ATTR_CONFIG_FILE= attribute configuration yaml file
configure-archiver:  ##configure attributes to archive
	curl -o charts/configuration_job.sh  https://gitlab.com/ska-telescope/ska-tango-archiver/-/raw/2.3.0/charts/configuration_job.sh?inline=false

	bash ./charts/configuration_job.sh $(OPTION)
	@if [ $(OPTION) = "remove" ]; then\
		make get_config;\
		python3 resources/remove_attributes.py --attr_conf=$(ATTR_CONFIG_FILE) --archived_file=attribute_configuration.yaml --conf_manager=$(CONFIG_MANAGER);\
		kubectl  --kubeconfig=$(KUBECONFIG) create configmap y2a-config --from-file attribute_configuration.yaml -o yaml -n $(KUBE_NAMESPACE) --dry-run=client | kubectl apply -f -;\
	else\
		kubectl  --kubeconfig=$(KUBECONFIG) create configmap y2a-config --from-file $(ATTR_CONFIG_FILE) -o yaml -n $(KUBE_NAMESPACE) --dry-run=client | kubectl apply -f - ;\
	fi

	kubectl  --kubeconfig=$(KUBECONFIG) create -f charts/configuration_job.yaml -n $(KUBE_NAMESPACE)
	-kubectl  --kubeconfig=$(KUBECONFIG) wait --for=condition=Complete job/add-configuration -n $(KUBE_NAMESPACE) --timeout=30s
	kubectl  --kubeconfig=$(KUBECONFIG) logs job.batch/add-configuration -n $(KUBE_NAMESPACE)
	rm charts/configuration_job.yaml
	rm charts/configuration_job.sh

#this job provides user archived attributes data
get_config:
	curl -o charts/get_configurations.sh   https://gitlab.com/ska-telescope/ska-tango-archiver/-/raw/master/charts/get_configurations.sh?inline=false
	bash ./charts/get_configurations.sh $(EVENT_SUBSCRIBER) $(TANGO_HOST)
	kubectl  --kubeconfig=$(KUBECONFIG) create -f charts/get_configurations.yaml -n $(KUBE_NAMESPACE)
	-kubectl  --kubeconfig=$(KUBECONFIG) wait --for=condition=Complete job/get-configuration --timeout=30s -n $(KUBE_NAMESPACE)
	kubectl  --kubeconfig=$(KUBECONFIG) logs job.batch/get-configuration -n $(KUBE_NAMESPACE) > attribute_configuration.yaml
	rm get_configurations.sh
	rm get_configurations.yaml

#Incase of error
#Requries parameter KUBECONFIG
delete_archiver_config_job:
	kubectl --kubeconfig=$(KUBECONFIG) delete job add-configuration

#Incase of error
#Requries parameter KUBECONFIG
delete_archiver_get_config_job:
	kubectl --kubeconfig=$(KUBECONFIG) delete job get-configuration

ARCHWIZ_IP=$(shell kubectl --kubeconfig=$(KUBECONFIG) get svc| grep archwizard | awk '{print $$4}')
ARCHWIZ_PORT=$(shell kubectl --kubeconfig=$(KUBECONFIG) get svc|grep archwizard |awk '{print $$5}'| cut -d ":" -f 1)
ARCHVIEWER_IP=$(shell kubectl --kubeconfig=$(KUBECONFIG) get svc| grep archviewer| awk '{print $$4}')
ARCHVIEWER_PORT=$(shell kubectl --kubeconfig=$(KUBECONFIG) get svc|grep archviewer |awk '{print $$5}'| cut -d ":" -f 1)
#VPN is required
#Provides ip and port for archwizard console
#Requries paramater KUBECONFIG
get_archwizard_link:
	$(info User must connect to VPN and click below link to access archwizard)
	@echo "http://$(ARCHWIZ_IP):$(ARCHWIZ_PORT)"
 

get_archviewer_link:
	$(info User must connect to VPN and click below link to access archviewer)	
	@echo "http://$(ARCHVIEWER_IP):$(ARCHVIEWER_PORT)"
