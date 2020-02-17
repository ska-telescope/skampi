Testing SKAMPI 
==============
The SKA MPI codebase ultimately holds all the information required to deploy and configure the complete prototype.
This information is encapsulated as a collection of `Helm <https://helm.sh/>`_ charts, Makefiles and any other
scripts, components to support its test and deployment.

This page outlines the various categories of testing and approaches one can employ to test various aspects of SKA MPI prototype that can
be implemented in this repository.

Minikube Testing Environment - EngageSKA Openstack
--------------------------------------------------

Minikube is a tool that makes it easy to run Kubernetes locally. Minikube runs a single-node Kubernetes cluster 
inside a Virtual Machine (VM) inside an instance in Openstack.

Create a Virtual Machine
^^^^^^^^^^^^^^^^^^^^^^

The first step is to create a Virtual Machine in EngageSKA Openstack: 
https://developerskatelescopeorg.readthedocs.io/en/latest/services/ait_performance_env.html. 
The recommended specifications are:

- Volume Size: 100 GB
- Image: Ubuntu 18.04
- Flavor: m2.small

Create and test the environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once this VM is up and running, we need to run the ansile-playbooks for creating a development environment and the SHAMPI environment:

1. Install Ansible: https://developer.skatelescope.org/projects/ansible-playbooks/en/latest/README.html#ansibleplaybook
2. Install the integration environment: https://developer.skatelescope.org/projects/ansible-playbooks/en/latest/README.html#skampi

Finally, we are going to test this installation with one project example. Just run these instructions to verify your installation.

.. code-block:: bash

    # Create Environment
    git clone https://gitlab.com/ska-telescope/ansible-playbooks.git
    cd ansible-playbooks
    ansible-playbook -i hosts deploy_tangoenv.yml
    ansible-playbook -i hosts deploy_skampi.yml
    sudo reboot
    # Run Project
    git clone https://gitlab.com/ska-telescope/skampi.git
    cd skampi/
    make deploy_all KUBE_NAMESPACE=integration

Kubernets Testing Environments
------------------------------
At the moment 3 k8s multi-node clusters are available for testing purpose: 

+--------------------------+-----------------------------------------------------------------------------------------------------------+
| Cluster name             | Information                                                                                               |
+==========================+===========================================================================================================+
| *engageska-k8s-master*   | - 1 master, 4 worker nodes                                                                                |
|                          | - working in the skampi pipeline                                                                          |
|                          | - A&A not available                                                                                       |
+--------------------------+-----------------------------------------------------------------------------------------------------------+
| *engageska-k8s-v2*       | - 1 master, 2 worker nodes                                                                                |
|                          | - working in the skampi pipeline                                                                          |
|                          | - A&A available. To work with it the file /etc/hosts has to be modified with the following lines:         |
|                          | .. code-block:: bash                                                                                      |
|                          |                                                                                                           |
|                          |      192.168.93.46	gangway.kubernetes-v2.engageska-portugal.pt                                            |
|                          |                                                                                                           |
+--------------------------+-----------------------------------------------------------------------------------------------------------+
| *kubernetes-cipro*       | - 1 master, 2 worker nodes                                                                                |
|                          | - not working in the skampi pipeline                                                                      |
|                          | - A&A available. To work with it the file /etc/hosts has to be modified with the following lines:         |
|                          | .. code-block:: bash                                                                                      |
|                          |                                                                                                           |
|                          |      192.168.93.46	gangway.kubernetes-cipro.engageska-portugal.pt                                         |
|                          |                                                                                                           |
+--------------------------+-----------------------------------------------------------------------------------------------------------+

Kubectl setup
^^^^^^^^^^^^^

