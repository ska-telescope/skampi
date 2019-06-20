# Set dir of Makefile to a variable to use later
MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
BASEDIR := $(notdir $(patsubst %/,%,$(dir $(MAKEPATH))))

# find IP addresses of this machine, setting THIS_HOST to the first address found
THIS_HOST := $(shell ifconfig | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)
DISPLAY := $(THIS_HOST):0
XAUTHORITYx ?= ${XAUTHORITY}
KUBE_NAMESPACE ?= default
HELM_RELEASE = test
HELM_CHART ?= tango-base
INGRESS_HOST ?= k8s-integration.minikube.local

# Vagrant
VAGRANT_VERSION = 2.2.4
V_BOX ?= ubuntu/bionic64
V_GUI ?= false
V_DISK_SIZE ?=  32GB
V_MEMORY ?=  8192
V_CPUS ?=  4
# V_IP ?= 172.200.0.25
V_IP ?= 172.16.0.92

# Minikube
DRIVER ?= true
USE_NGINX ?= false

# activate remote debugger for VSCode (ptvsd)
REMOTE_DEBUG ?= false

# define overides for above variables in here
-include PrivateRules.mak

# Format the disk size for minikube - 999g
FORMATTED_DISK_SIZE = $(shell echo $(V_DISK_SIZE) | sed 's/[^0-9]*//g')g


.PHONY: vars k8s apply logs rm show deploy delete ls podlogs launch-tiller tiller-acls namespace help
.DEFAULT_GOAL := help

vars: ## Display variables - pass in DISPLAY and XAUTHORITY
	@echo "DISPLAY: $(DISPLAY)"
	@echo "XAUTHORITY: $(XAUTHORITYx)"
	@echo "Namespace: $(KUBE_NAMESPACE)"

k8s: ## Which kubernetes are we connected to
	@echo "Kubernetes cluster-info:"
	@kubectl cluster-info
	@echo ""
	@echo "kubectl version:"
	@kubectl version
	@echo ""
	@echo "Helm version:"
	@helm version --client

apply: ## apply resource descriptor k8s.yml
	kubectl apply -n $(KUBE_NAMESPACE) -f k8s.yml

logs: ## POD logs for descriptor
	@for i in `kubectl -n $(KUBE_NAMESPACE) get pods -l group=example -o=name`; \
	do echo "-------------------"; \
	echo "Logs for $$i"; \
	kubectl -n $(KUBE_NAMESPACE) logs $$i; \
	done

rm: ## delete applied resources
	kubectl delete -n $(KUBE_NAMESPACE) -f k8s.yml

namespace: ## create the kubernetes namespace
	kubectl describe namespace $(KUBE_NAMESPACE) || kubectl create namespace $(KUBE_NAMESPACE)

deploy: namespace  ## deploy the helm chart
	@helm template charts/$(HELM_CHART)/ --name $(HELM_RELEASE) \
				 --namespace $(KUBE_NAMESPACE) \
	             --tiller-namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITYx)" \
	             --set tangoexample.debug="$(REMOTE_DEBUG)" | kubectl -n $(KUBE_NAMESPACE) apply -f -

show: ## show the helm chart
	@helm template charts/$(HELM_CHART)/ --name $(HELM_RELEASE) \
				 --namespace $(KUBE_NAMESPACE) \
	             --tiller-namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITYx)" \
	             --set tangoexample.debug="$(REMOTE_DEBUG)"

delete: ## delete the helm chart release
	@helm template charts/$(HELM_CHART)/ --name $(HELM_RELEASE) \
				 --namespace $(KUBE_NAMESPACE) \
	             --tiller-namespace $(KUBE_NAMESPACE) \
	             --set display="$(DISPLAY)" \
	             --set xauthority="$(XAUTHORITYx)" \
	             --set tangoexample.debug="$(REMOTE_DEBUG)" | kubectl -n $(KUBE_NAMESPACE) delete -f -


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

