
Helm Deployment
===============

Prerequisites
-------------

### Kubernetes

You will need Kubernetes installed. [Docker for
Desktop](https://www.docker.com/products/docker-desktop) includes a
workable one-node Kubernetes installation - just need to activate it
in the settings. Alternatively, you can install
[Minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/).

Note that on both Windows and Mac, this will run containers within a
VM that has limited resources. You should increase the memory to at
least 8 GB and the disk size to at least 32 GB. For Docker this can
be found in the settings, for Minikube you need to specify it on the
command line:

    $ minikube --memory=8192m --disk-size=32768m ...

Deploying SDP
-------------

### Deploy the prototype

```
$ make deploy_all KUBE_NAMESPACE=integration
```

Testing it out
--------------

### Connecting to configuration database

The deployment scripts should have exposed the SDP configuration
database (i.e. etcd) via a NodePort service. For Docker Desktop, this
should automatically expose the port on localhost, you just need to
find out which one:

```
$ kubectl get service -n integration
```

This will return something like:
```
NAME                               TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                             AGE
databaseds-tango-base-test         ClusterIP   None             <none>        10000/TCP                           4m
etcd-restore-operator              ClusterIP   10.109.184.11    <none>        19999/TCP                           4m3s
mongodb-webjive-test               ClusterIP   None             <none>        27017/TCP                           3m50s
oet-ssh                            NodePort    10.106.154.234   <none>        2022:31887/TCP                      4m2s
rsyslog-tmc-proto-test             ClusterIP   None             <none>        514/TCP,514/UDP                     3m57s
tangodb-tango-base-test            ClusterIP   None             <none>        3306/TCP                            4m
test-sdp-prototype-etcd-nodeport   ClusterIP   None             <none>        2379/TCP,2380/TCP                   3m50s
```

Then take the deployment name and run: 

    $ kubectl get service test-sdp-prototype-etcd-nodeport -n integration
    NAME                          TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
    sdp-prototype-etcd-nodeport   NodePort   10.97.188.221   <none>        2379:32234/TCP   3h56m

Set the environment variable `SDP_CONFIG_PORT` according to the
second part of the `PORTS(S)` column:

    $ export SDP_CONFIG_PORT=32234

For Minikube, you need to set both `SDP_CONFIG_HOST` and
`SDP_CONFIG_PORT`, but you can easily query both using
`minikube service`:

    $ minikube service --url test-sdp-prototype-etcd-nodeport -n integration
    http://192.168.39.45:32234
    $ export SDP_CONFIG_HOST=192.168.39.45
    $ export SDP_CONFIG_PORT=32234

This will allow you to connect with the `sdpcfg` utility:

    $ pip install -U ska-sdp-config
    $ sdpcfg ls -R /
    Keys with / prefix:

Which correctly shows that the configuration is currently empty.


### Start a workflow

Assuming the configuration is prepared as explained in the previous
section, we can now add a processing block to the configuration:

    $ sdpcfg process realtime:testdask:0.1.0
    OK, pb_id = realtime-20191121-0000

The processing block is created with the `/pb` prefix in the
configuration:

    $ sdpcfg ls values -R /pb
    Keys with /pb prefix:
    /pb/realtime-20191121-0000 = {
      "parameters": {},
      "pb_id": "realtime-20191121-0000",
      "sbi_id": null,
      "scan_parameters": {},
      "workflow": {
        "id": "testdask",
        "type": "realtime",
        "version": "0.1.0"
      }
    }
    /pb/realtime-20191121-0000/owner = {
      "command": [
        "testdask.py",
        "realtime-20191121-0000"
      ],
      "hostname": "realtime-20191121-0000-workflow-7bf947687f-9h9gz",
      "pid": 1
    }

The processing block is detected by the processing controller which
deploys the workflow. The workflow in turn deploys the execution engines
(in this case, Dask). The deployments are requested by creating entries
with `/deploy` prefix in the configuration, where they are detected by
the Helm deployer which actually makes the deployments:

    $ sdpcfg ls values -R /deploy
    Keys with /deploy prefix:
    /deploy/realtime-20191121-0000-dask = {
      "args": {
        "chart": "stable/dask",
        "values": {
          "jupyter.enabled": "false",
          "scheduler.serviceType": "ClusterIP",
          "worker.replicas": 2
        }
      },
      "deploy_id": "realtime-20191121-0000-dask",
      "type": "helm"
    }
    /deploy/realtime-20191121-0000-workflow = {
      "args": {
        "chart": "workflow",
        "values": {
          "env.SDP_CONFIG_HOST": "sdp-prototype-etcd-client.default.svc.cluster.local",
          "env.SDP_HELM_NAMESPACE": "sdp",
          "pb_id": "realtime-20191121-0000",
          "wf_image": "nexus.engageska-portugal.pt/sdp-prototype/workflow-testdask:0.1.0"
        }
      },
      "deploy_id": "realtime-20191121-0000-workflow",
      "type": "helm"
    }

The deployments associated with the processing block have been created
in the `integration-sdp` namespace, so to view the created pods we have
to ask as follows:

    $ kubectl get pod -n integration-sdp
    NAME                                                    READY   STATUS    RESTARTS   AGE
    realtime-20191121-0000-dask-scheduler-6c7cc64c7-jfczn   1/1     Running   0          113s
    realtime-20191121-0000-dask-worker-7cb8cdf6bd-mtc9w     1/1     Running   3          113s
    realtime-20191121-0000-dask-worker-7cb8cdf6bd-tdzkp     1/1     Running   3          113s
    realtime-20191121-0000-workflow-7bf947687f-9h9gz        1/1     Running   0          118s

### Cleaning up

Finally, let us remove the processing block from the configuration:

    $ sdpcfg delete /pb/realtime-[...]

If you re-run the commands from the last section you will notice that
this correctly causes all changes to the cluster configuration to be
undone as well.

Accessing Tango
---------------

By default the chart installs the iTango shell pod from the tango-base
chart. You can access it as follows:

    $ kubectl exec -it itango-tango-base-sdp-prototype /venv/bin/itango3

You should be able to query the SDP Tango devices:

    In [1]: lsdev
    Device                                   Alias                     Server                    Class
    ---------------------------------------- ------------------------- ------------------------- --------------------
    mid_sdp/elt/master                                                 SDPMaster/1               SDPMaster
    sys/tg_test/1                                                      TangoTest/test            TangoTest
    sys/database/2                                                     DataBaseds/2              DataBase
    sys/access_control/1                                               TangoAccessControl/1      TangoAccessControl
    mid_sdp/elt/subarray_1                                             SDPSubarray/1             SDPSubarray

This allows direction interaction with the devices, such as querying and
and changing attributes and issuing commands:

    In [2]: d = DeviceProxy('mid_sdp/elt/subarray_1')

    In [3]: d.obsState
    Out[3]: <obsState.IDLE: 0>
    
    In [4]: d.state()
    Out[4]: tango._tango.DevState.OFF
    
    In [5]: d.adminMode = 'ONLINE'
    In [6]: d.AssignResources('')
    In [7]: d.state()
    Out[7]: tango._tango.DevState.ON
    
    In [8]: d.obsState
    Out[8]: <obsState.IDLE: 0>
    
    In [9]: d.Configure('{ "configure": { "id": "xyz", "sbiId": "xyz", "workflow": { "type": "realtime", "version": "0.1.0", "id": "vis_receive" }, "parameters": {}, "scanParameters": { "1": {} } } }')
    In [10]: d.obsState
    Out[10]: <obsState.READY: 2>
    
    In [11]: d.StartScan()
    In [12]: d.obsState
    Out[12]: <obsState.SCANNING: 3>
    
    In [13]: d.EndScan()
    In [14]: d.obsState
    Out[14]: <obsState.READY: 2>

