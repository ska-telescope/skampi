.PHONY: k8s_test smoketest template_tests tango_rest_ingress_check

#
# IMAGE_TO_TEST defines the tag of the Docker image to test
#
#nexus.engageska-portugal.pt/ska-docker/tango-vscode:0.2.6-dirty
IMAGE_TO_TEST ?= nexus.engageska-portugal.pt/ska-docker/tango-vscode:0.2.7## docker image that will be run for testing purpose
# Test runner - run to completion job in K8s
TEST_RUNNER = test-makefile-runner-$(CI_JOB_ID)-$(KUBE_NAMESPACE)-$(HELM_RELEASE)##name of the pod running the k8s_tests
#
# defines a function to copy the ./test-harness directory into the K8s TEST_RUNNER
# and then runs the requested make target in the container.
# capture the output of the test in a build folder inside the container 
# 
TESTING_ACCOUNT = testing-pod ## this is the service acount name that is used by testing pod enabling it roles to manipulate k8 
TANGO_HOST = databaseds-tango-base-$(HELM_RELEASE):10000
MARK ?= fast## this will allow to add the mark parameter of pytest 
SLEEPTIME ?= 30s ##amount of sleep time for the smoketest target

#
# defines a function to copy the ./test-harness directory into the K8s TEST_RUNNER
# and then runs the requested make target in the container.
# capture the output of the test in a tar file
# stream the tar file base64 encoded to the Pod logs
# 
k8s_test = tar -c post-deployment/ | \
		kubectl run $(TEST_RUNNER) \
		--namespace $(KUBE_NAMESPACE) -i --wait --restart=Never \
		--image-pull-policy=IfNotPresent \
		--image=$(IMAGE_TO_TEST) -- \
		/bin/bash -c "mkdir skampi && tar xv --directory skampi --strip-components 1 --warning=all && cd skampi && \
		make KUBE_NAMESPACE=$(KUBE_NAMESPACE) HELM_RELEASE=$(HELM_RELEASE) TANGO_HOST=$(TANGO_HOST) MARK=$(MARK) TEST_RUN_SPEC=$(TEST_RUN_SPEC) $1 && \
		tar -czvf /tmp/build.tgz build && \
		echo '~~~~BOUNDARY~~~~' && \
		cat /tmp/build.tgz | base64 && \
		echo '~~~~BOUNDARY~~~~'" \
		2>&1

# run the test function
# save the status
# clean out build dir
# print the logs minus the base64 encoded payload
# pull out the base64 payload and unpack build/ dir
# base64 payload is given a boundary "~~~~BOUNDARY~~~~" and extracted using perl
# clean up the run to completion container
# exit the saved status
k8s_test: clear_sdp_config smoketest## test the application on K8s
	$(call k8s_test,test); \
		status=$$?; \
		rm -fr build; \
		kubectl --namespace $(KUBE_NAMESPACE) logs $(TEST_RUNNER) | \
		perl -ne 'BEGIN {$$on=0;}; if (index($$_, "~~~~BOUNDARY~~~~")!=-1){$$on+=1;next;}; print if $$on % 2;' | \
		base64 -d | tar -xzf -; \
		kubectl --namespace $(KUBE_NAMESPACE) delete pod $(TEST_RUNNER); \
		exit $$status

TEST_RUN_SPEC=spec2.yaml
k8s_multiple_test_runs: enable_test_auth
	$(call k8s_test,test_multiple_runs); \
		status=$$?; \
		rm -fr build; \
		kubectl --namespace $(KUBE_NAMESPACE) logs $(TEST_RUNNER) | \
		perl -ne 'BEGIN {$$on=0;}; if (index($$_, "~~~~BOUNDARY~~~~")!=-1){$$on+=1;next;}; print if $$on % 2;' | \
		base64 -d | tar -xzf -; \
		kubectl --namespace $(KUBE_NAMESPACE) delete pod $(TEST_RUNNER); \
		exit $$status

clear_sdp_config:
	kubectl exec -n $(KUBE_NAMESPACE) sdp-proto-console-0 -- sdpcfg delete -R /

