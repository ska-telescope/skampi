==========
Deployment
==========
SCAMPI deployment must be robust, repeatable, and idempotent. 
We have multiple flavours of deployment for different configurations.

Flavours
========

By running *make* in the command line, we can see all 
the **targets** and **arguments** (and their defaults) available.

.. code-block:: bash

    [user@pc skampi]$ make
    make targets:
    Makefile:delete_all            delete ALL of the helm chart release
    Makefile:delete                delete the helm chart release. @param: same as deploy_all, plus HELM_CHART
    Makefile:delete_etcd           Remove etcd-operator from namespace
    Makefile:delete_gangway        delete install gangway authentication for gitlab. @param: CLIENT_ID, CLIENT_SECRET, INGRESS_HOST, CLUSTER_NAME, API_SERVER_IP, API_SERVER_PORT
    Makefile:delete_traefik        delete the helm chart for traefik. @param: EXTERNAL_IP
    ...
    make vars (+defaults):
    dev-testing.mk:hostPort        2020
    dev-testing.mk:k8_path         $(shell echo ~/.minikube)
    dev-testing.mk:kube_path       $(shell echo ~/.kube)
    Makefile:API_SERVER_IP         $(THIS_HOST)## Api server IP of k8s
    
    Makefile:API_SERVER_PORT       6443		# Api server port of k8s


All the next deployments are deployed using using the same makefile.

Deploy
------

Deploy only one Helm Chart available at charts directory.

Basic arguments:

- **KUBE_NAMESPACE** - integration *default*
- **HELM_CHART** - tango-base *default*

.. code-block:: bash

    make deploy KUBE_NAMESPACE=integration HELM_CHART=tmc-proto


Deploy All
----------

Deploy every helm chart inside charts directory.

Basic parameters:

- **KUBE_NAMESPACE** - integration *default*

.. code-block:: bash

    make deploy_all KUBE_NAMESPACE=integration
    
    
Deploy All with Order
---------------------

Deploy every helm chart inside charts directory order by its dependencies.

Basic parameters:

- **KUBE_NAMESPACE** - integration *default*

.. code-block:: bash

    make deploy_ord KUBE_NAMESPACE=integration


Parameters
==========
 
In SKAMPI, we separated the parameters into two levels. 
The first one can change the behaviour of the makefile,
and the second level can only change the arguments in each chart.

Level 1
------

The first one is inside the Makefile of the repository and is the top priority 
meaning that it overrides all the parameters in any level below. We have three ways
to customize these parameters and they are prioritize in this order (from most to last
important):

1.  Command-line arguments - make deploy_ord **KUBE_NAMESPACE=integration**;
2.  PrivateRules.mak - Create this file and add arguments. Ex: **HELM_CHART = logging**;
3.  *Makefile* defaults - All the defaults are available by running **make** in the command-line.

Level 2
-------

The second level is specified with the 
`Values Files <https://helm.sh/docs/chart_template_guide/values_files/>`_. 

The priority file is the root directory and goes along the deploy commands with 
*values.yaml* by default but that could change using the *VALUES* argument in the *makefile*.

.. code-block:: bash

    elastic:
        enabled: false
    fluentd:
        enabled: false
    kibana:
        enabled: false
    tests:
        enabled: false
    hdbppdb:
        enabled: false
    archiver:
        enabled: false

    minikube: true

This root values file overrides the *values.yaml* file inside each chart. 
All chart values files can also be changed to customize your deployment needs.

In the skampi repository, there are 2 examples of values files, one that has everything 
enabled (pipeline.yaml) and another one with has come charts disabled (values.yaml). 
The latter disable the logging chart and the archiver chart and it has been thought for a 
minikube environment. 


Forward Oriented Deployment
===========================

With the help of the above parameter levels it is possible to have a forward oriented 
deployment which means that there is the ability to declarative select the charts needed 
for a particular configuration of the deployment. Selecting a chart with the values file 
means that we need to disable or enable the charts that are needed for the specific deployment.









