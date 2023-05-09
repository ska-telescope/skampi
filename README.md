# The current state of Skampi

Skampi is currently undergoing major restructuring.  As a result, the current deployment consists of the ska-tango-base chart (containing MariaDB and the central DS) that is deployed in a single test pipeline simulating ska-mid.  The test deploys, runs tests and tears down the deployment on Kubernetes.  This can run both in cluster, and on Minikube.

For a Minikube deployment, this can be emulated with:
```
make k8s-install-chart KUBE_NAMESPACE=default; make k8s-wait KUBE_NAMESPACE=default
make k8s-test KUBE_NAMESPACE=default
make k8s-uninstall-chart KUBE_NAMESPACE=default
```

The above installation step, including the creation of the namespace where deployment should happen, can be bundled into one by using the `make install` target, and specifying the `KUBE_NAMESPACE` in your `PrivateRules.mak` file as before. Set the `VALUES` parameter in your `PrivateRules.mak` to the `values.yaml` file that enables/modifies the deployment if required (such as `pipeline.yaml`, which is the `values.yaml` file in the root of the project by default).


Also, verify your Minikube cluster beforehand as below (assuming that you have the `tests/requirements.txt` installed in a `venv` or similar):
```
make verify-minikube
```

## Taranta Enabled
If you want to deploy Taranta locally, and you want to be able to log into the web dashboards UI, you should set `TARANTA_AUTH_DASHBOARD_ENABLE=true` in your `PrivateRules.mak` file.