vagrant_install:  ## install vagrant and vagrant-disksize on Ubuntu
	@VER=`vagrant version 2>/dev/null | grep Installed | awk '{print $$3}' | sed 's/\./ /g'` && \
	echo "VER: $${VER}" && \
	MAJ=`echo $${VER} | awk '{print $$1}'` && \
	echo "MAJOR: $${MAJ}" && \
	MIN=`echo $${VER} | awk '{print $$2}'` && \
	echo "MINOR: $${MIN}" && \
	if [ "0$${MAJ}" -ge "2" ] || [ "0$${MIN}" -ge "1" ]; then \
	  echo "Vagrant is OK - "`vagrant version`; \
	else \
	  cd /tmp/ && wget https://releases.hashicorp.com/vagrant/$(VAGRANT_VERSION)/vagrant_$(VAGRANT_VERSION)_x86_64.deb && \
	   sudo dpkg -i /tmp/vagrant_$(VAGRANT_VERSION)_x86_64.deb && \
	  rm -f /tmp/vagrant_$(VAGRANT_VERSION)_x86_64.deb; \
	fi
	@vagrant plugin list | grep vagrant-disksize >/dev/null; RES=$$? && \
	if [ "$${RES}" -eq "1" ]; then \
	  vagrant plugin install vagrant-disksize; \
	fi
	@vagrant plugin list

vagrant_env:  ## vagrant box settings
	@echo "V_BOX: $(V_BOX)"
	@echo "V_GUI: $(V_GUI)"
	@echo "V_DISK_SIZE: $(V_DISK_SIZE)"
	@echo "V_MEMORY: $(V_MEMORY)"
	@echo "V_CPUS: $(V_CPUS)"
	@echo "V_IP: $(V_IP)"

vagrant_up: vagrant_env  ## startup minikube in vagrant
	V_BOX=$(V_BOX) \
	V_DISK_SIZE=$(V_DISK_SIZE) \
	V_MEMORY=$(V_MEMORY) \
	V_CPUS=$(V_CPUS) \
	V_IP=$(V_IP) \
	V_GUI=$(V_GUI) \
		vagrant up

vagrant_down: vagrant_env  ## destroy vagrant instance
	V_BOX=$(V_BOX) \
	V_DISK_SIZE=$(V_DISK_SIZE) \
	V_MEMORY=$(V_MEMORY) \
	V_CPUS=$(V_CPUS) \
	V_IP=$(V_IP) \
	V_GUI=$(V_GUI) \
		vagrant destroy -f

vagrantip:  ## set Vagrant Minikube IP in /etc/hosts file for Ingress $(INGRESS_HOST)
	@existing_ip=`grep $(INGRESS_HOST) /etc/hosts || true` && \
	echo "New IP is: $(V_IP)" && \
	echo "Existing IP: $${existing_ip}" && \
	if [ -z "$${existing_ip}" ]; then echo "$(V_IP) $(INGRESS_HOST)" | sudo tee -a /etc/hosts; \
	else sudo perl -i -ne "s/\d+\.\d+.\d+\.\d+/$(V_IP)/ if /$(INGRESS_HOST)/; print" /etc/hosts; fi && \
	echo "/etc/hosts is now: " `grep $(INGRESS_HOST) /etc/hosts`

minikube:  ## Ansible playbook for install and launching Minikube
	PYTHONUNBUFFERED=1 ANSIBLE_FORCE_COLOR=true ANSIBLE_CONFIG='playbooks/ansible-local.cfg' \
	ansible-playbook --inventory=playbooks/hosts \
					 -v \
	                 --limit=development \
					 --extra-vars='{"use_driver": $(DRIVER), "use_nginx": $(USE_NGINX), "minikube_disk_size": $(FORMATTED_DISK_SIZE), "minikube_memory": $(V_MEMORY), "minikube_cpus": $(V_CPUS)}' \
					 playbooks/deploy_minikube.yml

help:  ## show this help.
	@echo "make targets:"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ": .*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""; echo "make vars (+defaults):"
	@grep -E '^[0-9a-zA-Z_-]+ \?=.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = " \\?\\= "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
