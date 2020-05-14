==========
Deployment
==========

SKAMPI deployment must be robust, repeatable, and idempotent. In this page, we will
explain the multiple flavours of deployment for different configurations.


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
 
In SKAMPI, we separated the parameters into three levels. 

The first one is inside the Makefile of the repository and is the top priority meaning that it overrides all the parameters in any level below. Parameters of this level are, for instance, the KUBE_NAMESPACE or INGRESS_HOST (for the complete list of parameters, please refer to the Makefile (i.e. running *make* in the command line)) and they can be personalized with the file PrivateRules.mk. 

The second level is specified with the values file (according to the helm formality). The file can be selected with the parameter VALUES of the Makefile (default is values.yaml present in the root folder of skampi). Those parameters ovveride all the parameters present in the charts which represent the lower level parameters. 


Forward Oriented deployment
===========================

With the help of the above parameter levels it is possible to have a forward oriented deployment which means that there is the ability to declarative select the charts needed for a particular configuration of the deployment. Selecting a chart with the values file means that we need to disable or enable the charts that are needed for the specific deployment. 

In the skampi repository, there are 2 examples of values files, one that has everything enabled (pipeline.yaml) and another one with has come charts disabled (values.yaml). The latter disable the logging chart and the archiver chart and it has been thought for a minikube environment. 

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

The pipeline.yaml file is the one used in the gitlab pipeline for deploying the complete skampi deployment. 
