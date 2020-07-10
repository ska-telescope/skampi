HELM_HOST ?= https://nexus.engageska-portugal.pt

namespace: ## create the kubernetes namespace
	@kubectl describe namespace tango-grafana > /dev/null 2>&1 ; \
		K_DESC=$$? ; \
		if [ $$K_DESC -eq 0 ] ; \
		then kubectl describe namespace tango-grafana ; \
		else kubectl create namespace tango-grafana; \
		fi

install-chart: namespace ## install the tango-grafana helm chart on the namespace tango-grafana
	helm repo add ska https://nexus.engageska-portugal.pt/repository/helm-chart/
	helm install tango-grafana ska/tango-grafana --set minikube=true --namespace tango-grafana

uninstall-chart: ## uninstall the tango-grafana helm chart on the namespace tango-grafana
	helm uninstall tango-grafana --namespace tango-grafana

reinstall-chart: uninstall-chart install-chart ## reinstall the tango-grafana helm chart on the namespace tango-grafana

upgrade-chart: ## upgrade the tango-grafana helm chart on the namespace tango-grafana
	helm upgrade --set minikube=$(MINIKUBE) tango-grafana --namespace tango-grafana