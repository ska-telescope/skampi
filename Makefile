# Set dir of Makefile to a variable to use later
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
BASEDIR := $(notdir $(patsubst %/,%,$(dir $(MAKEPATH))))

# find IP addresses of this machine, setting THIS_HOST to the first address found
THIS_HOST := $(shell (ip a 2> /dev/null || ifconfig) | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)
DISPLAY := $(THIS_HOST):0
XAUTHORITYx ?= ${XAUTHORITY}
KUBE_NAMESPACE ?= integration# Kubernetes Namespace to use
KUBE_NAMESPACE_SDP ?= $(KUBE_NAMESPACE)-sdp# Kubernetes Namespace to use for SDP dynamic deployments
HELM_RELEASE ?= test# Helm release name
HELM_CHART ?= skampi# Helm Chart to install (see ./charts)
SUB_CHART ?= tmc-proto# SubChart to install/uninstall
HELM_CHART_TEST ?= tests# Helm Chart to install (see ./charts)
INGRESS_HOST ?= integration.engageska-portugal.pt# Ingress HTTP hostname
USE_NGINX ?= false# Use NGINX as the Ingress Controller
API_SERVER_IP ?= $(THIS_HOST)# Api server IP of k8s
API_SERVER_PORT ?= 6443# Api server port of k8s
EXTERNAL_IP ?= $(THIS_HOST)# For traefik installation
CLUSTER_NAME ?= integration.cluster# For the gangway kubectl setup
CLIENT_ID ?= 417ea12283741e0d74b22778d2dd3f5d0dcee78828c6e9a8fd5e8589025b8d2f# For the gangway kubectl setup, taken from Gitlab
CLIENT_SECRET ?= 27a5830ca37bd1956b2a38d747a04ae9414f9f411af300493600acc7ebe6107f# For the gangway kubectl setup, taken from Gitlab
CHART_SET ?=#for additional flags you want to set when deploying (default empty)
VALUES ?= values.yaml# root level values files. This will override the chart values files.
DEPLOYMENT_ORDER ?= tango-base cbf-proto csp-proto sdp-prototype tmc-proto oet webjive archiver dsh-lmc-prototype logging skuid## list of charts that will be deployed in order

# Stable name for the Tango DB
TANGO_DATABASE_DS ?= databaseds-tango-base-$(HELM_RELEASE):10000

# activate remote debugger for VSCode (ptvsd)
REMOTE_DEBUG ?= false

# define overides for above variables in here
-include PrivateRules.mak

.PHONY: vars k8s apply logs rm show deploy deploy_all delete ls podlogs namespace namespace_sdp help
.DEFAULT_GOAL := help

# include makefile targets that wrap helm
-include helm.mk

# install stable chart repo this step si
helm_add_stable_repo := helm repo add stable https://kubernetes-charts.storage.googleapis.com/

# include makefile targets for testing
-include test.mk

vars: ## Display variables - pass in DISPLAY and XAUTHORITY
	@echo "DISPLAY: $(DISPLAY)"
	@echo "XAUTHORITY: $(XAUTHORITYx)"
	@echo "Namespace: $(KUBE_NAMESPACE)"
	@echo "HELM_RELEASE: $(HELM_RELEASE)"
	@echo "VALUES: $(VALUES)"
	@echo "TANGO_DATABASE_DS: $(TANGO_DATABASE_DS)"

k8s: ## Which kubernetes are we connected to
	@echo "Kubernetes cluster-info:"
	@kubectl cluster-info
	@echo ""
	@echo "kubectl version:"
	@kubectl version
	@echo ""
	@echo "Helm version:"
	@$(helm_tiller_prefix) helm version

