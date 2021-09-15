
#
# IMAGE_TO_TEST defines the tag of the Docker image to test
#
IMAGE_TO_TEST ?= nexus.engageska-portugal.pt/ska-telescope/oet-ssh:0.3.0
# Test runner - run to completion job in K8s
TEST_RUNNER = test-makefile-runner-only-once-$(KUBE_NAMESPACE)-$(HELM_RELEASE)
#
# defines a function to copy the ./test-harness directory into the K8s TEST_RUNNER
# and then runs the requested make target in the container.
# capture the output of the test in a build folder inside the container 
# 
TANGO_HOST = databaseds-tango-base-$(HELM_RELEASE):10000
#
# defines a function to copy the ./test-harness directory into the K8s TEST_RUNNER
# and then runs the requested make target in the container.
# capture the output of the test in a tar file
# stream the tar file base64 encoded to the Pod logs
# 
k8s_test = tar -c test-harness/ | \
		kubectl run $(TEST_RUNNER) \
		--namespace $(KUBE_NAMESPACE) -i --wait --restart=Never \
		--image-pull-policy=IfNotPresent \
		--image=$(IMAGE_TO_TEST) -- \
		/bin/bash -c "mkdir skampi && tar xv --directory skampi --strip-components 1 --warning=all && cd skampi && \
		make KUBE_NAMESPACE=$(KUBE_NAMESPACE) HELM_RELEASE=$(HELM_RELEASE) TANGO_HOST=$(TANGO_HOST) $1 && \
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
k8s_test: smoketest ## test the application on K8s
	$(call k8s_test,test); \
	  status=$$?; \
	  rm -fr build; \
	  kubectl --namespace $(KUBE_NAMESPACE) logs $(TEST_RUNNER) | perl -ne 'BEGIN {$$on=1;}; if (index($$_, "~~~~BOUNDARY~~~~")!=-1){$$on+=1;next;}; print if $$on % 2;'; \
		kubectl --namespace $(KUBE_NAMESPACE) logs $(TEST_RUNNER) | \
		perl -ne 'BEGIN {$$on=0;}; if (index($$_, "~~~~BOUNDARY~~~~")!=-1){$$on+=1;next;}; print if $$on % 2;' | \
		base64 -d | tar -xzf -; \
		kubectl --namespace $(KUBE_NAMESPACE) delete pod $(TEST_RUNNER); \
	  exit $$status
