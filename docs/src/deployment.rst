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
 
In SKAMPI, we separated the parameters into two levels. 
The first one can change the the behaviour of the makefile
and the second level only change the arguments in each chart.

Level 1
-------

We have this hierarchy in place:

1.  Command-line arguments - make deploy_ord **KUBE_NAMESPACE=integration**;
2.  PrivateRules.mak - Create this file and add arguments. Ex: *HELM_CHART = logging*;
3.  *Makefile* defaults - All the defaults are available by running *make* in the command-line.



Level 2
-------
Charts
======

Forward Oriented
================