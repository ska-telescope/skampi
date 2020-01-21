KUBE_NAMESPACE = integration
pod_name=acceptance-testing-pod
app= acceptance-tester
SOURCE_PATH := $(shell  cd ../.. && pwd )
THIS_HOST := $(shell (ip a 2> /dev/null || ifconfig) | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)

#kubectl composites
pod_ready := kubectl get pods -l app=$(app) -n $(KUBE_NAMESPACE) -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}'
get_pod = output=$$(kubectl get pods -l app=$(app) -n $(KUBE_NAMESPACE) -o 'jsonpath={..metadata.name}'); \
		echo $$output

#shell routines
#wait for a time out period until pod is in ready state
wait_for_pod = count=0;  \
		ready=$$($(pod_ready));  \
		while [ $$count -lt 10 -a $$ready != True ]; do \
			sleep 1; \
			count=`expr $$count + 1`; \
			ready=$$($(pod_ready)) ;\
		done;


deploy_storage: # deploy a persistant volume that maps to the skampi repository
	@helm template storage/helm-chart/  -n test --namespace $(KUBE_NAMESPACE) --set path=$(SOURCE_PATH) | kubectl apply -f -

deploy_interactive: deploy_storage # deploy a testing container to work on interactively
	@helm template test-pod/helm-chart/ -n test --namespace $(KUBE_NAMESPACE) -f test-pod/helm-chart/local_values.yaml | kubectl apply -f -
	#wait for pod to be in running state
	@$(wait_for_pod)
	#get pod name
	$(eval THE_POD := $(shell $(get_pod)))
	echo $(THE_POD)
	#execute additional dependencies on the pod
	kubectl exec -it  -n integration $(THE_POD) -- bash  -c "apt-get update && apt-get install curl -y && apt-get install git -y"

deploy_test_job: deploy_storage # deploy a testing job TODO
	@helm template test-pod/helm-chart/ -n test --namespace $(KUBE_NAMESPACE) -f test-pod/helm-chart/local_values.yaml --set interactive=false | kubectl apply -f -

delete_storage: # delete a storage volume
	@helm template storage/helm-chart/ -n test --namespace $(KUBE_NAMESPACE) --set path=$(SOURCE_PATH) | kubectl delete -f -	

delete_interactive: # delete an interactive test container
	@helm template test-pod/helm-chart/ -n test --namespace $(KUBE_NAMESPACE) -f test-pod/helm-chart/local_values.yaml | kubectl delete -f -

get_ssh_par: # get the ssh paramaters for getting into container
	@kubectl get service -l app=acceptance-tester -n integration  -o jsonpath="{range .items[0]}{'Use this port to shh in: '}{.spec.ports[0].nodePort}{'\n'}{end}"