# Getting Started
[![Documentation Status](https://readthedocs.org/projects/ska-telescope-ska-skampi/badge/?version=latest)](https://developer.skatelescope.org/projects/ska-skampi/en/latest/?badge=latest)

## Cloning the repository
Checkout the repository and ensure that submodules (including `.make`) are cloned with:
```
$ git clone --recurse-submodules git@gitlab.com:ska-telescope/ska-skampi.git
$ cd ska-skampi
```


## Before you begin
The documentation for SKAMPI is currently being reworked. To look at the documentation that was available before this rework started, please go to [this temporary build on ReadtheDocs](https://developer.skao.int/projects/ska-skampi/en/sp-1747-docs-old/).

For information on how to use the subsystems / components that are deployed using SKAMPI, please first look at the documentation on [SKAMPI Subsystems](https://developer.skao.int/projects/ska-skampi/en/latest/subsystems.html)

If you're developing (or planning to develop or contribute to) a component or subsystem that is to be integrated in a Kubernetes cluster, read on. If you are a tester, it is also recommended that you gain at least a basic understanding of the concepts before jumping to the section on [Testing](#testing).

### SKA Tango Examples and Tango Images
If your component or product is ready for integration, skip the following sections and go to [Development](#development).

A basic understanding of the [SKA Tango Examples](https://gitlab.com/ska-telescope/ska-tango-examples/) repository is required before attempting to integrate a component on SKAMPI. Please clone the repository and base your development on the examples given there. Pay particular attention to how deployment and partial integration is demonstrated using Helm. It will be helpful to follow the SKAMPI [Documentation on Helm](https://developer.skao.int/projects/ska-skampi/en/latest/deployment/helm.html) while you are doing this. There are also links to the documentation on Container Orchestration which you should also follow.

The SKA Tango Base and Tango Util Helm charts are required by most of the deployments that are integrated in SKAMPI. It is therefore also worth your while to look at the [SKA Tango Images](https://gitlab.com/ska-telescope/ska-tango-images/) repository. The deployment workflow is very similar to SKAMPI.

### Kubernetes and Kubectl
For information on Kubernetes and Kubectl, a quick list of references is available [here](https://developer.skao.int/projects/ska-skampi/en/latest/deployment/kubernetes.html). Follow the links provided and ensure that you have Kubectl installed before moving on.

## Deployment

### Makefile Targets
Deployment of SKAMPI is supported by Make targets, exactly as is the case with [SKA Tango Examples](https://gitlab.com/ska-telescope/ska-tango-examples/).

Note that the variable `CONFIG` is required and should be set to `mid` for the MID telescope or `low` for LOW.
The best place is to use `PrivateRules.mak`, e.g.
```
$ echo CONFIG=mid >> PrivateRules.mak
```
or via environment variables
```
$ export CONFIG=mid
```
To check which targets are available and what default values are set for variables used by Make. 
```
$ make 
```

### Environment Settings
To check what some of the most commonly used variables are that your Makefile will use when you run any commands (defaults or environment specific), you can run
```
$ make vars
```
This should give you all the basic environment variables needed to run the `make` commands as they are called in CI jobs, in case you want to debug deployment issues. For more information see the section on [CI Pipeline Deployment](#ci-pipeline-deployment).

### Local Minikube / Dedicated Server Deployment
The full deployment of SKAMPI is currently very resource intensive and therefore we recommend that you rather use the [CI Pipeline Deployment](#ci-pipeline-deployment) methods provided. If you want to deploy SKAMPI locally or on a dedicated server, first install [Docker](#docker), [Minikube](#minikube) and [Helm](#helm-charts) (note that Helm is installed alongside with Kubectl when you use the [SKA Minikube Deployment](https://gitlab.com/ska-telescope/sdi/ska-cicd-deploy-minikube/) repository).


A Minikube cluster is a kubernetes cluster with only one node (your laptop is called a node), which acts as the master and worker node. The SKA Minikube repository also provides an ingress to expose your cluster's deployment to the outside world if needed, and other settings (see the documentation in the repo for more details). Once these prerequisites are installed, you can follow the guidelines on [Deployment](https://developer.skao.int/projects/ska-skampi/en/latest/deployment.html). Note that a partial deployment of SKAMPI is made possible by setting the `<subchartname>.enabled` value to `false` in the `values.yaml` file of the repository, for any component (represented by a subchart) that can be switched off to save resources. Details can be found in the Deployment guidelines.

### CI Pipeline Deployment
Installation/Deployment of SKAMPI is much simpler using the Gitlab CI Pipelines (and this is the recommended method), as everything required to set up the environment is included in the CI infrastructure. As all branches should be named after a Jira ticket, you need a Jira ticket before checking out your branch.

Start by cloning the SKAMPI repository to your local machine. If you don't use SSH (or don't know what that even means), use the following command:
```
$ git clone https://gitlab.com/ska-telescope/ska-skampi.git
$ cd ska-skampi
```

Let's say your ticket is AT-42. Check out your branch (do this from the root directory of the SKAMPI project)
```
$ git checkout -b at-42
Switched to a new branch 'at-42'
```
Now push this new branch to Gitlab:
```
$ git push --set-upstream origin at-42
Total 0 (delta 0), reused 0 (delta 0), pack-reused 0
remote:
remote: To create a merge request for at-42, visit:
remote:   https://gitlab.com/ska-telescope/ska-skampi/-/merge_requests/new?merge_request%5Bsource_branch%5D=at-42
remote:
To gitlab.com:ska-telescope/ska-skampi.git
 * [new branch]        at-42 -> at-42
 ```

Follow the [Documentation](https://developer.skao.int/projects/ska-skampi/en/latest/deployment/multitenancy.html#deploying-in-a-namespace-linked-to-a-development-branch) for deploying in a namespace, and then downloading and using the KUBECONFIG file. This file is your key to accessing the namespace in the cluster where your branch has just been deployed.

### VSCode Kubernetes
There are multiple ways to access your cluster. With the Kubernetes plugin installed in VSCode, you can set your VSCode to access the namespaced deployment. Follow the above-mentioned documentation and set your cluster to the KUBECONFIG file provided.

### Minikube
For a local installation of a Minikube cluster, we recommend you use the SKA Minikube Deployment repository - see link below.

#### Docker

For installing Minikube, you first need to install Docker - follow [these instructions](https://docs.docker.com/get-docker/).

#### Minikube setup
To set up your Minikube cluster for local SKAMPI deployment, follow the instructions provided in the [SKA Minikube Deployment](https://gitlab.com/ska-telescope/sdi/ska-cicd-deploy-minikube/) repository. For first-time setup, do the following:
```
$ git clone git@gitlab.com:ska-telescope/sdi/ska-cicd-deploy-minikube.git
$ cd ska-cicd-deploy-minikube
$ make all
$ eval $(minikube docker-env)
```

*Please note that the command `eval $(minikube docker-env)` will point your local docker client at the docker-in-docker for minikube. Use this only for building the docker image and another shell for other work.*

Once your minikube cluster is running, you can deploy SKAMPI using the `make` commands (see below). First check that your Minikube is running:
```
$ minikube status
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
```
Now install SKAMPI. Take note: all default values of variables will be used if none are set. Read more about this under [Modifying deployment configuration](#modifying-deployment-configuration).
```
$ cd .. # this is to go back to the root of the SKAMPI repo after the above commands
$ make install-or-upgrade
$ make wait
$ make skampi-links
```
Once `make wait` finishes, you can run `make skampi-links` and follow the URL given to check if you can access the deployed software.

### Helm Charts
Installation of Helm should be done as part of familiarising with SKA Tango Examples. This will also help you getting familiar with what a Helm Chart is.

Helm Charts are basically a templating solution that enables a large project such as the SKA to configure a set of standard kubernetes resources using configuration parameters. A Chart is essentially a folder with a general structure, which can be packaged in a .tar.gz file and published to a Helm Repository, or used locally for deployment.

For an understanding of how Helm Charts are used in the SKAMPI project, please go to the section on [Templating the Application](https://developer.skao.int/en/latest/tools/containers/orchestration-guidelines.html#templating-the-application) under the [Container Orchestration Guidelines](https://developer.skao.int/en/latest/tools/containers/orchestration-guidelines.html) of the [Developer Portal](https://developer.skao.int/en/latest/).

## Deploy and use the signal display via Skampi

### Deploy via skampi

Access skampi pipelines via the following link https://gitlab.com/ska-telescope/ska-skampi/-/pipelines

Click Run pipeline, default is to run against master

From pipeline stages, run the mid_deploy_on_demand job

When this completes, in the log a new link to the skampi landing page should be generated (see below example)

https://k8s.stfc.skao.int/ci-ska-skampi-master-mid/start/

### Use the signal display via skampi

Run the jupyter notebooks via the following link:
https://k8s.stfc.skao.int/binderhub/v2/gl/ska-telescope%2Fska-jupyter-scripting/HEAD

Modify prelim_aa05.ipynb at stage 1.3 Define deployment to be tested

set_cluster(namespace="staging") should be updated to include the namespace in use (see example below)

set_cluster(namespace="ci-ska-skampi-master")

When this block is run, a link to the dashboard will be generated (example below)

Link to dashboard: https://k8s.stfc.skao.int//ci-ska-skampi-master-mid/qa/display/

Run each stage of the notebook blocks in order and the qa display dashboard will be updated with data.

## Development
The following sections are aimed at developers who want to integrate their products/components, or who want to add integration or system-level tests to the repository.

### Setting up your development environment
Development environments are not being dictated at the SKA. However, the development environment can be provisioned for VSCode developers by using a combination of the `.devcontainer` and the `.vscode` settings (launch configurations and environment setup).

Developers should take care not to confuse localised development environments with the environments provided by the standard deployment and testing container images used in CI Pipelines, as these represent supported dependencies in as many as possible maintained by the System Team.

To run from the `.devcontainer` provided, copy the `/resources/vscode/devcontainer` folder to `<skampi-root>/.devcontainer`, and `/resources/vscode/vscode` to `<skampi-root>/.vscode`. This can also be done by using 

``` make dev-vscode```

If not running in a Dev Container, do:
- Copy the `settings` object from `.devcontainer.json` to `.vscode/settings.json`;
- Look at what is installed in the Dockerfile under the `.devcontainer/` directory and install these packages;
- Install one by one the VSCode plugins listed under `"extensions"` in `.devcontainer/devcontainer.json`;
- Run the commands in the `.devcontainer/devcontainer.json` file's `"postCreateCommand":` object (such as setting up the `poetry` virtualenvironment in your project - this is used in the linter setup);

### Required dependencies
On Ubuntu 22.04, the following dependencies are required:

- `pkg-config`
- `poetry`

### Adding a new product/component
This is an example of how the deployment would look, if a new application ("Application three"), were to be added to the minimal deployment described in the section on [Modifying deployment configuration](#modifying-deployment-configuration):
```{mermaid}
flowchart TB
    subgraph "Namespace integration-mid"
      subgraph "SKAMPI Landing Page"
        d1[chart ska-landingpage] --> d2(container ska-landingpage)
      end
      subgraph SKA Mid Chart
        subgraph "Tango Util Library Chart"
          a1[chart ska-tango-util]--> |uses| a2(container ska-tango-util)
        end
        subgraph "SKA Tango Base application"
          b1[chart ska-tango-base]-->b2(container databaseds)
          b1--> |uses| a2
        end
        subgraph "Application three"
          c1[chart c1]-->c2(container c2)
          c1--> |uses| a2
        end
      end
    end

```

Using the example repositories and SKAMPI as a guide should prove useful. More information to follow here.
..todo

### Modifying deployment configuration
To override local environment variables used by the Makefile, you can either export them (they will only persist for the current shell session), or create a file in the root of the project called PrivateRules.mak.

:warning: In this section, the assumption is made that you have deployed Minikube as described above, and are deploying for local development and testing purposes.

#### Local overrides for Make and Helm variables
Test the effect of changes to the environment / `Make` variables by following these steps:

1. First check the current value (according to `Make`), of the `MARK` variable (the variables listed below, and their defaults, may change over time):
    ```
    $ make vars
    SKA_K8S_TOOLS_DEPLOY_IMAGE=

    KUBE_NAMESPACE=integration

    ...snip...

    MARK=
    ```

    In the above example, `MARK` is empty. If this is your first time using the repo, that's to be expected.

2. Now set it for the current shell and check the value of `MARK` again:
    ```
    $ export MARK=ping
    $ make vars | grep MARK
    MARK=ping
    ```
3. Next, reset the `MARK` variable, create a `PrivateRules.mak` file and set the value for `MARK`:
    ```
    $ export MARK=
    $ make vars | grep MARK
    MARK=
    $ echo MARK=ping >> PrivateRules.mak
    $ make vars | grep MARK
    MARK=ping
    ```
#### Set the host to point to your local machine
If you deployed Minikube as per the above, your HAProxy frontend will expose your Nginx to your browser at the IP address given in the output near the end of the `make all` or `make minikube` command:
```
...snip...
# Now setup the Proxy to the NGINX Ingress and APIServer, and any NodePort services
# need to know the device and IP as this must go in the proxy config
Installing HAProxy frontend to make Minikube externally addressable
MINIKUBE_IP: 192.168.64.12
Adding proxy for NodePort 80
Adding proxy for NodePort 443
```
The `MINIKUBE_IP` variable should be given to your Makefile. Copy that IP address and set the value of the `INGRESS_HOST` in `PrivateRules.mak` to this variable. For instance, if the IP address was output as `192.168.64.12` (above example), you can do this:
```
$ echo INGRESS_HOST=192.168.64.12 >> PrivateRules.mak
```
This will help reaching the NodePort services (see reaching the landingpage further on).

#### Control the deployment with VALUES and values.yaml
Check the rest of the PrivateRules.mak variables. Notice that there is a `VALUES` parameter, by default set to `values.yaml`:
```
$ make vars | grep VALUES
VALUES=values.yaml
```

The values.yaml file controls all the variables that are used by Helm when interpreting the templates written for each of the Charts. In other words, if you want to modify the deployment of `SKAMPI` in any way, the simplest method would be to modify the appropriate variables in your own `yaml` file, and tell `Make` about this file. As a convenience, there is already a `yaml` file specified in `.gitignore`, so that you won't unnecessarily commit your local file.

**NOTE** the following assumes that `CONFIG=mid` was set. Replace the `mid` with `low` if needed.

1. Set your `VALUES` to this file and populate this file with a harmless default and check that Helm doesn't complain:
    ```
    $ echo VALUES=my_local_values.yaml >> PrivateRules.mak
    $ echo am_i_awesome: true >> my_local_values.yaml
    $ make template-chart
    helm dependency update ./charts/ska-mid/; \
    helm template test \
            --set ska-tango-base.xauthority="" --set ska-oso-scripting.ingress.nginx=true --set ska-ser-skuid.ingress.nginx=true --set ska-tango-base.ingress.nginx=true --set ska-taranta.ingress.nginx=true --set global.minikube=true --set ska-sdp.helmdeploy.namespace=integration-sdp --set global.tango_host=databaseds-tango-base:1     0000 --set ska-tango-archiver.hostname= --set ska-tango-archiver.dbname=default_mvp_archiver_db  --set ska-tango-archiver.port= --set ska-tango-archiver.dbuser= --set ska-tango-archiver.dbpassword=   \
            --values my_local_values.yaml \
            ./charts/ska-mid/ --namespace integration;
    Hang tight while we grab the latest from your chart repositories...
    ...Successfully got an update from the "skao" chart repository
    ...Successfully got an update from the "skatelescope" chart repository
    Update Complete. ⎈Happy Helming!⎈
    Saving 11 charts
    Downloading ska-tango-base from repo https://artefact.skao.int/repository/helm-internal
    Downloading ska-tango-util from repo https://artefact.skao.int/repository/helm-internal
    Downloading ska-mid-cbf from repo https://artefact.skao.int/repository/helm-internal
    ... snip ...
    Deleting outdated charts

    # after a bit of waiting, suddenly lots of output appears.
    ```

    You now have a values file that overrides the local deployment without affecting the repository. If you want to create a minimal deployment, you can now switch off all the components deployed by Helm.

2. Copy all the settings below into `my_local_values.yaml`
    ```
    minikube: true

    am_i_awesome: true

    ska-tango-base:
      vnc:
        enabled: false
    ska-mid-cbf:
      enabled: false
    ska-csp-lmc-mid:
      enabled: false
    ska-sdp:
      enabled: false
    ska-tmc-mid:
      enabled: false
    ska-oso-scripting:
      enabled: false
    ska-taranta:
      enabled: false
    ska-ser-skuid:
      enabled: false
    ska-landingpage:
      enabled: false
    ska-tango-archiver:
      enabled: false
    ```
    NOTE: this can hardly be called a deployment of SKAMPI, as no component is deployed at all. This example is only intended to show how the deployment can be controlled using Helm chart values. The entire SKAMPI cannot be easily deployed on a laptop at the time of writing. Updates to requests & limits for the components of SKAMPI are needed, in order to make the deployment less bloated. Developers of components must follow the [Documentation](https://developer.skao.int/en/latest/tools/containers/orchestration-guidelines.html#resource-reservations-and-constraints) for setting resource limits & requests for their charts. Use the [Monitoring dashboards](https://developer.skao.int/en/latest/tools/monitoring-dashboards/monitoring-dashboards.html) available for properly gauging the resource usage of components.

3. In a new terminal, watch the deployment settle with `kubectl` (the below snapshot of statuses should change as the deployment settles down. Prepending `watch ` to the `kubectl` creates the watcher - exit it by hitting Ctrl+C.). Assuming you didn't modify the name of the namespace (from `integration` to something else) in `PrivateRules.mak`:
    ```
    $ watch kubectl get all -n integration
    NAME                                            READY   STATUS              RESTARTS   AGE
    pod/databaseds-tango-base-0                     0/1     ContainerCreating   0          18s
    pod/ska-tango-base-tango-rest-86646c966-5svhr   0/1     Init:0/5            0          18s
    pod/ska-tango-base-tangodb-0                    0/1     ContainerCreating   0          18s
    pod/tangotest-config-cbkxj                      0/1     Init:0/1            0          18s
    pod/tangotest-test-0                            0/1     Init:0/2            0          18s

    NAME                                 TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)           AGE
    service/databaseds-tango-base        NodePort    10.99.68.66    <none>        10000:30397/TCP   19s
    service/ska-tango-base-tango-rest    NodePort    10.106.95.48   <none>        8080:31500/TCP    19s
    service/ska-tango-base-tangodb       NodePort    10.108.17.5    <none>        3306:31278/TCP    19s
    service/tangotest-test               ClusterIP   None           <none>        <none>            19s

    NAME                                        READY   UP-TO-DATE   AVAILABLE   AGE
    deployment.apps/ska-landingpage                 0/1     1            0           19s
    deployment.apps/ska-tango-base-tango-rest   0/1     1            0           19s

    NAME                                                  DESIRED   CURRENT   READY   AGE
    replicaset.apps/ska-tango-base-tango-rest-86646c966   1         1         0       18s

    NAME                                          READY   AGE
    statefulset.apps/databaseds-tango-base        0/1     18s
    statefulset.apps/ska-tango-base-tangodb       0/1     18s
    statefulset.apps/tangotest-test               0/1     18s

    ```
    Above deployment is pretty useless and will not pass any tests, but illustrates how a small deployment can be made. You now have the ability to add components to the deployment, by modifying their `enabled` variables. Let's test that out, and just re-introduce the Landing Page:

4. Enable the Landing Page by setting `ska-landingpage.enabled` to `true` in the `my_local_values.yaml` file:
    ```
    ska-landingpage:
      enabled: true
    ```
5. Now update the deployment:
    ```
    $ make install-or-upgrade
    ```
6. You should now see the landing page being added to the cluster:
    ```
    $ kubectl get all -n integration -l app=ska-landingpage    # the -l app=ska-landingpage is to filter for anything that is labelled app=ska-landingpage
    NAME                             READY   STATUS    RESTARTS   AGE
    pod/ska-landingpage-5f95cdff-26mqc   1/1     Running   0          27m

    NAME                  TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
    service/ska-landingpage   ClusterIP   10.106.182.252   <none>        80/TCP    27m

    NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
    deployment.apps/ska-landingpage   1/1     1            1           27m

    NAME                                   DESIRED   CURRENT   READY   AGE
    replicaset.apps/ska-landingpage-5f95cdff   1         1         1       27m
    ```
7. You should now be able to get an output of the ska-landingpage by running `make skampi-links`:
    ```
    $ make skampi-links
    ############################################################################
    #            Access the Skampi landing page here:
    #            https://192.168.64.12/integration/start/
    ############################################################################
    ```
    Clicking on this link should open the landing page.

#### Verifying Chart versions deployed by Helm
The landing page holds a list of versions of the Charts that are deployed. This list is generated at deploy-time, taking into account the enabled and disabled items. This should give an indication of what should be deployed. :warning: NOTE: This is not a list of successfully deployed items, but merely a list of items that should be expected to run. Further investigation is required if subsystems are unexpectedly not functioning.

For the above deployment, when you click on `About >> Version`, you'll see only the three sub-charts that were deployed, the umbrella chart (in SKAMPI we only have Mid and Low umbrella charts), and their versions, for example:
![](_static/img/about_version.png)

This means that the Taranta link should result in a 404 error, even though it is available.
### Testing
While running SKAMPI on a local Minikube, the following steps can be carried out to see if your setup can test SKAMPI.

1. Install the Python `kubernetes` package in your virtual environment
```
python3 -m venv venv && . venv/bin/activate && pip3 install --upgrade pip
python3 -m pip install kubernetes
```
2. Run the test suite from a pod deployed in the cluster (using `MARK=ping` will limit your test to only one).
```
make k8s_test MARK=ping
```
Use the `MARK` parameter to run specific tests. All tests are marked with a `@pytest.mark.<some-test-marker>`, and by specifying the `MARK` variable by `<some-test-marker>`, you tell `pytest` to only run those tests. Note that this test will fail for the deployment described above, as there is no central node deployed.

More information should be available in the [Documentation](https://developer.skao.int/projects/ska-skampi/en/latest/testing.html).

## EDA 
The EDA solution is based on HDB++ archiver with TimescaleDB as the backend database. The HDB++ Configuration Manager configures the attributes to be archived and defines which Event Subscriber is responsible for a set of Tango attributes to be archived. For more detail information on EDA please click [here](https://ska-tango-archiver.readthedocs.io/en/latest/)

## Troubleshooting / FAQ
Finding issues with SKAMPI deployments can sometimes be difficult, and knowledge of Kubernetes and Tango are essential. Some excellent troubleshooting tips for Kubernetes can be found at https://kubernetes.io/docs/tasks/debug-application-cluster/troubleshooting.

## Getting Help
If you get stuck, the SKA Slack channels related to the technology that you are working on, are good places to go. These are a few useful channels:

### [#help-kubernetes](https://skao.slack.com/archives/C016W494EHZ)
For help with Kubernetes related issues.
### [#help-gitlab](https://skao.slack.com/archives/C016F65FBB9)
Struggling with CI or other Gitlab related things? Go here.

### [#proj-mvp](https://skao.slack.com/archives/CKBDRGCKB)
This is the channel where (in general) the current progress of the MVP is discussed, as well as integration issues on SKAMPI.

### [#team-system-support](https://skao.slack.com/archives/CEMF9HXUZ)
The System Team help out whenever there are CI related problems that seem to be out of developers' control.
