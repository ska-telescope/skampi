#
# IMAGE_TO_TEST defines the tag of the Docker image to test
#
IMAGE_TO_TEST ?= nexus.engageska-portugal.pt/ska-docker/tango-itango
# Test runner - pod always running for testing purposes
TEST_RUNNER = $(shell kubectl get pod -n $(KUBE_NAMESPACE) | grep test-runner | cut -d\  -f1)
#
# defines a function to copy the ./test-harness directory into the K8s TEST_RUNNER
# and then runs the requested make target in the container.
# capture the output of the test in a build folder inside the container 
# 
TANGO_HOST = $(shell kubectl get pods -n $(KUBE_NAMESPACE) | grep tangod | cut -d\  -f1)
k8s_test = kubectl exec -i $(TEST_RUNNER) --namespace $(KUBE_NAMESPACE) -- rm -fr /app/test-harness && \
		kubectl cp test-harness/ $(KUBE_NAMESPACE)/$(TEST_RUNNER):/app/test-harness && \
		kubectl exec -i $(TEST_RUNNER) --namespace $(KUBE_NAMESPACE) -- \
		/bin/bash -c "cd /app/test-harness && make $1" 2>&1

# run the test function
# save the status
# clean out build dir
# retrieve the new build dir
# exit the saved status
k8s_test: smoketest ## test the application on K8s
	$(call k8s_test,test); \
	  status=$$?; \
	  rm -fr build; \
	  kubectl cp $(KUBE_NAMESPACE)/$(TEST_RUNNER):/app/test-harness/build/ build/; \
	  exit $$status