
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
VM that has limited resources. You might want to increase this to at
least 3 GB. For Docker this can be found in the settings, for Minikube
you need to specify it on the command line:

    $ minikube --mem 4096 ...

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

    $ minikube service --url sdp-prototype-etcd-nodeport -n integration
    http://192.168.39.45:32234
    $ export SDP_CONFIG_HOST=192.168.39.45
    $ export SDP_CONFIG_PORT=32234

This will allow you to connect with the `sdpcfg` utility:

    $ pip install -U ska-sdp-config
    $ sdpcfg ls -R /
    Keys with / prefix:

Which correctly shows that the configuration is currently empty.

### Start a test dask workflow
Assuming the configuration is prepared as explained in the previous section, we can now add a processing block to the configuration:

    $ sdpcfg process realtime:testdask:0.0.1
    OK, pb_id = realtime-20190807-0000

### Use it to add a deployment

We can instead create a test deployment, by changing "`sdpcfg process realtime:testdask:0.0.1`" to `sdpcfg process realtime:testdeploy:0.0.7`.

    $ sdpcfg ls values -R /
    Keys with / prefix:
    /pb/realtime-20190807-0000 = {
      "parameters": {},
      "pb_id": "realtime-20190807-0000",
      "sbi_id": null,
      "scan_parameters": {},
      "workflow": {
        "id": "testdeploy",
        "type": "realtime",
        "version": "0.0.7"
      }
    }
    /pb/realtime-20190807-0000/owner = {
      "command": [
        "dummy_workflow.py"
      ],
      "hostname": "sdp-prototype-workflow-testdeploy-[...]",
      "pid": 6
    }

Notice that the workflow was claimed immediately by one of the containers. 

The special property of the deployment test workflow is that it will
create deployments automatically depending on workflow parameters. It
even watches the processing block parameters and will add deployments
while it is running. Let's try this out:

    $ sdpcfg edit /pb/realtime-[...]

At this point an editor should open with the processing block
information formatted as YAML. Change the "`parameters: {}`" line to
read as follows:

    parameters:
      mysql:
        type: helm
        args:
          chart: stable/mysql

This will cause the workflow to deploy a new mysql instance, as we can
easily check:

    $ sdpcfg ls values -R /deploy
    Keys with /deploy prefix:
    /deploy/realtime-20190807-0000-mysql = {
      "args": {
        "chart": "stable/mysql"
      },
      "deploy_id": "realtime-20190807-0000-mysql",
      "type": "helm"
    }

This causes Helm to get called, so you should be able to check:

    $ helm list
    NAME                        	REVISION	UPDATED                 	STATUS  	CHART              	APP VERSION	NAMESPACE
    etcd                        	1       	Wed Aug  7 12:35:47 2019	DEPLOYED	etcd-operator-0.8.4	0.9.3      	default  
    realtime-20190807-0000-mysql	1       	Wed Aug  7 13:45:33 2019	DEPLOYED	mysql-1.3.0        	5.7.14     	sdp-helm 
    sdp-prototype               	1       	Wed Aug  7 13:38:42 2019	DEPLOYED	sdp-prototype-0.2.0	1.0        	default

Note the deployment associated with the processing block. Note that it
was deployed into the name space `sdp-helm`, so to view the created pod we
have to ask as follows:

    $ kubectl get pod -n sdp-helm
    NAME                                           READY   STATUS    RESTARTS   AGE
    realtime-20190807-0000-mysql-89f658f78-mfstr   1/1     Running   0          6m20s

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

