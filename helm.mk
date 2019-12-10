.PHONY: helm_init helm_deploy helm_delete helm_test helm helm_deploy_all helm_delete_all

HELM_RELEASE ?= $(shell make helm_ls | grep $(HELM_CHART) | cut -f1)

# stuff for backwards compatibility with helm v2
HELM_TILLER_PLUGIN := https://github.com/rimusz/helm-tiller
helm_is_v2 = $(strip $(shell helm version 2> /dev/null | grep SemVer:\"v2\.))
helm_install_shim = $(if $(helm_is_v2),--tiller-namespace $(KUBE_NAMESPACE),$(HELM_RELEASE))

# helm command to install a chart
# usage: $(call helm_install_cmd,$(HELM_CHART))
helm_install_cmd = helm install charts/$1 \
		   	$(if helm_is_v2,--tiller-namespace $(KUBE_NAMESPACE),$(HELM_RELEASE)) \
			--namespace="$(KUBE_NAMESPACE)" \
			--set display="$(DISPLAY)" \
			--set xauthority="$(XAUTHORITYx)" \
			--set ingress.hostname="$(INGRESS_HOST)" \
			--set ingress.nginx="$(USE_NGINX)" \
			--set tangoexample.debug="$(REMOTE_DEBUG)" \
			--set tests.enabled=true

# helm command to test a release
# usage: $(call helm_test_cmd)
helm_test_cmd = helm test $(HELM_RELEASE) $(if helm_is_v2,--logs --cleanup)

# helm command to delete a release
# usage: $(call helm_test_cmd)
helm_delete_cmd = helm delete $(HELM_RELEASE) $(if helm_is_v2,--purge)

# start the third-party tiller plugin if helmv2
define tiller-plugin-startup
$(if $(helm_is_v2), 
	@echo "+++ helmv2 detected. Starting third-party tiller plugin."
	@helm tiller start-ci $(KUBE_NAMESPACE)
	$(eval $(shell helm tiller env))
)
endef

define tiller-plugin-teardown
$(if $(helm_is_v2),
	@helm tiller stop
)
endef

# ensure third-party tiller plugin is installed for helm v2:
# tiller is provided locally as a helm plugin instead of on the cluster
helm_init:
	@echo "+++ Checking your helm version."
	@if [ -n '$(helm_is_v2)' ] && ! helm plugin list | grep -q tiller ; then \
		echo "+++ Detected helm v2 and no tiller. Installing local tiller plugin."; \
		helm plugin install $(HELM_TILLER_PLUGIN); \
	else \
		echo "+++ Everything seems fine." ;\
	fi

# deploys/releases a chart via helm
# usage make helm_deploy HELM_CHART=logging
helm_deploy: 
	$(tiller-plugin-startup)
	@echo "+++ Deploying chart '$(HELM_CHART)'
	@$(call helm_install_cmd,$(HELM_CHART))
	$(tiller-plugin-teardown)

# deploy all the charts
# usage: make helm_deploy_all
CHARTS := $(shell cd charts/ && ls -d *)
helm_deploy_all:
	$(tiller-plugin-startup)
	$(foreach chrt,$(CHARTS),$(call helm_install_cmd,$(chrt));)
	$(tiller-plugin-teardown)

helm_ls:
	$(tiller-plugin-startup)
	@helm ls
	$(tiller-plugin-teardown)


# tests a released helm chart. will deploy it if it isn't already there
# usage: make helm_test HELM_CHART=logging
helm_test: 
	$(tiller-plugin-startup)
	@$(call helm_test_cmd)
	$(tiller-plugin-teardown)

# deletes a deployed/released chart
# usage: make helm_delete
helm_delete:
	$(tiller-plugin-startup)
	@$(call helm_delete_cmd)
	$(tiller-plugin-teardown)

# deletes all releases specified by KUBE_NAMESPACE and then HELM_RELEASE
# usage: make helm_delete_all KUBE_NAMESPACE=test
helm_delete_all: delete_etcd
	$(tiller-plugin-startup)
	helm delete $$(helm ls -q --namespace=$(KUBE_NAMESPACE)) $(if $(helm_is_v2),--purge)
	$(tiller-plugin-teardown)

# wrapper for helm commands
# usage: make helm HELM_CMD="ls --all"
helm:
	$(tiller-plugin-startup)
	@helm $(HELM_CMD)
	$(tiller-plugin-teardown)

