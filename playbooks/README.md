

[![Documentation Status](https://readthedocs.org/projects/ska-docker/badge/?version=latest)](https://developer.skatelescope.org/projects/k8s-integration/en/latest/?badge=latest)


Ansible Playbook for Kubernetes
===============================

The following are a set of instructions for deploying Kubernetes either directly locally or on a Vagrant VirtualBox.  It has been tested on minikube v1.1.1 with Kubernetes v1.14.3 on Ubuntu 18.04, using Vagrant 2.2.4.

The Aim
=======

The aim of these instructions, scripts, and playbook+roles is to provide a canned locally available Kubernetes development environment.  This environment will contain:

* Kubernetes at 1.14+ on Docker
* Tools: `kubectl` and `helm` configured with a local [Tiller-less Helm](https://rimusz.net/tillerless-helm)
* A running Ingress Controller
* [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/) implemented with Calico as the Pod network
* This project mounted into the Guest OS at `/vagrant` so that the associated Helm Charts can be run


make
====

All actions are available as targets in the `Makefile` - type `make help` to get the list of available targets, and variables that can be supplied at the command line.  To make your own variables permanent, place them in a `PrivateRules.mak` file in the root of this project.
```
$ make
make targets:
Makefile:apply                 apply resource descriptor k8s.yml
Makefile:delete                delete the helm chart release
Makefile:deploy                deploy the helm chart
Makefile:help                  show this help.
Makefile:k8s                   Which kubernetes are we connected to
Makefile:localip               set local Minikube IP in /etc/hosts file for Ingress $(INGRESS_HOST)
Makefile:logs                  POD logs for descriptor
Makefile:minikube              Ansible playbook for install and launching Minikube
Makefile:namespace             create the kubernetes namespace
Makefile:poddescribe           describe Pods executed from Helm chart
Makefile:podlogs               show Helm chart POD logs
Makefile:rm                    delete applied resources
Makefile:show                  show the helm chart
Makefile:vagrant_down          destroy vagrant instance
Makefile:vagrant_env           vagrant box settings
Makefile:vagrant_install       install vagrant and vagrant-disksize on Ubuntu
Makefile:vagrantip             set Vagrant Minikube IP in /etc/hosts file for Ingress $(INGRESS_HOST)
Makefile:vagrant_up            startup minikube in vagrant
Makefile:vars                  Display variables - pass in DISPLAY and XAUTHORITY

make vars (+defaults):
Makefile:DRIVER                false
Makefile:HELM_CHART            tango-base
Makefile:INGRESS_HOST          k8s-integration.minikube.local
Makefile:KUBE_NAMESPACE        default
Makefile:REMOTE_DEBUG          false
Makefile:V_BOX                 ubuntu/bionic64
Makefile:V_CPUS                 2
Makefile:V_DISK_SIZE            50GB
Makefile:V_IP                  172.200.0.25
Makefile:V_MEMORY               4096
Makefile:XAUTHORITYx           ${XAUTHORITY}
```

Vagrant
=======

Install Vagrant and VirtualBox - on Ubuntu 18.04+ use:
```
apt install virtualbox vagrant
```
and then:
```
make vagrant_install
```
This will ensure that Vagrant is at minimally working level, and that the Vagrant plugin `vagrant-disksize` is installed which is required for the guest base box disk resizing.

There are two tested options for Vagrant base boxes - `ubuntu/bionic64`, and `fedora/29-cloud-base`.  These can be supplied by var `V_BOX`.

Adjust the vcpus, memory, and initial disk size with: `V_CPUS`, `V_MEMORY`, and `V_DISK_SIZE` as above.

Minikube
========

Once Vagrant and VirtualBox are installed, launching a guest OS and installing Minikube with Ansible is carried out with the following:
```
make vagrant_up
```

Once successfully completed, inspect Minikube by ssh'ing onto the box with `vagrant ssh`, where all the usual `kubectl` capabilities are available:
```
kubectl get all --all-namespaces
```
The repository has been shared into the guest OS in `/vagrant` where the associated Helm Charts ane `make` commands are available.


Minikube direct install (for the brave)
=======================================

Minikube can also be installed directly onto your Debian or RedHat based machine with:
```
make minikube
```
***WARNING*** This will overwrite anything that you have locally installed for `docker`, `helm`, `kubectl`, and `minikube` which could be disastrous if you have an existing and customised configuration.
