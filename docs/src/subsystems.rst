.. _subsystems:

SKAMPI Sub-systems
******************

This page briefly describes the various sub-systems integrated within SKAMPI, and
provides useful links to the projects. You can also read more about the various
Helm modules and their dependencies, which make up SKAMPI at |helm_modules|.

.. |helm_modules| raw:: html

    <a href="https://confluence.skatelescope.org/display/SWSI/SKAMPI%3A+Helm+modules+and+dependencies+view" target="_blank">this Confluence page</a>


SDP (Science Data Processor)
============================

The SDP is the system of the telescope responsible for processing observed data into
required data products, preserving these products, and delivering them to
the SKA Regional Centres.

- |sdp_general|
- |sdp_in_skampi|

.. |sdp_general| raw:: html

    <a href="https://developer.skao.int/en/latest/projects/area/sdp.html" target="_blank">SDP General Overview and Components</a>

.. |sdp_in_skampi| raw:: html

    <a href="https://developer.skao.int/projects/ska-sdp-integration/en/latest/running/skampi.html" target="_blank">Interacting with SDP within SKAMPI</a>


OET (Observation Execution Tool)
================================

The OET is an application, which provides on-demand Python script
(telescope control script) execution for the SKA.

- |oet_rest_layers|
- |oet_scripts|
- |script_execution|
- |oet_jupyter|

.. |oet_rest_layers| raw:: html

    <a href="https://developer.skao.int/projects/ska-telescope-ska-oso-oet/en/latest/index.html" target="_blank">OET Rest layers</a>

.. |oet_scripts| raw:: html

    <a href="https://developer.skao.int/projects/ska-telescope-ska-oso-scripting/en/latest/index.html" target="_blank">OET scripts</a>

.. |script_execution| raw:: html

    <a href="https://developer.skao.int/projects/ska-telescope-ska-oso-scripting/en/latest/script_execution.html" target="_blank">Telescope control script execution</a>

.. |oet_jupyter| raw:: html

    <a href="https://developer.skao.int/projects/ska-telescope-ska-oso-scripting/en/latest/oet_with_skampi.html#accessing-jupyter-on-skampi" target="_blank">OET Jupyter Notebooks for direct SKAMPI interactions</a>

Taranta
===============

The Taranta deployment from SKAMPI consists of four components. Following the deployment steps to enable Taranta, a deployment can be made according to the applicable requirements for the environment.

Please refer to the |taranta_docs| for further information.

.. todo:: (the link provided is not to the latest documentation version - update this link as soons as Taranta namechange is on https://taranta.readthedocs.io/en/master/)

.. |taranta_docs| raw:: html

    <a href="https://taranta.readthedocs.io/en/sp-1406/" target="_blank">Taranta documentation</a>

Taranta specific deployment notes for Minikube environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Two important aspects for developers deploying Taranta on their local Minikube environment, are the resource requirements, and the need for authorization if the user wants to be able to log into the web UI.

Enabling Taranta with authorization for the Dashboard UI
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

See the note in the |taranta_readme|.

.. |taranta_readme| raw:: html

    <a href="https://gitlab.com/ska-telescope/ska-skampi#taranta-enabled" target="_blank">README</a>

Resource Requirements
+++++++++++++++++++++

For the Resource requirements, if it becomes apparent that the default scaled deployment of TangoGQL (replicas=3) is too much, this can be rectified by scaling down the replicaset.

As example (assuming you're using integration namespace):

.. code-block:: console

    $ kubectl  get all -n integration -l app=tangogql-ska-taranta-test
    NAME                              READY   STATUS    RESTARTS   AGE
    pod/tangogql-ska-taranta-test-0   1/1     Running   0          18h
    pod/tangogql-ska-taranta-test-1   1/1     Running   0          18h
    pod/tangogql-ska-taranta-test-2   0/1     Pending   0          3s

    NAME                                TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
    service/tangogql-ska-taranta-test   ClusterIP   10.105.252.8   <none>        5004/TCP   18h

    NAME                                         READY   AGE
    statefulset.apps/tangogql-ska-taranta-test   2/3     18h

That meant that the third pod was not deployed for some reason. Let's find out why:

.. code-block:: console

    $ kubectl  describe pod/tangogql-ska-taranta-test-2 -n integration
    ... snip ...
    Events:
    Type     Reason            Age   From               Message
    ----     ------            ----  ----               -------
    Warning  FailedScheduling  69s   default-scheduler  0/1 nodes are available: 1 Insufficient cpu.

So let's scale it down to only one replica:

.. code-block:: console

    $ kubectl -n integration scale statefulset tangogql-ska-taranta-test --replicas 1
    statefulset.apps/tangogql-ska-taranta-test scaled

Verify the scaling worked:

.. code-block:: console

    $ kubectl get all -n integration -l app=tangogql-ska-taranta-test                
    NAME                              READY   STATUS    RESTARTS   AGE
    pod/tangogql-ska-taranta-test-0   1/1     Running   0          18h

    NAME                                TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
    service/tangogql-ska-taranta-test   ClusterIP   10.105.252.8   <none>        5004/TCP   18h

    NAME                                         READY   AGE
    statefulset.apps/tangogql-ska-taranta-test   1/1     18h

TMC (Telescope Monitoring and Control)
======================================

The Telescope Monitor and Control (TMC) is the software module identified to perform the telescope management, 
and data management functions of the Telescope Manager. 
Main responsibilities identified for TMC are:

- General monitoring and control of the telescope
- Support execution of astronomical observations
- Manage telescope hardware and software subsystems in order to perform astronomical observations
- Manage the data to support operators, maintainers, engineers and science users to achieve their goals
- Determine telescope state.

To support these responsibilities, the TMC performs high-level functions such as Observation Execution, 
Monitoring and Control of Telescope, Resource Management, Configuration Management, Alarm and Fault Management, 
and Telescope Data Management (Historical data and Real time data).
These high level functions are again divided into lower level functions to perform the specific functionalities.

TMC Architecture
++++++++++++++++

The TMC is a distributed system having multiple components to fulfil its functionalities. For carrying out 
observation execution, monitoring and control it has a hierarchy of control nodes for Mid and Low-
Central Node, Subarray Node, SDP Leaf Nodes, CSP Leaf Nodes, MCCS Leaf Nodes, Dish Leaf Nodes.
The detailed architecture of the TMC can be found in `TMC Architecture<https://confluence.skatelescope.org/display/SWSI/TMC+Architecture>`
section in the Solution Intent.

APIs
++++

.. toctree::
    :titlesonly:
    :glob:

    Operational Monitoring and Control<apis/operational_mandc>
    Observation Execution<apis/obs_mandc>

The components(CentralNode, SubarrayNode, Leaf Nodes) of the TMC system are integrated in the `TMC integration repository
<https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-integration>`, which contains
the Helm chart to deploy the TMC. More details on the design of the TMC and how
to run it locally or in the integration environment can be found in the `Documentation 
<https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-integration/-/blob/main/docs/src/getting_started/getting_started.rst>`_
