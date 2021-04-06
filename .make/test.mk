.PHONY: k8s_test smoketest template_tests tango_rest_ingress_check get_archiver_tango_host

CI_JOB_ID?=local
#
# IMAGE_TO_TEST defines the tag of the Docker image to test
#
#nexus.engageska-portugal.pt/ska-docker/tango-vscode:0.2.6-dirty
IMAGE_TO_TEST ?= artefact.skatelescope.org/ska-tango-images/tango-itango:9.3.3.1## docker image that will be run for testing purpose
# Test runner - run to completion job in K8s
TEST_RUNNER = test-makefile-runner-$(CI_JOB_ID)##name of the pod running the k8s_tests
#
# defines a function to copy the ./test-harness directory into the K8s TEST_RUNNER
# and then runs the requested make target in the container.
# capture the output of the test in a build folder inside the container
#
TANGO_HOST ?= $(TANGO_DATABASE_DS):10000
MARK ?= fast## this variable allow the mark parameter in the pytest
FILE ?= ##this variable allow to execution of a single file in the pytest 
SLEEPTIME ?= 30s ##amount of sleep time for the smoketest target

oet_podname = $(shell kubectl get pods -l app=oet,component=rest,release=$(HELM_RELEASE) -o=jsonpath='{..metadata.name}')
sut_cdm_ver= $(shell kubectl exec -it $(oet_podname) -- pip list | grep "cdm-shared-library" | awk ' {print $$2}' | awk 'BEGIN { FS = "+" } ; {print $$1}')
sut_oet_ver = $(shell kubectl exec -it $(oet_podname) -- pip list | grep "oet-scripts" | awk ' {print $$2}' | awk 'BEGIN { FS = "+" } ; {print $$1}')
sut_oet_cur_ver=$(shell grep "oet-scripts" post-deployment/SUT_requirements.txt | awk 'BEGIN { FS = "==" } ; {print $$2}')


check_oet_packages:
	@echo "MVP is based on cdm-shared-library=$(sut_cdm_ver)"
	@echo "MVP is based on oet-scripts=$(sut_oet_ver)"
	@echo "Test are based on oet-scripts=$(sut_oet_cur_ver)"
	@if [ $(sut_oet_ver) != $(sut_oet_cur_ver) ] ; then \
	echo "Warning: oet-scripts package for MVP is not the same as used for testing!"; \
	fi

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
		--image=$(IMAGE_TO_TEST) \
		--limits='cpu=1000m,memory=500Mi' \
		--requests='cpu=900m,memory=400Mi' \
		--env=INGRESS_HOST=$(INGRESS_HOST) \
		$(PSI_LOW_PROXY_VALUES) -- \
		/bin/bash -c "mkdir skampi && tar xv --directory skampi --strip-components 1 --warning=all && cd skampi && \
		make SKUID_URL=skuid-skuid-$(KUBE_NAMESPACE)-$(HELM_RELEASE).$(KUBE_NAMESPACE).svc.cluster.local:9870 KUBE_NAMESPACE=$(KUBE_NAMESPACE) HELM_RELEASE=$(HELM_RELEASE) TANGO_HOST=$(TANGO_HOST) MARK='$(MARK)' FILE='$(FILE)' $1 && \
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
k8s_test: smoketest## test the application on K8s
	$(call k8s_test,test); \
		status=$$?; \
		rm -fr build; \
		kubectl --namespace $(KUBE_NAMESPACE) logs $(TEST_RUNNER) | \
		perl -ne 'BEGIN {$$on=0;}; if (index($$_, "~~~~BOUNDARY~~~~")!=-1){$$on+=1;next;}; print if $$on % 2;' | \
		base64 -d | tar -xzf -; mkdir -p build; \
		python3 scripts/collect_k8s_logs.py $(KUBE_NAMESPACE) $(KUBE_NAMESPACE_SDP) \
			--pp build/k8s_pretty.txt --dump build/k8s_dump.txt --tests build/k8s_tests.txt; \
		kubectl --namespace $(KUBE_NAMESPACE) delete pod $(TEST_RUNNER); \
		exit $$status


clear_sdp_config:
	@echo "clearing the sdp config db using a temporary call on the console pod on namespace: $(KUBE_NAMESPACE)"
	kubectl exec -n $(KUBE_NAMESPACE) deploy/test-sdp-prototype-console -- sdpcfg delete -R /

smoketest: wait## wait for pods to be ready and jobs to be completed

wait:## wait for pods to be ready
	@echo "Waiting for pods to be ready and jobs to be completed. Timeout 120s"
	@date
	@kubectl -n $(KUBE_NAMESPACE) get pods
	@date
	@jobs=$$(kubectl get job --output=jsonpath={.items..metadata.name} -n $(KUBE_NAMESPACE)); kubectl wait job --for=condition=complete --timeout=120s $$jobs -n $(KUBE_NAMESPACE)
	@date
	@for p in `kubectl get pods -n $(KUBE_NAMESPACE) -o=jsonpath="{range .items[*]}{.metadata.name}{';'}{'Ready='}{.status.conditions[?(@.type == 'Ready')].status}{';'}{.metadata.ownerReferences[?(@.kind != 'Job')].name}{'\n'}{end}"`; do v_owner_name=$$(echo $$p | cut -d';' -f3); if [ ! -z "$$v_owner_name" ]; then v_pod_name=$$(echo $$p | cut -d';' -f1); pods="$$pods $$v_pod_name"; fi; done; kubectl wait pods --all --for=condition=ready --timeout=120s $$pods -n $(KUBE_NAMESPACE)
	@date

tango_rest_ingress_check:  ## curl test Tango REST API - https://tango-controls.readthedocs.io/en/latest/development/advanced/rest-api.html#tango-rest-api-implementations
	@echo "---------------------------------------------------"
	@echo "Test HTTP:"; echo ""
	curl -u "tango-cs:tango" -XGET http://tango.rest.$(INGRESS_HOST)/tango/rest/rc4/hosts/databaseds-tango-base-$(HELM_RELEASE)/10000 | json_pp
	# @echo "", echo ""
	# @echo "---------------------------------------------------"
	# @echo "Test HTTPS:"; echo ""
	# curl -k -u "tango-cs:tango" -XGET https://tango.rest.$(INGRESS_HOST)/tango/rest/rc4/hosts/databaseds-tango-base-$(HELM_RELEASE)/10000 | json_pp
	# @echo ""

