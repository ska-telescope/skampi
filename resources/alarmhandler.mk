.PHONY: configure-alarmhandler

# This script configures the alarmhandler with the rules defined in text file.
configure-alarmhandler:
	curl https://gitlab.com/ska-telescope/ska-tango-alarmhandler/-/raw/0.1.1/charts/configuration_job.sh?inline=false > charts/configuration_job.sh
	curl https://gitlab.com/ska-telescope/ska-tango-alarmhandler/-/raw/0.1.1/charts/ska-tango-alarmhandler/data/alarm_configure.py?inline=false > resources/alarm_configure.py 
	bash ./charts/configuration_job.sh $(FILE_NAME) $(ALARM_HANDLER_FQDN)
	kubectl  --kubeconfig=$(KUBECONFIG) create configmap alarm-configure  --from-file $(FILE_NAME) --from-file resources/alarm_configure.py -o yaml -n $(KUBE_NAMESPACE) --dry-run=client | kubectl apply -f -
	kubectl  --kubeconfig=$(KUBECONFIG) create -f charts/configuration_job.yaml -n $(KUBE_NAMESPACE)
	kubectl  --kubeconfig=$(KUBECONFIG) wait --for=condition=Complete job/alarm-configuration -n $(KUBE_NAMESPACE)
	kubectl  --kubeconfig=$(KUBECONFIG) logs job.batch/alarm-configuration -n $(KUBE_NAMESPACE)
	rm charts/configuration_job.sh
	rm resources/alarm_configure.py 
	rm charts/configuration_job.yaml
