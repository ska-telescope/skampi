.PHONY: k8s_test smoketest template_tests tango_rest_ingress_check

CI_JOB_ID?=local
#
# IMAGE_TO_TEST defines the tag of the Docker image to test
IMAGE_TO_TEST = artefact.skao.int/ska-tango-images-pytango-builder-alpine:0.3.0## docker image that will be run for testing purpose
# Test runner - run to completion job in K8s
TEST_RUNNER = test-makefile-runner-$(CI_JOB_ID)##name of the pod running the k8s_tests
#
# defines a function to copy the ./test-harness directory into the K8s TEST_RUNNER
# and then runs the requested make target in the container.
# capture the output of the test in a build folder inside the container
#
MARK ?= fast## this variable allow the mark parameter in the pytest
FILE ?= ##this variable allow to execution of a single file in the pytest
SLEEPTIME ?= 1200s ##amount of sleep time for the smoketest target
COUNT ?= 1## amount of repetition for pytest-repeat
BIGGER_THAN ?= ## get_size_images parameter: if not empty check if images are bigger than this (in MB)

TELESCOPE = 'SKA-Mid'
CENTRALNODE = 'ska_mid/tm_central/central_node'
SUBARRAY = 'ska_mid/tm_subarray_node'
# Define environmenvariables required by OET
ifneq (,$(findstring low,$(KUBE_NAMESPACE)))
	TELESCOPE = 'SKA-Low'
	CENTRALNODE = 'ska_low/tm_central/central_node'
	SUBARRAY = 'ska_low/tm_subarray_node'
endif

PUBSUB = true

# Bash script to run inside the testing pod. This does the following:
# 1. Create a FIFO to push the results to
# 2. Extract "post-deployment" folder, the contents of which should be
#    piped in through stdin
# 3. Invoke post-deployment/Makefile
# 4. Pipe results back through the FIFO (including make's return code)
k8s_test_command = /bin/bash -c "\
	mkfifo results-pipe && tar zx --warning=all && cd tests\
        pip install -qUr test_requirements.txt && \
	make -s SKUID_URL=ska-ser-skuid-$(HELM_RELEASE)-svc.$(KUBE_NAMESPACE).svc.cluster.local:9870 \
		KUBE_NAMESPACE=$(KUBE_NAMESPACE) \
		HELM_RELEASE=$(HELM_RELEASE) \
		TANGO_HOST=$(TANGO_HOST) \
		CI_JOB_TOKEN=$(CI_JOB_TOKEN) \
		MARK='$(MARK)' \
		COUNT=$(COUNT) \
		FILE='$(FILE)' \
		SKA_TELESCOPE=$(TELESCOPE) \
		CENTRALNODE_FQDN=$(CENTRALNODE) \
		SUBARRAYNODE_FQDN_PREFIX=$(SUBARRAY) \
		OET_READ_VIA_PUBSUB=$(PUBSUB) \
		JIRA_AUTH=$(JIRA_AUTH) \
		CAR_RAW_USERNAME=$(RAW_USER) \
		CAR_RAW_PASSWORD=$(RAW_PASS) \
		CAR_RAW_REPOSITORY_URL=$(RAW_HOST) \
		$1; \
	echo \$$? > build/status; pip list > build/pip_list.txt; \
	tar zcf results-pipe build"

k8s_test_runner = $(TEST_RUNNER) -n $(KUBE_NAMESPACE)
k8s_test_kubectl_run_args = \
	$(k8s_test_runner) --restart=Never \
	--image-pull-policy=IfNotPresent --image=$(IMAGE_TO_TEST) \
	--env=INGRESS_HOST=$(INGRESS_HOST) $(PSI_LOW_PROXY_VALUES)

# Set up of the testing pod. This goes through the following steps:
# 1. Create the pod, piping the contents of post-deployment in. This is
#    run in the background, with stdout left attached - albeit slightly
#    de-cluttered by removing pytest's live logs.
# 2. In parallel we wait for the testing pod to become ready.
# 3. Once it is there, we attempt to pull the results from the FIFO queue.
#    This blocks until the testing pod script writes it (see above).
k8s_test: ## test the application on K8s
	@rm -fr build; mkdir build

	@echo "TESTING THE DEPLOYMENT"
	@echo "$(k8s_test_kubectl_run_args)"
	@( tar -cz ./ \
	  | kubectl run $(k8s_test_kubectl_run_args) -iq -- $(k8s_test_command) 2>&1 \
	  | grep -vE "^(1\||-+ live log)" --line-buffered &); \
	sleep 1; \
	kubectl wait pod $(k8s_test_runner) --for=condition=ready --timeout=1m && \
		(kubectl exec $(k8s_test_runner) -- cat results-pipe | tar xz); \
	\
	(kubectl get all -n $(KUBE_NAMESPACE) -o yaml > build/k8s_manifest.txt); \
	python3 scripts/collect_k8s_logs.py $(KUBE_NAMESPACE) $(KUBE_NAMESPACE_SDP) \
		--pp build/k8s_pretty.txt --dump build/k8s_dump.txt --tests build/k8s_tests.txt; \
	kubectl --namespace $(KUBE_NAMESPACE) delete pod $(TEST_RUNNER)

	exit `cat build/status`

smoketest: wait## wait for pods to be ready and jobs to be completed

get_size_images: ## get a list of images together with their size (both local and compressed) in the namespace KUBE_NAMESPACE
	@for p in `kubectl get pods -n $(KUBE_NAMESPACE) -o jsonpath="{range .items[*]}{range .spec.containers[*]}{.image}{'\n'}{end}{range .spec.initContainers[*]}{.image}{'\n'}{end}{end}" | sort | uniq`; do \
		docker pull $$p > /dev/null; \
		B=`docker inspect -f "{{ .Size }}" $$p`; \
		if [ ! -z "$$BIGGER_THAN" ] ; then \
			MB=$$(((B)/1024/1024)); \
			if [ $$MB -lt $$BIGGER_THAN ] ; then \
				continue; \
			fi; \
		fi; \
		MB=$$(((B)/1000000)); \
		cB=`docker manifest inspect $$p | jq '[.layers[].size] | add'`; \
		cMB=$$(((cB)/1000000)); \
		echo $$p: $$B B \($$MB MB\), $$cB \($$cMB MB\); \
	done;