If a cluster has the A&A module enabled it is possible to generate the instructions to let the local kubectl work with it. In order To do that, once modified the file /etc/hosts as explained above, open the [gangway](https://github.com/heptiolabs/gangway) url for `engageska-k8s-v2 <http://gangway.kubernetes-v2.engageska-portugal.pt>`_ or `kubernetes-cipro <http://gangway.kubernetes-cipro.engageska-portugal.pt >`_.
The *Sign In* button will redirect to gitlab.com for authentication. Once authenticated it will appear the set of commands to setup the local kubectl as shown below. 

.. image:: _static/img/signin.png
    :alt: Gangway Sign In

.. image:: _static/img/kubectl.png
    :alt: Kubectl setup

The following namespaces are available for use: "integration", "sdp", "csp", "button", "ncra", "karoo". For creating new namespaces or for any authorization request, contact the system team.

Visual Studio Code Remote Access
--------------------------------

Visual Studio Code Remote Development allows you to use a container, remote machine, or the Windows Subsystem for Linux (WSL) as a 
full-featured development environment.

No source code needs to be on your local machine. Each extension in the Remote Development extension pack can run commands 
and other extensions directly inside a container, in WSL, or on a remote machine so that everything feels like it does when you run locally.

.. image:: _static/img/architecture.png 
    :alt: SKAMPI Gitlab CI pipeline

Install Extension
^^^^^^^^^^^^^^^^^
Before everything, we need to install the Remote Development extension from vscode.


.. image:: _static/img/vscode-installExtension.png
    :alt: SKAMPI Gitlab CI pipeline


Connect to Openstack Virtual Machine - Option 1
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With the previous VM successfully up and running, 
we can successfully use *vscode* to create a vscode server inside the VM so we can connect to it.

First, we have to make sure that the local ssh configurations are correct on the ``home/$USERNAME/.ssh/`` directory. 
The private key associated with this VM needs to have the filename ``id_rsa`` and 
the ``config`` file with the VM specifications.

.. code-block:: bash

    Host $VM_NAME
        HostName $floating_IP
        User ubuntu

After this, just launch the remote extension (bottom left icon or use the shortcut "ctrl+shift+P") 
and select ``Remote-SSH: Connect to Host...`` and select the ``$VM_NAME`` connection you previously created.

Connect to Kubernets - Option 2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Connection establish
^^^^^^^^^^^^^^^^^^^^

Finally, the vscode will install everything on its own, and establish the SSH connection.

.. image:: _static/img/vscode-connection.png
    :alt: SKAMPI Gitlab CI pipeline


In this new instance of vscode, you can create/edit files and directories, install extensions and have direct access to the VM terminal.

Testing Infrastructure as Code
------------------------------
There is a substantial amount of infrastructure and its constituent parts (e.g. Kubernetes resources and their
configuration) that forms part of The Telescope. This configuration is orthogonal to the functionality of the
software components that are deployed, but changes to them can result in faults in deployment and operation of 
the system.

Testing at the appropriate level will ensure faster feedback of changes, reducing frustration for everyone and
ultimately improve the quality of the system. **Troubleshooting faults in a distributed system caused by
a typo in configuration is no fun!**

To support different levels of testing, various different jobs are executed as part of the SKAMPI build pipeline and
some `testware <https://en.wikipedia.org/wiki/Testware>`_ has been developed to aid in testing.


Pipeline Stages for Testing
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The stages of the pipeline related to testing are outlined below:

+-------------------+------------------------------------------------------------------------------------------------------------------+
|       Stage       |                                                   Description                                                    |
+===================+==================================================================================================================+
| Static_analysis   | Tests aspects of charts that do not require their deployment, e.g. linting                                       |
+-------------------+------------------------------------------------------------------------------------------------------------------+
| Unit_test [unit]_ | Tests here might deploy them to an                                                                               |
|                   | `ephemeral test environment <https://pipelinedriven.org/article/ephemeral-environment-why-what-how-and-where>`_. |
+-------------------+------------------------------------------------------------------------------------------------------------------+
| Test              | Tests to be executed in-cluster alongside the fully deployed SKAMPI prototype.                                   |
+-------------------+------------------------------------------------------------------------------------------------------------------+

**SKAMPI Gitlab CI Pipeline** (as of January 2020):

.. image:: _static/img/ci_pipeline.png 
    :alt: SKAMPI Gitlab CI pipeline

Python testware
^^^^^^^^^^^^^^^
Some components have been developed to assist in testing the Helm charts using Python. They are intended to be 
used with `pytest <http://pytest.org/>`_ as a test runner and there are currently three jobs in the pipeline that 
are configured to executed them, filtered based on `pytest markers <https://docs.pytest.org/en/latest/example/markers.html>`_: 

Pipeline jobs
"""""""""""""
- *helm-template-pytest* runs as part of the *Static_analysis* stage in the pipeline executes Python tests marked 
  with ``no_deploy``.

- *chart-pytest* runs as part of the *Unit_test* stage and will execute tests marked with the ``chart_deploy`` 
  marker [unit]_.

- *chart-pytest-quarantine* also runs during the *Unit_test* stage and executes tests marked with ``quarantine`` 
  but do not fail the build if they do.

Pytest configuration
""""""""""""""""""""
As per convention, Pytest is will collect all tests placed in the ``/tests/`` directory. The following markers are
currently defined (see */pytest.ini* for more details):

``no_deploy``
    Indicates tests that will not require any resources to be deployed into a cluster. Generally, tests that
    parse and transform the source chart templates.

``chart_deploy``
    Indicates tests that requires resources to be deployed into cluster such as the Helm chart under test and
    any other collaborating testware.

``quarantine``
    Indicates tests that should be executed but not necessarily break the build. Should be used sparingly. 

The following custom command-line flags can be passed to Pytest:

``--test-namespace <namespace>``
    Specify the namespace to use in the test session. Defaults to ``ci``.

``--use-tiller-plugin``
    Indicates that all commands to Helm should be prefixed with ``helm tiller run --``. Required when using the 
    `helm-tiller plugin <https://github.com/rimusz/helm-tiller>`_.

Test lifecycle
""""""""""""""
The lifecycle (setup, execute, teardown) of tests are managed by pytest fixtures, defined in `/tests/conftest.py`.
The ``infratest_context`` fixture in particular will determine if tests that involve deployments are included in the
pytest run, i.e. the ``chart_deploy`` marker is included. It will then:

1. invoke **kubectl** to create a namespace for the test resources(pods, services, etc.) to be deployed into 
2. ensure this namespace is deleted after the test run

**Note**: the default namespace is ``ci``, but can be overriden by specifying the custom pytest option,
``--test-namespace``. When running inside the pipeline, this flag is set to ``ci-$CI_JOB_ID`` so each job will use
its own namespace and resources, ensuring test isolation.


Test support
""""""""""""

A collection of useful components and functions to assist in testing can be found in the ``tests.testsupport`` module
(*/tests/testsupport/*):

``testsupport.util``
    Functions that may be useful in testing such as `wait_until` which allows polling, retries and timeouts.

``testsupport.helm.HelmChart``
    Represents a Helm chart that is the collection of YAML template files and *not necessarily a set of deployed 
    Kubernetes resources*. Primarily used to assist in testing the policies in YAML specifications, i.e. ``no_deploy`` 
    tests.

``testsupport.helm.ChartDeployment``
    Represents a deployed Helm chart and offers access to its resources in-cluster their metadata (by querying the
    Kubernetes API server).

``testsupport.helm.HelmTestAdaptor``
    A rudimentary adaptor class to manage the interaction with the Helm CLI.

``testsupport.extras.EchoServer``
    Represents a pod that can be deployed alongside the chart under test, containing a basic Python HTTP server that
    can receive commands. Currently it only supports echoing any HTTP POST sent to the `/echo` path. A handle to this
    is provided by the `print_to_stdout` method.

Charts are deployed via Helm and the `HelmTestAdaptor`. It's available as a Pytest fixture or you can import it from
the ``tests.testsupport.helm`` module.

The ``ChartDeployment`` class is an abstraction to represent a deployed chart and offers access to its resources
in-cluster (by querying the Kubernetes API) and metadata (such as ``release_name``).

In fact, **instantiating a ChartDeployment in code will deploy the specified chart**. A useful pattern is to create
Pytest fixture that represents the chart to be deployed and yields a ``ChartDeployment`` object. It can also call
``.delete()`` to ensure the chart is deleted and Pytest fixture scope can be used to limit a chart's lifespan. For an
example of this see the ``tango_base_release`` fixture in */tests/tango_base_chart_test.py*.

The diagram below illustrates the relationship between the Python classes in test code, CLI tools and the cluster.

.. image:: _static/img/infra_testware.png 
    :alt: Testware architecture and conceptual view

Running locally
"""""""""""""""
Requirements:

- A Kubernetes cluster (minikube).
- **kubectl** authorized to create namespaces and deploy resources to the cluster.
- **helm v2.16.1** 
- `helm-tiller plugin <https://github.com/rimusz/helm-tiller>`_ (optional).
- **Python 3.7+**

1. Install Python dependencies: ``pip install -r test-requirements.txt``
2. Execute only the ``no_deploy`` tests: ``pytest -m "no_deploy and not quarantine"``
3. Execute only the ``chart_deploy`` tests: ``pytest -m "chart_deploy and not quarantine"``
4. Execute the quarantined tests: ``pytest -m quarantine``

You should use the ``--use-tiller-plugin`` flag if you're using the **helm-tiller** plugin instead of an in-cluster
tiller. See following `article <https://rimusz.net/tillerless-helm>`_ for details. This is recommended until we
completely migrate to Helm 3 and remove Helm 2 in our codebase.

PyCharm integration
"""""""""""""""""""
PyCharm as an IDE can be used to run and debug the tests, just be sure to edit the Run/Debug configuration so that it
has the appropriate "Additional Arguments" and "Working Directory" (SKAMPI root directory and not */tests*).

.. image:: _static/img/pycharm_pytest_config_1.png 
    :alt: PyCharm config for running chart_deploy tests

.. image:: _static/img/pycharm_pytest_config_2.png 
    :alt: PyCharm config for running specific chart_deploy test


Third-party libraries
"""""""""""""""""""""
The following third-party libraries are included in the `test-requirements.txt` and used by the tests and various
supporting testware components:

- `python kubernetes client <https://github.com/kubernetes-client/python>`_ is the official kubernetes API client for
  Python. It's provided as a pytest fixture, ``k8s_api`` and also used by ``ChartDeployment`` to obtain a list of deployed
  pods(see get_pods method).

- `testinfra <https://testinfra.readthedocs.io/en/latest/index.html>`_ is a library that allows connecting to pods
  and asserting on the state of various things inside them such as open ports, directory structure, user accounts, etc.

- `elasticsearch-py <https://elasticsearch-py.readthedocs.io/en/master>`_ is the official, low-level Python client for 
  ElasticSearch.

- `requests <http://python-requests.org/>`_ is the popular HTTP client library.


.. [unit] A unit in this context is a Helm chart that can be deployed and tested.