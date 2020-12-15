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
    Makefile:clean                 clean out references to chart tgz's
    Makefile:delete_namespace      delete the kubernetes namespace
    Makefile:delete_sdp_namespace  delete the kubernetes SDP namespace
    Makefile:get_versions          lists the container images used for particular pods
    Makefile:help                  show this help.
    Makefile:install-or-upgrade    install or upgrade the release
    Makefile:install               install the helm chart on the namespace KUBE_NAMESPACE
    Makefile:k8s                   Which kubernetes are we connected to
    Makefile:lint                  lint the HELM_CHART of the helm chart
    Makefile:lint_all              lint ALL of the helm chart
    Makefile:logs                  POD logs for descriptor
    ...
    make vars (+defaults):
    Makefile:API_SERVER_IP         $(THIS_HOST)# Api server IP of k8s
    Makefile:API_SERVER_PORT       6443# Api server port of k8s
    Makefile:CHART_SET ?=#for additional flags you want to set when deploying (default empty) 
    Makefile:CLIENT_ID             417ea12283741e0d74b22778d2dd3f5d0dcee78828c6e9a8fd5e8589025b8d2f# For the gangway kubectl setup, taken from Gitlab
    Makefile:CLIENT_SECRET         27a5830ca37bd1956b2a38d747a04ae9414f9f411af300493600acc7ebe6107f# For the gangway kubectl setup, taken from Gitlab
    Makefile:CLUSTER_NAME          integration.cluster# For the gangway kubectl setup
    Makefile:DEPLOYMENT_CONFIGURATION skamid## umbrella chart to work with
    Makefile:DOMAIN_TAG            test## always set for TANGO_DATABASE_DS


All the following deployments are deployed using using the same makefile.

Deploy
------

Skampi enables the deployment of two separate products as charts

- **mvp-low:** (DEPLOYMENT_CONFIGURATION = skalow)
- **mvp-mid:** (DEPLOYMENT_CONFIGURATION = skamid)

After setting the variable, run the following:

.. code-block:: bash

    make install

It isn't necessary to always delete and install from scratch once you have a running deployment

.. code-block:: bash

    make upgrade_chart

The default release name (instance name of the chart) is *test*, change using env variable:

**HELM_RELEASE=** *<your release name>*

To uninstall :

.. code-block:: bash

    make uninstall

To uninstall and the install from scratch:

.. code-block:: bash

    reinstall-chart


VALUES
==========
 
The deployments of the low and mid charts are parametrized, enabling the user to have a wide degree of configuration choices. 
These parameters (values in helm nomenclature) can be set by a user using different layers, each capable of overriding the lower one:

1.  Makefile: values are set based on variables within the makefile (e.g. `webjive.ingress.hostname` ) the default values of which can be set by the user upon calling the make targets.

2.  Values file: A user can define a values file that refer to values for the mid or low chart the location of which is set by the makefile variable  **VALUES**. (note the values file can also refer to values from specific subcharts but this should only be used during diagnostic work)


The default values file can be found at `./values.yaml` while the values used for testing the pipeline is found under `pipeline.yaml`




