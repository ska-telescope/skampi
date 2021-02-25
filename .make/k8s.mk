template-chart: ## output the helm chart that will be installed with make upgrade-chart
	helm dependency update $(UMBRELLA_CHART_PATH); \
	helm template $(HELM_RELEASE) \
        --set tango-base.xauthority="$(XAUTHORITYx)" \
    	--set logging.ingress.hostname=$(INGRESS_HOST) \
        --set logging.ingress.nginx=$(USE_NGINX) \
        --set oet-scripts.ingress.hostname=$(INGRESS_HOST) \
        --set oet-scripts.ingress.nginx=$(USE_NGINX) \
        --set skuid.ingress.hostname=$(INGRESS_HOST) \
        --set skuid.ingress.nginx=$(USE_NGINX) \
        --set tango-base.ingress.hostname=$(INGRESS_HOST) \
        --set tango-base.ingress.nginx=$(USE_NGINX) \
        --set webjive.ingress.hostname=$(INGRESS_HOST) \
        --set webjive.ingress.nginx=$(USE_NGINX) \
		--set minikube=$(MINIKUBE) \
		--set global.minikube=$(MINIKUBE) \
		--set sdp.helmdeploy.namespace=$(KUBE_NAMESPACE_SDP) \
		--set sdp.tango-base.enabled=false \
		--set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
		--set oet-scripts.tangoDatabaseDS=$(TANGO_DATABASE_DS) \
		--set global.tango_host=$(TANGO_DATABASE_DS):10000 \
		--set tango-base.databaseds.domainTag=$(DOMAIN_TAG) \
		--set tango-base.ingress.hostname=$(INGRESS_HOST) \
		--set webjive.ingress.hostname=$(INGRESS_HOST) \
		--values $(VALUES) \
		$(UMBRELLA_CHART_PATH) --namespace $(KUBE_NAMESPACE);
