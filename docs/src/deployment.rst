==========
Deployment
==========

SKAMPI deployment must be robust, repeatable, and idempotent. In this page, we will
explain the multiple flavours of deployment for different configurations.


Flavours
========

All the next deployments are deployed using using the makefile.

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



Level 1
-------

.. code-block:: bash

    # Parameter description
    ARGUMENT := *default*

    # Set dir of Makefile to a variable to use later
    MAKEPATH := $(abspath $(lastword $(MAKEFILE_LIST)))

    # Set base directory
    BASEDIR := $(notdir $(patsubst %/,%,$(dir $(MAKEPATH))))

    # find IP addresses of this machine, setting THIS_HOST to the first address found
    THIS_HOST := $(shell (ip a 2> /dev/null || ifconfig) | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)

    # Set display IP
    DISPLAY := $(THIS_HOST):0

    #
    XAUTHORITYx ?= ${XAUTHORITY}

    # Kubernetes Namespace
    KUBE_NAMESPACE ?= integration

    # Kubernetes Namespace to use for SDP dynamic deployments
    KUBE_NAMESPACE_SDP ?= $(KUBE_NAMESPACE)-sdp 

    # Helm release name
    HELM_RELEASE ?= test

    # Helm Chart to install (see ./charts)
    HELM_CHART ?= tango-base

    # Helm Chart to install (see ./charts)
    HELM_CHART_TEST ?= tests

    # Ingress HTTP hostname
    INGRESS_HOST ?= integration.engageska-portugal.pt
    
    # Use NGINX as the Ingress Controller
    USE_NGINX ?= false

    # Api server IP of k8s
    API_SERVER_IP ?= $(THIS_HOST)

    # Api server port of k8s
    API_SERVER_PORT ?= 6443

    # For traefik installation
    EXTERNAL_IP ?= $(THIS_HOST)

    # For the gangway kubectl setup
    CLUSTER_NAME ?= integration.cluster

    # For the gangway kubectl setup, taken from Gitlab
    CLIENT_ID ?= 417ea12283741e0d74b22778d2dd3f5d0dcee78828c6e9a8fd5e8589025b8d2f

    # For the gangway kubectl setup, taken from Gitlab
    CLIENT_SECRET ?= *secret*

    #for additional flags you want to set when deploying (default empty)
    CHART_SET ?= 

    
    VALUES ?= values.yaml



Level 2
-------
Charts
======

Forward Oriented
================