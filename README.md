# Getting Started
[![Documentation Status](https://readthedocs.org/projects/ska-telescope-ska-skampi/badge/?version=latest)](https://developer.skatelescope.org/projects/ska-skampi/en/latest/?badge=latest)

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
Deployment of SKAMPI is supported by Make targets, exactly as is the case with [SKA Tango Examples](https://gitlab.com/ska-telescope/ska-tango-examples/). To check which targets are available and what default values are set for variables used by Make, run
```
make
```

### Environment Settings
To check what some of the most commonly used variables are that your Makefile will use when you run any commands (defaults or environment specific), you can run 
```
make vars
```
This should give you all the basic environment variables needed to run the `make` commands as they are called in CI jobs, in case you want to debug deployment issues. For more information see the section on [CI Pipeline Deployment](#ci-pipeline-deployment).

### Local Minikube / Dedicated Server Deployment
The full deployment of SKAMPI is currently very resource intensive and therefore we recommend that you rather use the [CI Pipeline Deployment](#ci-pipeline-deployment) methods provided. If you want to deploy SKAMPI locally or on a dedicated server, first install [Docker](#docker), [Minikube](#minikube) and [Helm](#helm-charts) (note that Helm is installed alongside with Kubectl when you use the [SKA Minikube Deployment](https://gitlab.com/ska-telescope/sdi/ska-cicd-deploy-minikube/) repository).


A Minikube cluster is a kubernetes cluster with only one node (your laptop is called a node), which acts as the master and worker node. The SKA Minikube repository also provides an ingress to expose your cluster's deployment to the outside world if needed, and other settings (see the documentation in the repo for more details). Once these prerequisites are installed, you can follow the guidelines on [Deployment](https://developer.skao.int/projects/ska-skampi/en/latest/deployment.html). Note that a partial deployment of SKAMPI is made possible by setting the `<subchartname>.enabled` value to `false` in the `values.yaml` file of the repository, for any component (represented by a subchart) that can be switched off to save resources. Details can be found in the Deployment guidelines.

### CI Pipeline Deployment
Installation/Deployment of SKAMPI is much simpler using the Gitlab CI Pipelines, as everything required to set up the environment is included in the CI infrastructure. As all branches should be named after a Jira ticket, you need a Jira ticket before checking out your branch. 

Let's say your ticket is AT-42. Check out your branch (do this from the root directory of the SKAMPI project)
```
➜  skampi git:(master) git checkout -b at-42
Switched to a new branch 'at-42'
```
Now push this new branch to Gitlab:
```
➜  skampi git:(at-42) git push --set-upstream origin at-42
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
git clone git@gitlab.com:ska-telescope/sdi/ska-cicd-deploy-minikube.git
cd ska-cicd-deploy-minikube
make all
eval $(minikube docker-env)
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
Now install SKAMPI (remember, all default values of variables will be used if none are set, or if no PrivateRules.mak is used for overrides):
```
$ cd .. # this is to go back to the root of the SKAMPI repo after the above commands
$ make install-or-upgrade
$ make wait
$ make links
```
Once `make wait` finishes, you can run `make links` and follow the URL given to check if you can access the deployed software.

### Helm Charts
Installation of Helm should be done as part of familiarising with SKA Tango Examples. This will also help you getting familiar with what a Helm Chart is.

Helm Charts are basically a templating solution that enables a large project such as the SKA to configure a set of standard kubernetes resources using configuration parameters. A Chart is essentially a folder with a general structure, which can be packaged in a .tar.gz file and published to a Helm Repository, or used locally for deployment. 

For an understanding of how Helm Charts are used in the SKAMPI project, please go to the section on [Templating the Application](https://developer.skao.int/en/latest/tools/containers/orchestration-guidelines.html#templating-the-application) under the [Container Orchestration Guidelines](https://developer.skao.int/en/latest/tools/containers/orchestration-guidelines.html) of the [Developer Portal](https://developer.skao.int/en/latest/).

## Development
The following sections are aimed at developers who want to integrate their products/components, or who want to add integration or system-level tests to the repository.

### Adding a new product/component

### Modifying deployment configuration

### Testing

## FAQ

## Getting Help
