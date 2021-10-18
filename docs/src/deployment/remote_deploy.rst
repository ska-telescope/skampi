.. _remote_host:

Deploying SKAMPI on a remote server
***********************************

Setting up a Kubernetes cluster
===============================

You may need to ask your server admin to set a cluster up for you and
provide you with the connection details, or follow the
|kube_cluster| to set one up yourself.

.. |kube_cluster| raw:: html

    <a href="https://kubernetes.io/docs/setup/" target="_blank">official Kubernetes guide</a>


Connecting to the Kubernetes cluster
====================================

To connect to the Kubernetes cluster, you need to have access to the Kubernetes configuration file.


If remote is OpenStack compatible
---------------------------------

If your remote server is OpenStack compatible and you have direct access
to the OpenStack webinterface, you can follow these steps to obtain the Kubernetes cluster configuration.

First, download the OpenStack configuration script
from the web interface. It can be downloaded using the user menu in the upper right corner:
click on `'OpenStack RC File'` and it should download a bash script.
Copy the file from your local machine to the remote host, and run the following commands

Run the configuration script:

.. code-block:: console

    source <openstack.sh>

In addition, you need to set up a Python virtual environment to install the OpenStack CLI:

.. code-block:: console

    python3 -m venv openstack
    source openstack/bin/activate
    pip install -U pip setuptools wheel
    pip install python-openstackclient python-magnumclient

Now you can use the OpenStack CLI to show information about the cluster:

.. code-block:: console

    openstack coe cluster show <kube-cluster-name>

``<kube-cluster-name>`` is what your Kubernetes cluster is called. To get the cluster configuration file, run:

.. code-block:: console

    openstack coe cluster config <kube-cluster-name>

This will create a file called `config`, and will tell you how to set the `KUBECONFIG`
environment variable to use it, e.g.:

.. code-block:: console

    export KUBECONFIG=<path-to-config-file>/config

Once you have the configuration file you shouldn't need to download it again, unless the cluster is reconfigured.

Installing SKAMPI
=================

First, clone the SKAMPI git repository and enter its directory:

.. code-block:: console

    git clone https://gitlab.com/ska-telescope/skampi.git
    cd skampi

Some of the SKAMPI components require persistent storage when they start. If your remote host
doesn't support such claims, edit the values in ``values.yaml`` to disable anything that needs
persistent storage:

.. code-block:: yaml

    elastic:
      enabled: false
    fluentd:
      enabled: false
    kibana:
      enabled: false
    tests:
      enabled: false
    hdbppdb:
      enabled: true
    archiver:
      enabled: false
    tangodb:
      use_pv: false
    tangotest:
      enabled: true
    webjive:
      enabled: false
    minikube: true

Note, that you need to set ``minikube: true`` even though you are not using Minikube.
This is because otherwise you are implying that persistent volume claims are going to get satisfied.
If your host can satisfy persistent storage claims, skip the above step.

Next, you need to set the environment variables to configure the deployment.
In particular you need to choose the namespaces to be used for the control system (```KUBE_NAMESPACE``)
and SDP dynamic deployments (```KUBE_NAMESPACE_SDP``). You should choose them so your deployment
won't collide with someone else's, e.g.:

.. code-block:: console

    export KUBE_NAMESPACE=skampi-<myname>
    export KUBE_NAMESPACE_SDP=skampi-<myname>-sdp

You may also specify these in a ``PrivateRules.mak`` file created at the project root by running:

.. code-block:: console

    make vars > PrivateRules.mak

The above command will add the most commonly used environment variables that appear in the Makefile.
You will need to update the relevant ones, and add more if needed. ``PrivateRules.mak``
takes precedence over exported environment variables when a ``make`` command is run, hence,
if you use this file, you don't need to export the variables. Now, deploy SKAMPI
(this ``make`` command will also create the namespaces if they don't already exist):

.. code-block:: console

    make install

Once you are done with your work, you can uninstall SKAMPI and clean up with:

.. code-block:: console

    make uninstall
    make delete-namespace
    make delete-sdp-namespace

If you want to see how ``make`` will use the variables (in other words, what commands will actually be run), append the parameter ``--dry`` for a dry-run, for example:

.. code-block:: console

    make install --dry

Accessing a web-server running in a pod
=======================================

Forwarding the Kubernetes cluster connection
--------------------------------------------

If the remote host does not have a browser installed, you will have to forward ports to your local machine,
in order to access web servers, which run in pods of the remote Kubernetes cluster.

Once you deployed SKAMPI on the remote host, make note of the Kubernetes cluster's IP address and port number listed
in the KUBECONFIG file:

.. code-block:: console

    kubectl config view -o jsonpath='{.clusters[].cluster.server}'

On your local machine, add the following to the connection details to the remote host within your
``ssh config`` file (normally located at ``$HOME/.ssh/config``):

.. code-block::

    LocalForward 6443 10.60.253.53:6443

Replace ports and IP address with the one you find in the KUBECONFIG file.

SSH into the remote machine as you would normally do, or, if you don't have an ssh config,
use the following command to connect (supply correct remote host name and user,
as well as IP and port):

.. code-block:: console

    ssh -L 6443:10.60.253.53:6443 user@remote-host

In another terminal window, create a new ``kubeconfig`` file on your local machine,
and copy-paste the contents of ``cat $KUBECONFIG`` command, which you ran on the remote host earlier.
Update the file by replacing the IP of the cluster with ``127.0.0.1``. Export the file as:

.. code-block:: console

    export KUBECONFIG=<kubeconfig_file>

now you should be able to access the cluster from your local machine.
Test it by running:

.. code-block:: console

    kubectl get pods -n skampi-<myname>

or ``k9s -n skampi-<myname>`` or some other ``kubectl`` command.

Access a webserver from local browser
-------------------------------------

Make sure there is a terminal window running with direct connection to the remote server (as done above).
The following steps are to be executed in a different terminal on your local machine.

Find the port on which the pod that hosts the webserver is listening:

.. code-block:: console

    kubectl get service -n skampi-<myname>

Locate your pod, e.g. this is an output for the SDP Operator interface:

.. code-block:: console

    sdp-opinterface     NodePort    10.254.212.223   <none>        8000:32403/TCP      2d17h

In this example, the pod is listening on port 8000. If there is only one port in the list, use that.

Next, forward a local port to the pod's port:

.. code-block:: console

    kubectl port-forward -n skampi-<myname> sdp-opinterface-0 :8000

This will start the port forwarding. It will not have a return value, so if you want to keep the
connection open, you'll have to start a new terminal window. It'll print the following:

.. code-block::

    Forwarding from 127.0.0.1:57864 -> 8000
    Forwarding from [::1]:57864 -> 8000

In this case, the port you can access the pod from is ``57864``, which is chosen by the command.
You can specify this port yourself, if you update the above command as follows:

.. code-block:: console

    kubectl port-forward -n skampi-<myname> sdp-opinterface-0 4661:8000

The above would make sure you can access the pod at port ``4661``.
Go to your browser and type: ``localhost:57864`` (or if you specified the port, use that one).
This will take you to the webserver running in the pod, in this example, to the SDP Operator Interface.
