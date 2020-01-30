KUBE_NAMESPACE = integration
apply_template= | kubectl apply -f -
delete_template= | kubectl delete -f -
pod_name_interactive= acceptance-testing-pod
test_job= acceptance-testing-job
app= acceptance-tester
execution_path:= /home/
time_out=10
storage_path = charts/acceptance-testing/storage
test_pod_path = charts/acceptance-testing/test-pod
test_scripts_path = test-harness/acceptance_tests 
SOURCE_PATH := $(shell pwd )
THIS_HOST := $(shell (ip a 2> /dev/null || ifconfig) | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)


#kubectl composites
pod_ready := kubectl get pods -l app=$(app) -n $(KUBE_NAMESPACE) -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}'
loc := pos $$(pwd) && cd $(test_scripts_path) && 
job_ready := kubectl get job $(test_job) -n $(KUBE_NAMESPACE) -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}'

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

wait_for_job = pod=$$(kubectl get pods --selector=job-name=$(test_job) -n $(KUBE_NAMESPACE) --output=jsonpath='{.items[*].metadata.name}'); \
	       kubectl wait --for=condition=Ready -n $(KUBE_NAMESPACE) pod/$$pod

acc_deploy_storage: # deploy a persistant volume that maps to the skampi repository
	@helm template $(storage_path)  -n test --namespace $(KUBE_NAMESPACE) --set path=$(SOURCE_PATH),enabled=true $(apply_template)

acc_deploy_interactive: acc_deploy_storage # deploy a testing container to work on interactively
	helm template $(test_pod_path) -n test --namespace $(KUBE_NAMESPACE) --set pod_name=$(pod_name_interactive),enabled=true -f $(test_pod_path)/local_values.yaml $(apply_template)
	#wait for pod to be in running state
	@$(wait_for_pod)
	#execute additional dependencies on the pod
	kubectl exec -it  -n integration $(pod_name_interactive) -- bash  -c "apt-get update && apt-get install curl -y && apt-get install git --fix-missing -y"

acc_show_interactive:
	@helm template $(test_pod_path) -n test --namespace $(KUBE_NAMESPACE) --set pod_name=$(pod_name_interactive),enabled=true -f $(test_pod_path)/local_values.yaml

acc_show_test_job:
	@helm template $(test_pod_path) -n test --namespace $(KUBE_NAMESPACE) -f $(test_pod_path)/local_values.yaml  --set pod_name=$(pod_name_test_job),enabled=true,non_interactive=true
	#--set non_interactive=true
acc_delete_interactive: # delete an interactive test container
	@helm template $(test_pod_path) -n test --namespace $(KUBE_NAMESPACE) --set pod_name=$(pod_name_interactive),enabled=true -f $(test_pod_path)/local_values.yaml $(delete_template)


acc_deploy_test_job: acc_deploy_storage # deploy a testing job 
	#delete job if already exists
	@-kubectl get job --namespace $(KUBE_NAMESPACE) $(test_job) 1> /dev/null && kubectl delete job --namespace $(KUBE_NAMESPACE) $(test_job)
	@helm template $(test_pod_path) -n test --namespace $(KUBE_NAMESPACE) -f $(test_pod_path)/local_values.yaml  --set pod_name=$(test_job),enabled=true,non_interactive=true  $(apply_template)
	#wait for pod to be in running state
	$(wait_for_job)
	#attach onto the job
	@kubectl attach job $(test_job) --namespace $(KUBE_NAMESPACE) 

temp:
	@helm template $(test_pod_path) -n test --namespace $(KUBE_NAMESPACE) -f $(test_pod_path)/local_values.yaml  --set pod_name=$(pod_name_test_job),enabled=true,non_interactive=true  $(apply_template)

acc_delete_test_job:
	@helm template $(test_pod_path)/ -n test --namespace $(KUBE_NAMESPACE) -f $(test_pod_path)/local_values.yaml --set pod_name=$(test_job),enabled=true --set non_interactive=true $(delete_template)
	@helm template $(storage_path)/ -n test --namespace $(KUBE_NAMESPACE) --set path=$(SOURCE_PATH),enabled=true $(delete_template)	


acc_delete_storage: # delete a storage volume
	@helm template $(storage_path)/ -n test --namespace $(KUBE_NAMESPACE) --set path=$(SOURCE_PATH),enabled=true $(delete_template)	

acc_get_ssh_par: # get the ssh paramaters for getting into container
	@kubectl get service -l app=acceptance-tester -n integration  -o jsonpath="{range .items[0]}{'Use this port to shh in: '}{.spec.ports[0].nodePort}{'\n'}{end}"

acc_get_status:
	kubectl get svc,pods,jobs -l app=$(app) -n $(KUBE_NAMESPACE)
	kubectl get pv,pvc -l type=repository -n $(KUBE_NAMESPACE)

acc_get_system:
	kubectl get svc,pods,pv,pvc -n $(KUBE_NAMESPACE)

acc_get_logs:
	kubectl logs $(pod_name_test_job) -n $(KUBE_NAMESPACE)

acc_attach:
	kubectl exec -it -n $(KUBE_NAMESPACE) $(pod_name_test_job) /bin/bash

acc_attach_interact:
	kubectl attach -it -n $(KUBE_NAMESPACE) $(pod_name_interactive) 

	




