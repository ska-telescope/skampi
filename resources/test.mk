# CI_JOB_ID ?= local
# CLUSTER_TEST_NAMESPACE ?= ci-$(CI_JOB_ID)##Test namespace for cluster readiness tests
LOADBALANCER_IP?=$(shell kubectl cluster-info | grep Kubernetes | cut -d/ -f3 | sed -e 's,:.*,,g')

# Make target based test of cluster setup. This is done so that the SKAMPI user can test the basic
# functionality of the cluster by simply calling `make cluster-k8s-test`

cluster-k8s-test-pre: ## Setup of kubernetes resources for testing cluster
	kubectl config view --flatten --raw > tests/resources/assets/kubeconfig
	kubectl get nodes -o wide --kubeconfig=tests/resources/assets/kubeconfig
	kubectl version
	kubectl auth can-i create pods/exec
	
cluster-k8s-test-post: ## teardown step for testing cluster
	kubectl -n $(CLUSTER_TEST_NAMESPACE) delete deployments,pods,svc,daemonsets,replicasets,statefulsets,cronjobs,jobs,ingresses,configmaps,pvc --all --ignore-not-found
	kubectl delete pv pv-test-$(CLUSTER_TEST_NAMESPACE) --ignore-not-found
	kubectl delete ns $(CLUSTER_TEST_NAMESPACE) --ignore-not-found
	rm tests/resources/assets/kubeconfig || true

cluster-k8s-test-do: export CLUSTER_TEST_NAMESPACE=ci-$(CI_JOB_ID)
cluster-k8s-test-do: ## Test the cluster using pytest
	echo $$CLUSTER_TEST_NAMESPACE
	echo ${LOADBALANCER_IP}
	LOADBALANCER_IP=${LOADBALANCER_IP} pytest tests/unit/test_cluster_k8s.py

cluster-k8s-test: cluster-k8s-test-pre cluster-k8s-test-do cluster-k8s-test-post ## Test the cluster using make setup and teardown