smoketest: ## check that the number of waiting containers is zero (10 attempts, wait time 30s).
	@echo "Smoke test START"; \
	n=10; \
	while [ $$n -gt 0 ]; do \
		waiting=`kubectl get pods -n $(KUBE_NAMESPACE) -o=jsonpath='{.items[*].status.containerStatuses[*].state.waiting.reason}' | wc -w`; \
		echo "Waiting containers=$$waiting"; \
		if [ $$waiting -ne 0 ]; then \
			echo "Waiting $(SLEEPTIME) for pods to become running...#$$n"; \
			sleep $(SLEEPTIME); \
		fi; \
		if [ $$waiting -eq 0 ]; then \
			echo "Smoke test SUCCESS"; \
			exit 0; \
		fi; \
		if [ $$n -eq 1 ]; then \
			waiting=`kubectl get pods -n $(KUBE_NAMESPACE) -o=jsonpath='{.items[*].status.containerStatuses[*].state.waiting.reason}' | wc -w`; \
			echo "Smoke test FAILS"; \
			echo "Found $$waiting waiting containers: "; \
			kubectl get pods -n $(KUBE_NAMESPACE) -o=jsonpath='{range .items[*].status.containerStatuses[?(.state.waiting)]}{.state.waiting.message}{"\n"}{end}'; \
			exit 1; \
		fi; \
		n=`expr $$n - 1`; \
	done

disable_test_auth = helm delete testing-auth

enable_test_auth:
	@helm upgrade --install testing-auth post-deployment/resources/testing_auth \
		--set namespace=$(KUBE_NAMESPACE) \
		--set accountName=$(TESTING_ACCOUNT)

disable_test_auth:
	@$(call disable_test_auth)

template_tests:
	rc=0; \
	for chrt in `ls charts/`; do \
	helm unittest -f template_tests/*_test.yaml charts/$$chrt \
		|| rc=2 && continue; \
	done; \
	exit $$rc

tango_rest_ingress_check:  ## curl test Tango REST API - https://tango-controls.readthedocs.io/en/latest/development/advanced/rest-api.html#tango-rest-api-implementations
	@echo "---------------------------------------------------"
	@echo "Test HTTP:"; echo ""
	curl -u "tango-cs:tango" -XGET http://tango.rest.$(INGRESS_HOST)/tango/rest/rc4/hosts/databaseds-tango-base-$(HELM_RELEASE)/10000 | json_pp
	# @echo "", echo ""
	# @echo "---------------------------------------------------"
	# @echo "Test HTTPS:"; echo ""
	# curl -k -u "tango-cs:tango" -XGET https://tango.rest.$(INGRESS_HOST)/tango/rest/rc4/hosts/databaseds-tango-base-$(HELM_RELEASE)/10000 | json_pp
	# @echo ""

oet_podname = $(shell kubectl get pods -l app=rest-oet-$(HELM_RELEASE) -o=jsonpath='{..metadata.name}')
sut_cdm_ver= $(shell kubectl exec -it $(oet_podname) pip list | grep "cdm-shared-library" | awk ' {print $$2}' | awk 'BEGIN { FS = "+" } ; {print $$1}')
sut_cdm_cur_ver=$(shell grep "cdm-shared-library" post-deployment/SUT_requirements.txt | awk 'BEGIN { FS = "==" } ; {print $$2}')
sut_oet_ver = $(shell kubectl exec -it $(oet_podname) pip list | grep "observation-execution-tool" | awk ' {print $$2}' | awk 'BEGIN { FS = "+" } ; {print $$1}')
sut_oet_cur_ver=$(shell grep "observation-execution-tool" post-deployment/SUT_requirements.txt | awk 'BEGIN { FS = "==" } ; {print $$2}')

check_oet_packages:
	@echo "MVP is based on cdm-shared-library=$(sut_cdm_ver)"
	@echo "Test are based on cdm-shared-library=$(sut_cdm_cur_ver)"
	@if [ $(sut_cdm_ver) != $(sut_cdm_cur_ver) ] ; then \
	echo "Warning: cdm-shared-library package for MVP is not the same as used for testing!"; \
	fi
	@echo "MVP is based on observation-execution-tool=$(sut_oet_ver)"
	@echo "Test are based on observation-execution-tool=$(sut_oet_cur_ver)"
	@if [ $(sut_oet_ver) != $(sut_oet_cur_ver) ] ; then \
	echo "Warning: observation-execution-tool package for MVP is not the same as used for testing!"; \
	fi

##the following section is for developers requiring the testing pod to be instantiated with a volume mappig to skampi
-include dev-testing.mk

timestamp=$(shell date -u +"%s")

sleepy_time:
	sleep 5s

measure_time:
	time1=$$SECONDS; \
	make sleepy_time; \
	time2=$$SECONDS; \
	elapsed=$$((time2 - time1)); \
	echo $$elapsed