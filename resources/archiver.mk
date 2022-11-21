.PHONY: configure-archiver 


ARCHIVER_DBNAME ?= default_mvp_archiver_db # Deafult database name used if not provided by user while deploying the archiver
FILE_NAME ?= attribute_config.yaml



# This script configures the archiver for attribute archival defined in yaml.
# It will run a job to configure attributes using yaml2archiving tool.
#FILE_NAME = attribute configuration yaml file
configure-archiver:  ##configure attributes to archive
	curl https://gitlab.com/ska-telescope/ska-tango-archiver/-/raw/2.0.0/charts/configuration_job.yaml?inline=false > charts/configuration_job.yaml
ifneq ($(FILE_NAME),attribute_config.yaml)
	mv $(FILE_NAME) attribute_config.yaml
endif
	kubectl  --kubeconfig=$(KUBECONFIG) create configmap y2a-config  --from-file attribute_config.yaml -o yaml -n $(KUBE_NAMESPACE) --dry-run=client | kubectl apply -f -
	kubectl  --kubeconfig=$(KUBECONFIG) create -f charts/configuration_job.yaml -n $(KUBE_NAMESPACE)
	kubectl  --kubeconfig=$(KUBECONFIG) wait --for=condition=Complete job/archiver-configuration -n $(KUBE_NAMESPACE)
	kubectl  --kubeconfig=$(KUBECONFIG) logs job.batch/archiver-configuration -n $(KUBE_NAMESPACE)
	rm charts/configuration_job.yaml

#Incase of error
delete_archiver_config_job:
	kubectl --kubeconfig=$(KUBECONFIG) delete job archiver-configuration