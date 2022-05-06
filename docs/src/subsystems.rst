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


Telescope Monitoring and Control(TMC)
-------------------------------------

The Telescope Monitoring and Control(TMC) is part of the evolutionary prototype of the
SKA. The TMC is built from software modules which produce a number of different
types of artefacts. The components of the system are built as Docker images
which are deployed on a Kubernetes cluster using a Helm chart. The Docker
images depend on libraries containing common code.

The TMC has a hierarchy of control nodes for Mid and Low-
Central Node, Subarray Node, SDP Leaf Nodes, CSP Leaf Nodes, MCCS Leaf Nodes, Dish Leaf Nodes.

TMC Functionality includes: 

* [x] Monitoring and control functionality with hierarchy of nodes
* [x] Automatic control actions on Alerts using Elettra Alarm Handler
* [x] Simulator for DishMaster
* [x] Allocation and Deallocation of receptors to a Subarray
* [x] Commands and Events propagation
* [x] TANGO group commands
* [x] Conversion of Ra-Dec to Az-El coordinates using KATPoint for TMC-Mid
* [x] Calculate Az-El periodically in Dish Leaf Node and implement tracking functionality in the Dish simulator
* [x] Interface between the TMC and CSP:
  * [x] Implementation of CSP Master Leaf Node and CSP Subarray Leaf Node
  * [x] Monitor/subscribe CSP Master and CSP Subarray attributes from CSP Master Leaf Node and CSP Subarray Leaf Node respectively
  * [x] Use of CSP Master health to calculate overall Telescope Health (in Central Node Mid)
  * [x] Use of CSP Subarray health to calculate Subarray Node health state
  * [x] TelescopeOn command on Central Node to change CSP Master device and CSP Subarray device state to ON
  * [x] Configure the CSP for a simple scan
  * [x] Publish Delay coefficients at regular time interval (every 10 seconds) on CSP Subarray Leaf Node per Subarray
* [x] Interface between the TMC and SDP:
  * [x] Implementation of SDP Master Leaf Node and SDP Subarray Leaf Node
  * [x] Monitor/subscribe SDP Master and SDP Subarray attributes from SDP Master Leaf Node and SDP Subarray Leaf Node respectively
  * [x] Use of SDP Master health to calculate overall Telescope Health (in Central Node Mid) 
  * [x] Use of SDP Subarray health to calculate Subarray Node health state
  * [x] TelescopeOn command on Central Node to change SDP Master device and SDP Subarray device state to ON
  * [x] Configure the SDP for a simple scan
* [x] Interface between the TMC and MCCS:
  * [x] Implementation of MCCS Master Leaf Node and MCCS Subarray Leaf Node
  * [x] Monitor/subscribe MCCS Master and MCCS Subarray attributes from MCCS Master Leaf Node and MCCS Subarray Leaf Node respectively
  * [x] Use of MCCS Master health to calculate overall Telescope Health (in Central Node Low)
  * [x] Use of MCCS Subarray health to calculate Subarray Node health state
  * [x] TelescopeOn command on Central Node Low to change MCCS Master device state to ON
  * [X] AssignResources command on Central Node Low to change MCCS Subarray device state to ON and allocates resources to MCCS Subarray through MCCS Master
  * [x] Configure the MCCS for a simple scan
  * [x] TMC commands/functionality to execute entire obsevation cycle
  * [x] Telescope Startup
  * [x] AssignResources command to allocate resources to the SubarrayNode
  * [x] Execute Configure command for a Subarray
  * [x] Execute Scan and End the Scan
  * [x] End command on SubarrayNode to end the scheduling block
  * [x] ReleaseResources commands to deallocate resources from the SubarrayNode
  * [x] Telescope Standby
* [x] Configure and execute multiple scans for TMC-Mid
* [x] Implement the observation state model and state transitions as per [ADR-8.](https://confluence.skatelescope.org/pages/viewpage.action?pageId=105416556)
* [x] Calculate Geometric delay values (in seconds) per antenna on CSP Subarray Leaf Node
* [x] Convert delay values (in seconds) to 5th order polynomial coefficients for TMC-Mid
* [x] Abort an ongoing operation, and Restart the control nodes, catch exceptions in the AssignResource workflow, log the exception details and raise them to the calling components for TMC-Mid.
* [x] Implementation of obsReset functinality (as per ADR-8) in which resource allocation in Subarray is retained and only the scan configuration parameters are cleared for TMC-Mid.
* [x] Update the JSON strings (command inputs and attributes) in the TMC as per ADR-35

The components(CentralNode, SubarrayNode, Leaf Nodes) of the TMC system are integrated in the `TMC integration repository
<https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-integration>`_, which contains
the Helm chart to deploy the TMC. More details on the design of the TMC and how
to run it locally or in the integration environment can be found in the 
`documentation
<https://gitlab.com/ska-telescope/ska-tmc/ska-tmc-integration/-/blob/main/docs/src/getting_started/getting_started.rst>`_.