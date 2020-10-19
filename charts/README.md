SKA Umbrella charts for MVP Mid and MVP Low
===========================================

This charts folder is based on https://gitlab.com/ska-telescope/ska-umbrellas and presents two set of working charts defined as umbrella charts which include for SKA-Low the following charts:

* tango-base, 
* webjive, 
* mccs-low.

For SKA-Mid the umbrella chart contains the following charts:


* etcd-operator,
* tango-base,
* cbf-proto,
* csp-proto,
* sdp-prototype,
* tmc-proto,
* oet,
* archiver,
* skuid,
* dsh-lmc-prototype,
* webjive, 
* logging.

The values files of the two umbrella charts may be used to override the values for its sub-charts including the resources (requests and limits). For more information relating to the inheritance pattern of Helm Charts see https://helm.sh/docs/chart_template_guide/subcharts_and_globals

Makefile
--------

The charts can be installed from the root of the SKAMPI repository but in this section we include also a simplified Makefile for installing the charts into a k8s cluster, like for example a minikube. Relevant targets are:

To launch the SKA-MID suite in the integration namespace use:
```
$ make install KUBE_NAMESPACE=integration DEPLOYMENT_CONFIGURATION=skamid
```

To clean up that Helm Chart release:
```
$make uninstall KUBE_NAMESPACE=integration DEPLOYMENT_CONFIGURATION=skamid
```
For SKA-LOW use DEPLOYMENT_CONFIGURATION=skalow


