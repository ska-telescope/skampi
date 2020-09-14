HELM_CHART ?= skampi# Publish skampi main chart only
# HELM_CHART ?= skampi/charts/tango-base# Publish one subchart - tango-base - only
# HELM_CHART ?= skampi/charts/*# Publish all SKAMPI subcharts
HELM_HOST ?= https://nexus.engageska-portugal.pt# 
HELM_PASSWORD ?=# not sure if we should publish this here?
HELM_USERNAME ?=# not sure if we should publish this here?
REPOSITORY_CACHE ?=

HELM_CHART_FULL_PATH := ./charts/$(HELM_CHART)

add_ska_helm_repo:
	helm repo add skatelescope $(HELM_HOST)/repository/helm-chart $(REPOSITORY_CACHE); \
	helm repo list; \
	helm repo update; \
	helm search repo skatelescope; \

publish-chart: ## Publish chart or charts specified by HELM_CHART on the SKA Helm Chart Repository
	if [[ -d "./repository" ]]; then rm -rf ./repository; fi; \
	mkdir -p repository; \
	make add_ska_helm_repo REPOSITORY_CACHE="--repository-cache ./repository/cache"; \
	helm package $(HELM_CHART_FULL_PATH) --destination ./repository; \
	helm repo index ./repository --merge ./repository/cache/skatelescope-index.yaml; \
	for file in ./repository/*; do \
		echo "checking if $${file} is a file"; \
		if [[ -f "$${file}" ]]; then \
			echo "uploading $${file##*/}"; \
		  curl -v -u $(HELM_USERNAME):$(HELM_PASSWORD) --upload-file $${file} $(HELM_HOST)/repository/helm-chart/$${file##*/}; \
		fi; \
	done; \
	helm search repo skatelescope; \
	helm repo update; \
	helm search repo skatelescope; 
	# rm -rf ./repository;

version-bump: ##Bump version of chart