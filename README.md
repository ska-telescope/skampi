[![Documentation Status](https://readthedocs.org/projects/ska-telescope-skampi/badge/?version=latest)](https://developer.skatelescope.org/projects/skampi/en/latest/?badge=latest)


SKA Integration on Kubernetes
===========================

The following are a set of instructions of running the SKA application on Kubernetes, and has been tested on minikube v1.12.3 with k8s v1.19.3 on Ubuntu 18.04.

Minikube
========

Using [Minikube](https://kubernetes.io/docs/getting-started-guides/minikube/) enables us to create a single node stand alone Kubernetes cluster for testing purposes.  If you already have a cluster at your disposal, then you can skip forward to 'Helm'.

The generic Minikube installation instructions are available at https://kubernetes.io/docs/tasks/tools/install-minikube/. We recommend that you use the deployment of Minikube that will support the standard features required for the SKA available at https://gitlab.com/ska-telescope/sdi/deploy-minikube 


Once completed, minikube will also update your kubectl settings to include the context `current-context: minikube` in `~/.kube/config`.  Test that connectivity works with something like:
```
$ kubectl get pods -n kube-system
NAME                               READY   STATUS    RESTARTS   AGE
coredns-86c58d9df4-5ztg8           1/1     Running   0          3m24s
...
```
Helm
----

The Helm Chart based install of the SKA TANGO-controls docker images relies on [Helm](https://docs.helm.sh/using_helm/#installing-helm) (surprise!).  If your system does not have a running version of Helm the easiest way to install one is using the install script:
```
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
```

Cleaning Up
-----------

Note on cleaning up:
```
minikube stop # stop minikube - this can be restarted with minikube start
minikube delete # destroy minikube - totally gone!
rm -rf ~/.kube # local minikube configuration cache
# remove all other minikube related installation files
sudo rm -rf /var/lib/kubeadm.yaml /data/minikube /var/lib/minikube /var/lib/kubelet /etc/kubernetes
```

SKA Umbrella charts for MVP Mid and MVP Low
===========================================

This charts folder is based on https://gitlab.com/ska-telescope/ska-umbrellas, 
by creating two set of working charts named skalow and skamid, and shifting all of the dependent charts into `charts/skampi/charts` as sub-charts - https://helm.sh/docs/chart_template_guide/subcharts_and_globals/.

The skalow umbrella chart includes (for SKA-Low) the following sub-charts:


* tango-base, 
* archiver,
* webjive, 
* mccs-low.

The skamid umbrella chart  (for SKA-Mid) contains the following sub-charts:

* etcd-operator,
* tango-base,
* cbf-proto,
* csp-proto,
* sdp-prototype,
* tmc-proto,
* oet,
* archiver,
* skuid,
* dsh-lmc-prototype,
* webjive.


All the above sub-charts have been uploaded into the helm chart repository available on nexus.

Note that values for sub-charts are namespaced in the `values.yaml`, 
and that you can use that configuration to override the values for its sub-charts. In particular shared charts, should be disabled according to the example below:

```
...
global:
  sub-system:
    tango-base:
      enabled: false
    archiver:
      enabled: false
    webjive:
      enabled: false
...
```
For more information relating to the inheritance pattern of Helm Charts see https://helm.sh/docs/chart_template_guide/subcharts_and_globals

Makefile
--------


To launch the SKA-Mid suite in the integration namespace use:
```
$ make install KUBE_NAMESPACE=integration DEPLOYMENT_CONFIGURATION=skamid
```

To clean up that Helm Chart release:
```
$make uninstall KUBE_NAMESPACE=integration DEPLOYMENT_CONFIGURATION=skamid
```
For SKA-Low use the same commands but with DEPLOYMENT_CONFIGURATION=skalow

This will give extensive output describing what has been deployed in the test namespace:

```
kubectl describe namespace integration || kubectl create namespace integration
Name:         integration
Labels:       <none>
Annotations:  <none>
Status:       Active

No resource quota.

No resource limits.
configmap/tango-config-script-integration-tmc-webui-test created
persistentvolume/rsyslog-integration-tmc-webui-test created
persistentvolumeclaim/rsyslog-integration-tmc-webui-test created
persistentvolume/tangodb-integration-tmc-webui-test created
persistentvolumeclaim/tangodb-integration-tmc-webui-test created
service/databaseds-integration-tmc-webui-test created
statefulset.apps/databaseds-integration-tmc-webui-test created
service/rsyslog-integration-tmc-webui-test created
statefulset.apps/rsyslog-integration-tmc-webui-test created
service/tangodb-integration-tmc-webui-test created
statefulset.apps/tangodb-integration-tmc-webui-test created
service/webjive-integration-tmc-webui-test created
ingress.extensions/webjive-integration-tmc-webui-test created
statefulset.apps/webjive-integration-tmc-webui-test created
pod/tangotest-integration-tmc-webui-test created
pod/tmcprototype-integration-tmc-webui-test created
```
Please wait patiently - it will take time for the Container images to download, and for the database to initialise.  After some time, you can check what is running with:
```
watch kubectl get all,pv,pvc,ingress -n integration
```

Which will give output like:
```
Every 2.0s: kubectl get all,pv,pvc -n integration           osboxes: Fri Mar 29 09:25:05 2019

NAME                                          READY   STATUS             RESTARTS   AGE
pod/databaseds-integration-tmc-webui-test-0   1/1     Running            3          117s
pod/rsyslog-integration-tmc-webui-test-0      1/1     Running            0          117s
pod/tangodb-integration-tmc-webui-test-0      1/1     Running            0          117s
pod/tangotest-integration-tmc-webui-test      1/1     Running            2          117s
pod/tmcprototype-integration-tmc-webui-test   4/5     CrashLoopBackOff   2          117s
pod/webjive-integration-tmc-webui-test-0      4/4     Running            0          117s

NAME                                            TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)           AGE
service/databaseds-integration-tmc-webui-test   ClusterIP   None           <none>        10000/TCP         117s
service/rsyslog-integration-tmc-webui-test      ClusterIP   None           <none>        514/TCP,514/UDP   117s
service/tangodb-integration-tmc-webui-test      ClusterIP   None           <none>        3306/TCP          117s
service/webjive-integration-tmc-webui-test      NodePort    10.100.50.64   <none>        8081:31171/TCP    117s

NAME                                                     READY   AGE
statefulset.apps/databaseds-integration-tmc-webui-test   1/1     117s
statefulset.apps/rsyslog-integration-tmc-webui-test      1/1     117s
statefulset.apps/tangodb-integration-tmc-webui-test      1/1     117s
statefulset.apps/webjive-integration-tmc-webui-test      1/1     117s

NAME                                                  CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                                            STORAGECLASS   REASON   AGE
persistentvolume/rsyslog-integration-tmc-webui-test   10Gi       RWO            Retain           Bound    integration/rsyslog-integration-tmc-webui-test   standard                117s
persistentvolume/tangodb-integration-tmc-webui-test   1Gi        RWO            Retain           Bound    integration/tangodb-integration-tmc-webui-test   standard                117s

NAME                                                       STATUS   VOLUME                               CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/rsyslog-integration-tmc-webui-test   Bound    rsyslog-integration-tmc-webui-test   10Gi       RWO            standard       117s
persistentvolumeclaim/tangodb-integration-tmc-webui-test   Bound    tangodb-integration-tmc-webui-test   1Gi        RWO            standard       117s

NAME                                                    HOSTS             ADDRESS         PORTS   AGE
ingress.extensions/webjive-integration-tmc-webui-test   integration.ska   193.204.1.157   80      117s
```

To clean up the Helm Chart release:
```
$make delete_all KUBE_NAMESPACE=integration
```


Access Pipeline Namespaces   
--------------------------

You can access the namespaces that are created in the pipeline to investigate any problems and test things using the namespace in the Engage Cluster.

### How to Access the Namespace

You'll see a `curl` output in the pipeline output towards the end:

```
Example:

You can get the kubeconfig file from the url: 
"https://nexus.engageska-portugal.pt/repository/k8s-ci-creds/k8s-ci-ci-test-svc-skampi-st-559-publish-credentials-12e1c424-ci-test-skampi-st-559-publish-credentials-12e1c424-low-conf" 
with the following command into your current directory in a file called KUBECONFIG:
	curl https://nexus.engageska-portugal.pt/repository/k8s-ci-creds/k8s-ci-ci-test-svc-skampi-st-559-publish-credentials-12e1c424-ci-test-skampi-st-559-publish-credentials-12e1c424-low-conf --output KUBECONFIG
```

This kubeconfig file is auto-generated to easily access the namespace created for the pipeline.

### How it works

This is enabled with adding `create_k8s_creds_after_script` to the `after_script` in the `test low` and `test mid` pipeline jobs. You can also include this script in other jobs as well. Note that `SERVICE_ACCOUNT` and `KUBE_NAMESPACE` variables must be set with an `environment` defined.

### Assumptions/Additional Notes

- `SERVICE_ACCOUNT` and `KUBE_NAMESPACE` variables must be set.
- `CI_PROJECT_NAME` and `CI_COMMIT_BRANCH` variables must be accessible. Note: These are already available in gitlab pipelines.
- The namespaces are deleted after 24 hours they are created
- The namespaces are deleted if there is recent commit on the branch (The previous namespaces for the same branch/MR are deleted) so that there is only one namespace which is pointing to the recent commit in the branch
- Kubernetes namespaces **must** start with `ci-test-<project_name>-<branch_name>-*` since same namespaces for the previous commits are deleted! Note: It doesn't check whether your namespace name is following the above naming!
- The URL to access the kubeconfig is only valid for 24 hours
- The script uses `jq` to parse json from kubernetes so you may include `create_k8s_creds_dependencies` in the `before_script` part. (See `test low/mid on demand` job definitions for a full example)

SKA Archiver
===========================================

Note: The archiver is available to deploy as per the architecture proposed at the start of PI #9. However, it has additional resource requirements which currently is a constraint. To save the resources, archiver deployment is disabled in SKAMPI till the new deployment architecture is implemented.

## Deployment

The Archiver deployment is kept independent of MVP. This enables the archiver lifecycle operations independent of MVP lifecycle. To deploy the archiver use command:

```
make deploy-archiver ARCHIVER_NAMESPACE=<archiver_namespace> DBNAME=<archiver_database_name>
```

To delete the deployment, use command:

```
make delete-archiver ARCHIVER_NAMESPACE=<archiver_namespace> DBNAME=<archiver_database_name>
```

## Configuration

The archiver can be configured to archive the required attributes. These attributes are required to be saved in the file `configuation_file.json` located in the `resources/archiver` directory. To configure the archiver, use command:

```
make configure-archiver
```

## Testing

Archiver test cases are developed and they are executed as part of the SKMAPI pipeline. Currently, the test cases are skipped as archiver deployment is disabled.
