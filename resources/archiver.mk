.PHONY: configure-archiver 


ARCHIVER_DBNAME ?= default_mvp_archiver_db # Deafult database name used if not provided by user while deploying the archiver
ATTR_CONFIG_FILE ?= attribute_config.yaml



# This script configures the archiver for attribute archival defined in yaml.
# It will run a job to configure attributes using yaml2archiving tool.
# Requries paramater KUBECONFIG,ATTR_CONFIG_FILE,KUBE_NAMESPACE
# ATTR_CONFIG_FILE= attribute configuration yaml file
configure-archiver:  ##configure attributes to archive
	curl https://gitlab.com/ska-telescope/ska-tango-archiver/-/raw/2.2.1/charts/configuration_job.yaml?inline=false > charts/configuration_job.yaml
ifneq ($(ATTR_CONFIG_FILE),attribute_config.yaml)
	mv $(ATTR_CONFIG_FILE) attribute_config.yaml
endif
	kubectl  --kubeconfig=$(KUBECONFIG) create configmap y2a-config  --from-file attribute_config.yaml -o yaml -n $(KUBE_NAMESPACE) --dry-run=client | kubectl apply -f -
	kubectl  --kubeconfig=$(KUBECONFIG) create -f charts/configuration_job.yaml -n $(KUBE_NAMESPACE)
	kubectl  --kubeconfig=$(KUBECONFIG) wait --for=condition=Complete job/archiver-configuration -n $(KUBE_NAMESPACE)
	kubectl  --kubeconfig=$(KUBECONFIG) logs job.batch/archiver-configuration -n $(KUBE_NAMESPACE)
	rm charts/configuration_job.yaml

#Incase of error
#Requries parameter KUBECONFIG
delete_archiver_config_job:
	kubectl --kubeconfig=$(KUBECONFIG) delete job archiver-configuration


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
