KUBE_NAMESPACE = integration
apply_template= | kubectl apply -f -
delete_template= | kubectl delete -f -
pod_name_interactive= acceptance-testing-pod
pod_name_test_job= acceptance-testing-job
app= acceptance-tester
execution_path:= /home/
time_out=10

SOURCE_PATH := $(shell  cd ../.. && pwd )
THIS_HOST := $(shell (ip a 2> /dev/null || ifconfig) | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)

#kubectl composites
pod_ready := kubectl get pods -l app=$(app) -n $(KUBE_NAMESPACE) -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}'


#shell routines
#wait for a time out period until pod is in ready state
wait_for_pod = count=0;  \
		ready=$$($(pod_ready));  \
		while [ $$count -lt $(time_out) -a $$ready != True ]; do \
			sleep 1; \
			echo $$count; \
			count=`expr $$count + 1`; \
			ready=$$($(pod_ready)) ;\
		done;

deploy_storage: # deploy a persistant volume that maps to the skampi repository
	@helm template storage/helm-chart/  -n test --namespace $(KUBE_NAMESPACE) --set path=$(SOURCE_PATH) $(apply_template)

deploy_interactive: deploy_storage # deploy a testing container to work on interactively
	@helm template test-pod/helm-chart/ -n test --namespace $(KUBE_NAMESPACE) --set pod_name=$(pod_name_interactive) -f test-pod/helm-chart/local_values.yaml $(apply_template)
	#wait for pod to be in running state
	@$(wait_for_pod)
	#execute additional dependencies on the pod
	kubectl exec -it  -n integration $(pod_name_interactive) -- bash  -c "apt-get update && apt-get install curl -y && apt-get install git -y"

delete_interactive: # delete an interactive test container
	@helm template test-pod/helm-chart/ -n test --namespace $(KUBE_NAMESPACE) -f test-pod/helm-chart/local_values.yaml --set pod_name=$(pod_name_interactive)  $(delete_template)


deploy_test_job: deploy_storage # deploy a testing job 
	@helm template test-pod/helm-chart/ -n test --namespace $(KUBE_NAMESPACE) -f test-pod/helm-chart/local_values.yaml  --set pod_name=$(pod_name_test_job) --set non_interactive=true $(apply_template)

delete_test_job:
	@helm template test-pod/helm-chart/ -n test --namespace $(KUBE_NAMESPACE) -f test-pod/helm-chart/local_values.yaml --set pod_name=$(pod_name_test_job) --set non_interactive=true $(delete_template)


delete_storage: # delete a storage volume
	@helm template storage/helm-chart/ -n test --namespace $(KUBE_NAMESPACE) --set path=$(SOURCE_PATH) $(delete_template)	

get_ssh_par: # get the ssh paramaters for getting into container
	@kubectl get service -l app=acceptance-tester -n integration  -o jsonpath="{range .items[0]}{'Use this port to shh in: '}{.spec.ports[0].nodePort}{'\n'}{end}"

get_status:
	kubectl get svc,pods -l app=$(app) -n $(KUBE_NAMESPACE)
	kubectl get pv,pvc -l type=repository -n $(KUBE_NAMESPACE)

get_system:
	kubectl get svc,pods,pv,pvc -n $(KUBE_NAMESPACE)

get_logs:
	kubectl logs $(pod_name_test_job) -n $(KUBE_NAMESPACE)

attach:
	kubectl exec -it -n $(KUBE_NAMESPACE) $(pod_name_test_job) /bin/bash

attach_interact:
	kubectl attach -it -n $(KUBE_NAMESPACE) $(pod_name_interactive) 

############container makes######################################

cont_build: cont_invoke ## build the base dependencies needed for basic operations
	pip3 install -r requirements

cont_invoke:
	p=$$(pwd) ; \
	cd / ; \
	. /venv/bin/activate ; \
	cd $$p 

cont_interactive:
	. /venv/bin/itango3 --profile=ska

cont_test: cont_build ## run tests
	py.test

temp:
	( p=$$(pwd) ; \
	cd / ; \
	. venv/bin/activate ; \
	cd $$p )