logs: ## POD logs for descriptor
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l group=example -o=name`; \
	do echo "-------------------"; \
	echo "Logs for $$i"; \
	kubectl -n $(KUBE_NAMESPACE) logs $$i; \
	done

namespace: ## create the kubernetes namespace
	@kubectl describe namespace $(KUBE_NAMESPACE) > /dev/null 2>&1 ; \
  K_DESC=$$? ; \
  if [ $$K_DESC -eq 0 ] ; \
  then kubectl describe namespace $(KUBE_NAMESPACE) ; \
  else kubectl create namespace $(KUBE_NAMESPACE); \
  fi

namespace_sdp: ## create the kubernetes namespace for SDP dynamic deployments
	@kubectl describe namespace $(KUBE_NAMESPACE_SDP) > /dev/null 2>&1 ; \
 	K_DESC=$$? ; \
	if [ $$K_DESC -eq 0 ] ; \
	then kubectl describe namespace $(KUBE_NAMESPACE_SDP) ; \
	else kubectl create namespace $(KUBE_NAMESPACE_SDP); \
	fi

lint_all:  ## lint ALL of the helm chart
	@for i in charts/skampi/charts/*; do \
	cd $$i; pwd; helm lint ; \
	done

lint:  ## lint the HELM_CHART of the helm chart
	cd charts/skampi/charts/$(HELM_CHART); pwd; helm lint;

.PHONY: deploy_etcd delete_etcd
deploy_etcd: namespace ## Deploy etcd-operator into namespace
	@if ! kubectl get pod -n $(KUBE_NAMESPACE) -o jsonpath='{.items[*].metadata.labels.app}' \
		| grep -q etcd-operator; then \
		TMP=`mktemp -d`; \
		$(helm_add_stable_repo) && \
		helm fetch stable/etcd-operator --untar --untardir $$TMP && \
		helm template $(helm_install_shim) $$TMP/etcd-operator \
			-n etc-operator --namespace $(KUBE_NAMESPACE) \
			--set deployments.backupOperator=false \
			--set deployments.restoreOperator=false \
		| kubectl apply -n $(KUBE_NAMESPACE) -f -; \
		n=5; \
    	while ! kubectl api-resources --api-group=etcd.database.coreos.com \
        	| grep -q etcdcluster && [ $${n} -gt 0 ]; do \
        	echo Waiting for etcd CRD to become available...; sleep 1; \
        	n=`expr $$n - 1` || true; \
		done \
	fi

delete_etcd: ## Remove etcd-operator from namespace
	-@if kubectl get pod -n $(KUBE_NAMESPACE) \
        		-o jsonpath='{.items[*].metadata.labels.app}' \
		| grep -q etcd-operator; then \
		TMP=`mktemp -d`; \
		$(helm_add_stable_repo) && \
		helm fetch stable/etcd-operator --untar --untardir $$TMP && \
		helm template $(helm_install_shim) $$TMP/etcd-operator \
			-n etc-operator --namespace $(KUBE_NAMESPACE) \
			--set deployments.backupOperator=false \
			--set deployments.restoreOperator=false \
		| kubectl delete -n $(KUBE_NAMESPACE) -f -; \
	fi

mkcerts:  ## Make dummy certificates for $(INGRESS_HOST) and Ingress
	@if [ ! -f charts/skampi/charts/webjive/data/tls.key ]; then \
	CN=`echo "$(INGRESS_HOST)" | tr -d '[:space:]'`; \
	openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 \
	   -keyout charts/skampi/charts/webjive/data/tls.key \
		 -out charts/skampi/charts/webjive/data/tls.crt \
		 -subj "/CN=$${CN}/O=Minikube"; \
	else \
	echo "SSL cert already exits in charts/skampi/charts/webjive/data ... skipping"; \
	fi; \
	if [ ! -f charts/skampi/charts/tango-base/secrets/tls.key ]; then \
	CN=`echo "tango.rest.$(INGRESS_HOST)" | tr -d '[:space:]'`; \
	openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 \
	   -keyout charts/skampi/charts/tango-base/secrets/tls.key \
		 -out charts/skampi/charts/tango-base/secrets/tls.crt \
		 -subj "/CN=$${CN}/O=Minikube"; \
	else \
	echo "SSL cert already exits in charts/skampi/charts/tango-base/secrets ... skipping"; \
	fi

deploy: namespace namespace_sdp mkcerts  ## Deploy one helm chart. @param: same as deploy_all, plus HELM_CHART
	@helm template $(helm_install_shim) charts/skampi/charts/$(HELM_CHART)/ \
				 --namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITYx)" \
				 --set ingress.hostname=$(INGRESS_HOST) \
				 --set ingress.nginx=$(USE_NGINX) \
	             --set tangoexample.debug="$(REMOTE_DEBUG)" \
				 $(CHART_SET) \
				 --set helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
				 --set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
				 --values $(VALUES) | kubectl apply -f -

show: mkcerts  ## Show the helm chart @param: same as deploy_all, plus HELM_CHART
	@helm template $(helm_install_shim) charts/skampi/charts/$(HELM_CHART)/ \
				 --namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITYx)" \
				 --set ingress.hostname=$(INGRESS_HOST) \
				 --set ingress.nginx=$(USE_NGINX) \
	             --set tangoexample.debug="$(REMOTE_DEBUG)" \
				 $(CHART_SET) \
				 --set helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
				 --set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
				 --values $(VALUES)

show_all:
	@for i in charts/skampi/charts/*; do \
	echo "*****************************  $$i ********************************"; \
	if [ "$$i" = "charts/skampi/charts/auth" ] ; then \
		continue; \
	fi; \
	helm template $(helm_install_shim) $$i \
				 --namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITYx)" \
				 --set ingress.hostname=$(INGRESS_HOST) \
				 --set ingress.nginx=$(USE_NGINX) \
	             --set tangoexample.debug="$(REMOTE_DEBUG)" \
					$(CHART_SET) \
				 --set helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
				 --set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
				 --values $(VALUES) ; \
	done

delete: ## delete the helm chart release. @param: same as deploy_all, plus HELM_CHART
	@helm template $(helm_install_shim) charts/skampi/charts/$(HELM_CHART)/ \
				 --namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITYx)" \
				 --set ingress.hostname=$(INGRESS_HOST) \
				 --set ingress.nginx=$(USE_NGINX) \
	             --set tangoexample.debug="$(REMOTE_DEBUG)" \
				 $(CHART_SET) \
				 --set helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
				 --values $(VALUES) | kubectl delete -f -

deploy_ordered: namespace namespace_sdp mkcerts deploy_etcd ## Deploy subset of charts. @param: DEPLOYMENT_ORDER, KUBE_NAMESPACE, DISPLAY, XAUTHORITYx, INGRESS_HOST, USE_NGINX, REMOTE_DEBUG, KUBE_NAMESPACE_SDP, CHART_SET, VALUES
	for chartname in $(DEPLOYMENT_ORDER); do \
	echo "*****************************  $$chartname ********************************"; \
		helm template $(helm_install_shim) charts/skampi/charts/$$chartname/ \
					--namespace $(KUBE_NAMESPACE) \
					--set display="$(DISPLAY)" \
					--set xauthority="$(XAUTHORITYx)" \
					--set ingress.hostname=$(INGRESS_HOST) \
					--set ingress.nginx=$(USE_NGINX) \
					--set tangoexample.debug="$(REMOTE_DEBUG)" \
					$(CHART_SET) \
					--set helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
				    --set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
					--values $(VALUES) | kubectl apply -f - ; \
					make smoketest SLEEPTIME=3s > /dev/null 2>&1; \
	done


show_skampi: mkcerts  ## Show entire suite
	@helm install --dry-run --debug $(HELM_RELEASE) charts/skampi/ \
				  --namespace $(KUBE_NAMESPACE) \
				  --set tango-base.display="$(DISPLAY)" \
				  --set tango-base.xauthority="$(XAUTHORITYx)" \
				  --set archiver.display="$(DISPLAY)" \
				  --set archiver.xauthority="$(XAUTHORITYx)" \
				  --set logging.ingress.hostname=$(INGRESS_HOST) \
				  --set logging.ingress.nginx=$(USE_NGINX) \
				  --set oet.ingress.hostname=$(INGRESS_HOST) \
				  --set oet.ingress.nginx=$(USE_NGINX) \
				  --set skuid.ingress.hostname=$(INGRESS_HOST) \
				  --set skuid.ingress.nginx=$(USE_NGINX) \
				  --set tango-base.ingress.hostname=$(INGRESS_HOST) \
				  --set tango-base.ingress.nginx=$(USE_NGINX) \
				  --set webjive.ingress.hostname=$(INGRESS_HOST) \
				  --set webjive.ingress.nginx=$(USE_NGINX) \
				  $(CHART_SET) \
				  --set sdp-prototype.helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
				  --set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
				  --values $(VALUES)

install: namespace namespace_sdp mkcerts deploy_etcd ## helm install entire suite
	helm install $(HELM_RELEASE) charts/skampi/ \
				 --namespace $(KUBE_NAMESPACE) \
				 --set tango-base.display="$(DISPLAY)" \
				 --set tango-base.xauthority="$(XAUTHORITYx)" \
				 --set archiver.display="$(DISPLAY)" \
				 --set archiver.xauthority="$(XAUTHORITYx)" \
				 --set logging.ingress.hostname=$(INGRESS_HOST) \
				 --set logging.ingress.nginx=$(USE_NGINX) \
				 --set oet.ingress.hostname=$(INGRESS_HOST) \
				 --set oet.ingress.nginx=$(USE_NGINX) \
				 --set skuid.ingress.hostname=$(INGRESS_HOST) \
				 --set skuid.ingress.nginx=$(USE_NGINX) \
				 --set tango-base.ingress.hostname=$(INGRESS_HOST) \
				 --set tango-base.ingress.nginx=$(USE_NGINX) \
				 --set webjive.ingress.hostname=$(INGRESS_HOST) \
				 --set webjive.ingress.nginx=$(USE_NGINX) \
				 $(CHART_SET) \
				 --set sdp-prototype.helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
				 --set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
				 --values $(VALUES) --wait --timeout=10m0s
	make smoketest SLEEPTIME=3s > /dev/null 2>&1

uninstall: delete_etcd ## delete ALL of the helm chart release
	helm delete $(HELM_RELEASE) --namespace $(KUBE_NAMESPACE) || true


install_subchart: namespace namespace_sdp mkcerts deploy_etcd ## helm install entire suite
	helm install $(SUB_CHART)-$(HELM_RELEASE) charts/skampi/charts/$(SUB_CHART)/ \
				 --namespace $(KUBE_NAMESPACE) \
				 --set tango-base.display="$(DISPLAY)" \
				 --set tango-base.xauthority="$(XAUTHORITYx)" \
				 --set archiver.display="$(DISPLAY)" \
				 --set archiver.xauthority="$(XAUTHORITYx)" \
				 --set logging.ingress.hostname=$(INGRESS_HOST) \
				 --set logging.ingress.nginx=$(USE_NGINX) \
				 --set oet.ingress.hostname=$(INGRESS_HOST) \
				 --set oet.ingress.nginx=$(USE_NGINX) \
				 --set skuid.ingress.hostname=$(INGRESS_HOST) \
				 --set skuid.ingress.nginx=$(USE_NGINX) \
				 --set tango-base.ingress.hostname=$(INGRESS_HOST) \
				 --set tango-base.ingress.nginx=$(USE_NGINX) \
				 --set webjive.ingress.hostname=$(INGRESS_HOST) \
				 --set webjive.ingress.nginx=$(USE_NGINX) \
				 $(CHART_SET) \
				 --set sdp-prototype.helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
				 --set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
				 --values $(VALUES) --wait --timeout=3m0s
	@chart_name=$$(helm list --filter $(SUB_CHART)-$(HELM_RELEASE) -o=yaml | grep chart | awk '{print $$NF}') && \
		kubectl get all -l chart=$$chart_name
	make smoketest SLEEPTIME=3s > /dev/null 2>&1

uninstall_subchart: delete_etcd ## delete ALL of the helm chart release
	helm delete $(SUB_CHART)-$(HELM_RELEASE) --namespace $(KUBE_NAMESPACE) || true

describe_install: ## describe a current helm installation given by SUB_CHART as name
	@chart_name=$$(helm list --all --filter $(SUB_CHART)-$(HELM_RELEASE) -o=yaml | grep chart | awk '{print $$NF}') && \
		kubectl get all -l chart=$$chart_name


deploy_all: namespace namespace_sdp mkcerts deploy_etcd ## Deploy all charts. @param: KUBE_NAMESPACE, DISPLAY, XAUTHORITYx, INGRESS_HOST, USE_NGINX, REMOTE_DEBUG, KUBE_NAMESPACE_SDP, CHART_SET, VALUES
	@for i in charts/skampi/charts/*; do \
	echo "*****************************  $$i ********************************"; \
	if [ "$$i" = "charts/skampi/charts/auth" ] ; then \
		continue; \
	fi; \
	helm template $(helm_install_shim) $$i \
				 --namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITYx)" \
				 --set ingress.hostname=$(INGRESS_HOST) \
				 --set ingress.nginx=$(USE_NGINX) \
	             --set tangoexample.debug="$(REMOTE_DEBUG)" \
					$(CHART_SET) \
				 --set helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
				 --set tangoDatabaseDS=$(TANGO_DATABASE_DS) \
				 --values $(VALUES) | kubectl apply -f - ; \
	done

delete_all: delete_etcd ## delete ALL of the helm chart release
	@for i in charts/skampi/charts/*; do \
	echo "*****************************  $$i ********************************"; \
	if [ "$$i" = "charts/skampi/charts/auth" ] ; then \
		continue; \
	fi; \
	helm template $(helm_install_shim) $$i \
				 --namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITYx)" \
				 --set ingress.hostname=$(INGRESS_HOST) \
				 --set ingress.nginx=$(USE_NGINX) \
	             --set tangoexample.debug="$(REMOTE_DEBUG)"  \
				 --set helm_deploy.namespace=$(KUBE_NAMESPACE_SDP) \
				 --values $(VALUES) | kubectl delete -f - ; \
	done

poddescribe: ## describe Pods executed from Helm chart
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l release=$(HELM_RELEASE) -o=name`; \
	do echo "---------------------------------------------------"; \
	echo "Describe for $${i}"; \
	echo kubectl -n $(KUBE_NAMESPACE) describe $${i}; \
	echo "---------------------------------------------------"; \
	kubectl -n $(KUBE_NAMESPACE) describe $${i}; \
	echo "---------------------------------------------------"; \
	echo ""; echo ""; echo ""; \
	done

