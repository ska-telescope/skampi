Using OET
===============

Rest client
-------------
For instructions on how to use the OET rest client, see documentation in [the SKA developer portal](https://developer.skatelescope.org/projects/observation-execution-tool/en/latest/rest_client.html).

The OET rest client in SKAMPI can be accessed through Jupyter or OET SSH service.

### Jupyter
Get the OET Jupyter service IP and port:
```
$ kubectl describe service jupyter-oet-release-name -n integration
```

Navigate to the IP address. In Jupyter, open an OET terminal by navigating to `New > Terminal`

### SSH
Get the OET SSH service NodePort:
```
$ kubectl describe service ssh-oet-release-name -n integration
```

SSH to OET container:
```
$ ssh tango@localhost -p NodePort
```
PW: oet

iTango
-------------
**Note:** The SKAMPI OET iTango service is disabled by default in the values.yaml

Get the OET iTango service NodePort:
```
$ kubectl describe service itango-oet-release-name -n integration
```

SSH to the iTango session:
```
$ ssh tango@localhost -p NodePort
```
PW: oet

You can also start an iTango session from within the oet-ssh container:
```
$ itango3 --profile=ska
```