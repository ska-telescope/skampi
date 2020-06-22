HELM_RELEASE ?= test# Helm release name
KUBE_NAMESPACE ?= integration# Kubernetes Namespace to use

install:
	helm install tango-base-$(HELM_RELEASE) ../../charts/skampi/charts/tango-base \
		--namespace $(KUBE_NAMESPACE) \
		--values values.yaml --wait --timeout=10m0s && \
		chart_name=$$(helm list -o=yaml | grep chart | awk '{print $$NF}') && \
		kubectl get all -l chart=$$chart_name

delete:
	helm delete tango-base-$(HELM_RELEASE)

describe:
	chart_name=$$(helm list -o=yaml | grep chart | awk '{print $$NF}') && \
	kubectl get all -l chart=$$chart_name

template_install:
	helm template tango-base-$(HELM_RELEASE) ../../charts/skampi/charts/tango-base \
		--namespace $(KUBE_NAMESPACE) \
		--values values.yaml --wait --timeout=10m0s | \
		tee test.yaml
