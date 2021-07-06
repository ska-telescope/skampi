.. _p3_cluster:

Deploying SKAMPI on P3
**********************

The SDP Performance Prototype Platform (:math:`\rm{P}^3` or P3), also known as Alaska (à la SKA),
is a development cluster hosted by the University of Cambridge Research Computing Services.

P3 Kubernetes cluster
=====================

A Kubernetes cluster has been set up on P3 to support testing SKAMPI.
The cluster is called ``ska-integration`` and it has been configured with two bare-metal nodes.

To follow these instructions, you need to be logged in to the P3 OpenHPC cluster login node.
(See instructions on the `P3 Confluence page <https://confluence.skatelescope.org/display/SE/P3+How+To>`_.)

Connecting to the Kubernetes cluster
====================================

To connect to the Kubernetes cluster, you need to obtain the Kubernetes configuration file from OpenStack.

If you are doing this for the first time, download the OpenStack configuration script
from the web interface. It can be downloaded using the user menu in the upper right corner:
click on `'OpenStack RC File'` and it should download a file called ``p3-openrc.sh``.
Copy the file from your local machine to the OpenHPC login node. ``TODO: does it have to go to the login node or to the p3 machine?``
The next steps are all to be run on P3.

Run the configuration script:

.. code-block::

    source p3-openrc.sh

which will ask you to enter your OpenStack password. In addition, you need to set up a Python virtual environment
to install the OpenStack CLI:

.. code-block::

    python3 -m venv openstack
    source openstack/bin/activate
    pip install -U pip setuptools wheel
    pip install python-openstackclient python-magnumclient

Now you can use the OpenStack CLI to show information about the cluster:

.. code-block::

    openstack coe cluster show ska-integration

To get the cluster configuration file, run:

.. code-block::

    openstack coe cluster config ska-integration

This will create a file called `config`, and will tell you how to set the `KUBECONFIG`
environment variable to use it, e.g.:

.. code-block::

    export KUBECONFIG=/alaska/<username>/config

Note, if you use Helm with the cluster, it will complain that the configuration file is group- and world-readable.
You can fix that by making the file private:

.. code-block::

    chmod go-rwx config

Once you have the configuration file you shouldn't need to download it again, unless the cluster is reconfigured.

Installing SKAMPI
=================

First, clone the SKAMPI git repository and enter its directory:

.. code-block::

    git clone https://gitlab.com/ska-telescope/skampi.git
    cd skampi

Edit the values in ``pipeline.yaml`` to disable anything that needs persistent storage:

.. code-block::

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
This is because otherwise you are implying that persistent volume claims are going to get satisfied,
which is not the case on the P3 cluster.

Next, you need to set the environment variables to configure the deployment.
In particular you need to choose the namespaces to be used for the control system (`KUBE_NAMESPACE`)
and SDP dynamic deployments (`KUBE_NAMESPACE_SDP`). You should choose them so your deployment
won't collide with someone else's, e.g.:

.. code-block::

    export KUBE_NAMESPACE=skampi-<myname>
    export KUBE_NAMESPACE_SDP=skampi-<myname>-sdp
    export VALUES=pipeline.yaml

Then install SKAMPI (this ``make`` command will also create the namespaces if they don't already exist):

.. code-block::

    make install

Once you are done with your work, you can uninstall SKAMPI and clean up with:

.. code-block::

    make uninstall
    make delete_namespace
    make delete_sdp_namespace

Accessing a web-server running in a pod
=======================================

Forwarding the Kubernetes cluster connection
--------------------------------------------

P3 does not have a browser installed, hence you need to forward ports to your local machine,
in order to access web servers, which run in pods of the P3 Kubernetes cluster.

Once you deployed SKAMPI on P3, make note of the Kubernetes cluster's IP address and port number listed
in the KUBECONFIG file:

.. code-block::

    cat $KUBECONFIG

They will be listed under ``clusters → -cluster → server``.

On your local machine, add the following to the connection details to the P3 cluster within your
``ssh config`` file (normally located at ``$HOME/.ssh/config``):

.. code-block::

    LocalForward 6443 10.60.253.53:6443

Replace ports and IP address with the one you find in the KUBECONFIG file. For example,
this is what your ssh config may look like after adding the above line:

.. code-block::

    Host p3-gateway
        Hostname alaska-gate.vss.cloud.cam.ac.uk
        User <gateway-username>
        IdentityFile <path-to-private-ssh-key-file>
        AddKeysToAgent yes
        ForwardX11 yes
        ForwardX11Trusted yes

    Host p3-openhpc
        Hostname 10.60.253.102
        User <p3-username>
        ProxyJump p3-gateway
        LocalForward 6443 10.60.253.53:6443

SSH into the P3 machine as you would normally do, or, if you don't have an ssh config,
use the following command to connect to P3 (supply correct remote host name and user,
as well as IP and port):

.. code-block::

    ssh -L 6443:10.60.253.53:6443 user@remote-host

In another terminal window, create a new `kubeconfig` file on your local machine,
and copy-paste the contents of ``cat $KUBECONFIG`` command, which you ran on the remote host earlier.
Update the file by replacing the IP of the cluster with ``127.0.0.1``. Export the file as:

.. code-block::

    export KUBECONFIG=<kubeconfig_file>

now you should be able to access the cluster from your local machine.
Test it by running:

.. code-block::

    kubectl get pods -n skampi-<myname>

or ``k9s -n skampi-<myname>`` or some other `kubectl` command.

Access a webserver from local browser
-------------------------------------

Make sure there is a terminal window running with direct connection to P3 (as done above).
The following steps are to be executed in a different terminal on your local machine.

Find the port on which the pod that hosts the webserver is listening:

.. code-block::

    kubectl get service -n skampi-<myname>

Locate your pod, e.g. this is an output for the SDP Operator interface:

.. code-block::

    sdp-opinterface     NodePort    10.254.212.223   <none>        8000:32403/TCP      2d17h

In this example, the pod is listening on port 8000. If there is only one port in the list, use that.

Next, forward a local port to the pod's port:

.. code-block::

    kubectl port-forward -n skampi-<myname> sdp-opinterface-0 :8000

This will start the port forwarding. It will not have a return value, so if you want to keep the
connection open, you'll have to start a new terminal window. It'll print the following:

.. code-block::

    Forwarding from 127.0.0.1:57864 -> 8000
    Forwarding from [::1]:57864 -> 8000

In this case, the port you can access the pod from is ``57864``, which is chosen by the command.
You can specify this port yourself, if you update the above command as follows:

.. code-block::

    kubectl port-forward -n skampi-<myname> sdp-opinterface-0 4661:8000

The above would make sure you can access the pod at port ``4661``.
Go to your browser and type: ``localhost:57864`` (or if you specified the port, use that one).
This will take you to the webserver running in the pod, in this example, to the SDP Operator Interface.