podlogs: ## show Helm chart POD logs
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l release=$(HELM_RELEASE) -o=name`; \
	do \
	echo "---------------------------------------------------"; \
	echo "Logs for $${i}"; \
	echo kubectl -n $(KUBE_NAMESPACE) logs $${i}; \
	echo kubectl -n $(KUBE_NAMESPACE) get $${i} -o jsonpath="{.spec.initContainers[*].name}"; \
	echo "---------------------------------------------------"; \
	for j in `kubectl -n $(KUBE_NAMESPACE) get $${i} -o jsonpath="{.spec.initContainers[*].name}"`; do \
	RES=`kubectl -n $(KUBE_NAMESPACE) logs $${i} -c $${j} 2>/dev/null`; \
	echo "initContainer: $${j}"; echo "$${RES}"; \
	echo "---------------------------------------------------";\
	done; \
	echo "Main Pod logs for $${i}"; \
	echo "---------------------------------------------------"; \
	for j in `kubectl -n $(KUBE_NAMESPACE) get $${i} -o jsonpath="{.spec.containers[*].name}"`; do \
	RES=`kubectl -n $(KUBE_NAMESPACE) logs $${i} -c $${j} 2>/dev/null`; \
	echo "Container: $${j}"; echo "$${RES}"; \
	echo "---------------------------------------------------";\
	done; \
	echo "---------------------------------------------------"; \
	echo ""; echo ""; echo ""; \
	done

localip:  ## set local Minikube IP in /etc/hosts file for Ingress $(INGRESS_HOST)
	@new_ip=`minikube ip` && \
	existing_ip=`grep $(INGRESS_HOST) /etc/hosts || true` && \
	echo "New IP is: $${new_ip}" && \
	echo "Existing IP: $${existing_ip}" && \
	if [ -z "$${existing_ip}" ]; then echo "$${new_ip} $(INGRESS_HOST)" | sudo tee -a /etc/hosts; \
	else sudo perl -i -ne "s/\d+\.\d+.\d+\.\d+/$${new_ip}/ if /$(INGRESS_HOST)/; print" /etc/hosts; fi && \
	echo "/etc/hosts is now: " `grep $(INGRESS_HOST) /etc/hosts`

help:  ## show this help.
	@echo "make targets:"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ": .*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""; echo "make vars (+defaults):"
	@grep -E '^[0-9a-zA-Z_-]+ \?=.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = " \\?\\= "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

get_pods: ##lists the pods deploued for a particular namespace. @param: KUBE_NAMESPACE
	kubectl get pods -n $(KUBE_NAMESPACE)

get_versions: ## lists the container images used for particular pods
	kubectl get pods -l release=$(HELM_RELEASE) -n $(KUBE_NAMESPACE) -o jsonpath="{range .items[*]}{.metadata.name}{'\n'}{range .spec.containers[*]}{.name}{'\t'}{.image}{'\n\n'}{end}{'\n'}{end}{'\n'}"

traefik: ## install the helm chart for traefik (in the kube-system namespace). @param: EXTERNAL_IP (i.e. private ip of the master node).
	@TMP=`mktemp -d`; \
	$(helm_add_stable_repo) && \
	helm fetch stable/traefik --untar --untardir $$TMP && \
	helm template $(helm_install_shim) $$TMP/traefik -n traefik0 --namespace kube-system \
		--set externalIP="$(EXTERNAL_IP)" \
		| kubectl apply -n kube-system -f - && \
		rm -rf $$TMP ; \


delete_traefik: ## delete the helm chart for traefik. @param: EXTERNAL_IP
	@TMP=`mktemp -d`; \
	$(helm_add_stable_repo) && \
	helm fetch stable/traefik --untar --untardir $$TMP && \
	helm template $(helm_install_shim) $$TMP/traefik -n traefik0 --namespace kube-system \
		--set externalIP="$(EXTERNAL_IP)" \
		| kubectl delete -n kube-system -f - && \
		rm -rf $$TMP

gangway: ## install gangway authentication for gitlab (in the kube-system namespace). @param: CLIENT_ID, CLIENT_SECRET, INGRESS_HOST, CLUSTER_NAME, API_SERVER_IP, API_SERVER_PORT
	@TMP=`mktemp -d`; \
	$(helm_add_stable_repo) && \
	helm fetch stable/gangway --untar --untardir $$TMP && \
	helm template $(helm_install_shim) $$TMP/gangway -n gangway0 --namespace kube-system \
			--values resources/gangway.yaml \
			--set gangway.redirectURL="http://gangway.$(INGRESS_HOST)/callback" \
			--set gangway.clusterName="$(CLUSTER_NAME)" 	\
			--set gangway.clientID="$(CLIENT_ID)" 	\
			--set gangway.clientSecret="$(CLIENT_SECRET)" 	\
			--set gangway.apiServerURL="https://$(API_SERVER_IP):$(API_SERVER_PORT)" \
			--set ingress.hosts="{gangway.$(INGRESS_HOST)}" \
			| kubectl apply -n kube-system -f - && 	\
			rm -rf $$TMP

delete_gangway: ## delete install gangway authentication for gitlab. @param: CLIENT_ID, CLIENT_SECRET, INGRESS_HOST, CLUSTER_NAME, API_SERVER_IP, API_SERVER_PORT
	@TMP=`mktemp -d`; \
	$(helm_add_stable_repo) && \
	helm fetch stable/gangway --untar --untardir $$TMP && \
	helm template $(helm_install_shim) $$TMP/gangway -n gangway0 --namespace kube-system \
			--values resources/gangway.yaml \
			--set gangway.redirectURL="http://gangway.$(INGRESS_HOST)/callback" \
			--set gangway.clusterName="$(CLUSTER_NAME)" 	\
			--set gangway.clientID="$(CLIENT_ID)" 	\
			--set gangway.clientSecret="$(CLIENT_SECRET)" 	\
			--set gangway.apiServerURL="https://$(API_SERVER_IP):$(API_SERVER_PORT)" \
			--set ingress.hosts="{gangway.$(INGRESS_HOST)}" \
			| kubectl delete -n kube-system -f - && \
			rm -rf $$TMP

set_context: ## Set current kubectl context. @param: KUBE_NAMESPACE
	kubectl config set-context $$(kubectl config current-context) --namespace $${NAMESPACE:-$(KUBE_NAMESPACE)}

get_status:
	kubectl get pod,svc,deployments,pv,pvc,ingress -n $(KUBE_NAMESPACE)

redeploy: delete_all deploy_ordered get_status

wait:
	pods=$$( kubectl get pods -n $(KUBE_NAMESPACE) -o=jsonpath="{range .items[*]}{.metadata.name}{' '}{end}" ) && \
	for pod in $$pods ;  do \
		phase=$$(kubectl get pod -n $(KUBE_NAMESPACE) $$pod -o=jsonpath='{.status.phase}'); \
		if [ "$$phase" = "Succeeded" ]; then \
			echo $$pod $$phase; else \
			kubectl wait --for=condition=Ready -n $(KUBE_NAMESPACE) pod/$$pod; \
		fi; \
	done

#this is so that you can load dashboards previously saved, TODO: make the name of the pod variable
dump_dashboards:
	kubectl exec -i pod/mongodb-webjive-test-0 -n $(KUBE_NAMESPACE) -- mongodump --archive > webjive-dash.dump

load_dashboards:
	kubectl exec -i pod/mongodb-webjive-test-0 -n $(KUBE_NAMESPACE) -- mongorestore --archive < webjive-dash.dump

get_jupyter_port:
	@kubectl get service -l app=jupyter-oet-test -n $(KUBE_NAMESPACE)  -o jsonpath="{range .items[0]}{'Use this url:http://$(THIS_HOST):'}{.spec.ports[0].nodePort}{'\n'}{end}"

test_ssl:
	curl -v https://$(THIS_HOST) -H 'Host: $(INGRESS_HOST) '2>&1 | awk 'BEGIN { cert=0 } /^\* SSL connection/ { cert=1 } /^\*/ { if (cert) print }'

clear_certificates:
	rm charts/skampi/charts/webjive/data/tls.*
	rm charts/skampi/charts/tango-base/secrets/tls.*