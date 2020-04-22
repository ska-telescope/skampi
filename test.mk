.PHONY: k8s_test smoketest template_tests tango_rest_ingress_check

#
# IMAGE_TO_TEST defines the tag of the Docker image to test
#
IMAGE_TO_TEST ?= nexus.engageska-portugal.pt/ska-docker/tango-vscode:0.2.4
# Test runner - run to completion job in K8s
TEST_RUNNER = test-makefile-runner-$(CI_JOB_ID)-$(KUBE_NAMESPACE)-$(HELM_RELEASE)
#
# defines a function to copy the ./test-harness directory into the K8s TEST_RUNNER
# and then runs the requested make target in the container.
# capture the output of the test in a build folder inside the container 
# 
TANGO_HOST = databaseds-tango-base-$(HELM_RELEASE):10000
MARK ?= fast
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
k8s_test: smoketest## test the application on K8s
	$(call k8s_test,test); \
	  status=$$?; \
	  rm -fr build; \
	  kubectl --namespace $(KUBE_NAMESPACE) logs $(TEST_RUNNER) | \
	  perl -ne 'BEGIN {$$on=0;}; if (index($$_, "~~~~BOUNDARY~~~~")!=-1){$$on+=1;next;}; print if $$on % 2;' | \
	  base64 -d | tar -xzf -; \
	  kubectl --namespace $(KUBE_NAMESPACE) delete pod $(TEST_RUNNER); \
	  exit $$status


smoketest: ## check that the number of waiting containers is zero (10 attempts, wait time 30s).
	@echo "Smoke test START"; \
	n=10; \
	while [ $$n -gt 0 ]; do \
		waiting=`kubectl get pods -n $(KUBE_NAMESPACE) -o=jsonpath='{.items[*].status.containerStatuses[*].state.waiting.reason}' | wc -w`; \
		echo "Waiting containers=$$waiting"; \
		if [ $$waiting -ne 0 ]; then \
			echo "Waiting 30s for pods to become running...#$$n"; \
			sleep 30s; \
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

##the following section is for developers requiring the testing pod to be instantiated with a volume mappig to skampi
location:= $(shell pwd)
kube_path ?= $(shell echo ~/.kube)
k8_path ?= $(shell echo ~/.minikube)
PYTHONPATH=/home/tango/skampi/:/home/tango/skampi/post-deployment/:
testing-pod?=testing-pod
#the port mapping to host
hostPort ?= 2020
testing-config := '{ "apiVersion": "v1","spec":{\
					"containers":[{\
						"image":"$(IMAGE_TO_TEST)",\
						"name":"testing-container",\
						"volumeMounts":[{\
							"mountPath":"/home/tango/skampi/",\
							"name":"testing-volume"}],\
						"env":[{\
          			 		"name": "TANGO_HOST",\
            				"value": "databaseds-tango-base-$(HELM_RELEASE):10000"},{\
							"name": "KUBE_NAMESPACE",\
          					"value": "$(KUBE_NAMESPACE)"},{\
        					"name": "HELM_RELEASE",\
          					"value": "$(HELM_RELEASE)"},{\
							"name": "PYTHONPATH",\
							"value": "$(PYTHONPATH)"}],\
						"ports":[{\
							"containerPort":22,\
							"hostPort":$(hostPort)}]}],\
					"volumes":[{\
						"name":"testing-volume",\
						"hostPath":{\
							"path":"$(location)",\
							"type":"Directory"}}]}}'

deploy_testing_pod:
	@kubectl run $(testing-pod) \
	--image=$(IMAGE_TO_TEST) \
	--namespace $(KUBE_NAMESPACE) \
	--wait \
	--generator=run-pod/v1 \
	--overrides=$(testing-config)
	@kubectl wait --for=condition=Ready pod/$(testing-pod)
	@kubectl exec -it $(testing-pod) -- bash -c "/usr/bin/python3 -m pip install -r /home/tango/skampi/post-deployment/test_requirements.txt"
	@kubectl cp $(kube_path) $(KUBE_NAMESPACE)/$(testing-pod):/home/tango/.kube/ 
	@kubectl cp $(k8_path) $(KUBE_NAMESPACE)/$(testing-pod):/home/tango/.minikube/
	@kubectl exec -it $(testing-pod) -- bash -c " \
	kubectl config --kubeconfig=/home/tango/.kube/config set-credentials minikube --client-key=/home/tango/.minikube/client.key && \
	kubectl config --kubeconfig=/home/tango/.kube/config set-credentials minikube --client-certificate=/home/tango/.minikube/client.crt && \
	kubectl config --kubeconfig=/home/tango/.kube/config set-cluster minikube --certificate-authority=/home/tango/.minikube/ca.crt && \
	echo 'source <(kubectl completion bash)' >>/home/tango/.bashrc && \
	echo 'export HELM_RELEASE=$(HELM_RELEASE)' >> /home/tango/.bashrc && \
	echo 'export KUBE_NAMESPACE=$(KUBE_NAMESPACE)' >> /home/tango/.bashrc && \
	echo 'export VALUES=pipeline.yaml' >> /home/tango/.bashrc && \
	echo 'export TANGO_HOST=databaseds-tango-base-test:10000' >> /home/tango/.bashrc


	
delete_testing_pod:
	@kubectl delete pod $(testing-pod) --namespace $(KUBE_NAMESPACE)

attach_testing_pod:
	@kubectl exec -it $(testing-pod) --namespace $(KUBE_NAMESPACE) /bin/bash

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

clean_skampi:
	 git ls-files . --ignored --exclude-standard --others --directory | xargs rm -R -f

ssh_config = "Host kube-host\n\tHostName $(THIS_HOST) \n \tUser ubuntu"

test_as_ssh_client:
	@kubectl exec -it $(testing-pod) -- bash -c "mkdir /home/tango/.ssh/ && ssh-keygen -t rsa -f /home/tango/.ssh/id_rsa -q -P ''"
	@kubectl exec -it $(testing-pod) -- bash -c "cat /home/tango/.ssh/id_rsa.pub" >>~/.ssh/authorized_keys
	@kubectl exec -it $(testing-pod) -- bash -c "chown tango:tango -R /home/tango/.ssh/"
	@echo $(ssh_config) >temp
	@kubectl cp temp $(KUBE_NAMESPACE)/$(testing-pod):/home/tango/.ssh/config
	@rm temp


location:= $(shell pwd)

