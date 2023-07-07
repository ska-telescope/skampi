# SKA MVP Prototype Integration Testing

SKAMPI was restructured into two parts - build/deploy and testing. This repository concerns **testing** only, as that will allow faster workflows for developers to run tests against SKAMPI deployments. This separation brings the ability to quickly run a test, multiple times, with different test configurations and targetting different namespaces, on demand. The deployment of SKAMPI now is done at [ska-skampi-deplopyment](https://gitlab.com/ska-telescope/ska-skampi-deployment). In the pipelines of that repository, we already have jobs to trigger these tests in **on-demand** deployments.

>The SKAMPI specific make targets were removed in place of generic ones where possible, to facilitate the maintenance of SKAMPI. Going forwards, always try to contribute to [.make](https://gitlab.com/ska-telescope/sdi/ska-cicd-makefile) instead of adding custom SKAMPI targets.

## CI/CD Pipeline

The CI/CD pipeline was refactored to be test-focused only, although, we still need continuous testing on the changes we do to the tests. Therefore, we have now 2 testing stages:

* **trigger** - This stage triggers a deploy and test pipeline in [ska-skampi-deplopyment](https://gitlab.com/ska-telescope/ska-skampi-deployment) (which in turn creates pipelines in this repository to run the low and mid tests)
* **test** - Manual test stages that can be used to run a test against any cluster. Currently we suport tests in STFC-Techops cluster (test-low and test-mid jobs) and STFC-DP cluster (test-low-dp and test-mid-dp)
  * On **merge request** pipelines, **test-low** and **test-mid** will automatically run against **integration-low** and **integration-mid** respectively

This way, any changes we do are tested against a fresh SKAMPI deployment, so that we can decouple the occurence of failures from the state of the environment. As mentioned above, if the pipeline is a **merge request** pipeline, it will run its tests against the integration environment in STFC-Techops for validation.  This can help us further differentiate where issues might come from and make sure our tests still hold true for long-running environments.

Note that we can still manually trigger tests on on-demand deployments. This increases the options we have to run tests. As we can retry deployments and tests separetely, if needed, we now have the abitlity to run more tests in a shorter amount of time.

## Before you begin
For information on how to use the subsystems / components that are deployed using SKAMPI, please first look at the documentation on [SKAMPI Subsystems](https://developer.skao.int/projects/ska-skampi-deployment/en/latest/subsystems.html).

>Note: Information regarding the deployment of SKAMPI was moved to [ska-skampi-deplopyment](https://gitlab.com/ska-telescope/ska-skampi-deployment)

# Getting Started
[![Documentation Status](https://readthedocs.org/projects/ska-telescope-ska-skampi/badge/?version=latest)](https://developer.skatelescope.org/projects/ska-skampi/en/latest/?badge=latest)

### Cloning the repository
Checkout the repository and ensure that submodules (including `.make`) are cloned with:
```
$ git clone --recurse-submodules git@gitlab.com:ska-telescope/ska-skampi.git
$ cd ska-skampi
```

### Setting up the local Python environment
After checking out the repository, and making sure **Python** and **poetry** are present, do:
```
$ poetry install
```

### Required tools
Other than the repository and Python, it is required to have the following tools installed, to work with Kubernetes:

* [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
* [helm](https://helm.sh/docs/intro/install/)

### Kubernetes cluster
SKAMPI is meant to be deployed - using an Helm chart - to a Kubernetes cluster. Usually, running tests locally target a local cluster, that you can setup with [minikube](https://gitlab.com/ska-telescope/sdi/ska-cicd-deploy-minikube/). In this case, you need to [deploy](https://gitlab.com/ska-telescope/ska-skampi-deployment) SKAMPI yourself.

If you need access to a cluster, please reach out to [#team-system-support](https://skao.slack.com/archives/CEMF9HXUZ) to ask for access. Bear in mind that this access might not be possible. 

>In the particular case of SKAMPI **on-demand** deployments, a Kubeconfig is generated in the pipeline, that can be used to test an environment from the local machine.

## Testing

Testing can be done in three different ways:

* Local
  * Requires acess to the Kubernetes cluster
  * Local machine setup is required
* CI/CD Pipelines
  * Non interactive
  * No setup required
* Binderhub
  * Requires acess to the Kubernetes cluster
  * No setup required

For local clusters, only **Local** tests can be ran. For remote clusters, we can use any of the above, altough, the recommended way is to do it in cluster (i.e., CI/CD or Binderhub).

>Check the [testing documentation](https://developer.skao.int/projects/ska-skampi/en/latest/testing.html#running-tests-in-ci-cd-pipelines) for more information on running tests.

### Environment Settings
To check what some of the most commonly used variables are that your Makefile will use when you run any commands (defaults or environment specific), you can run:

```
$ make vars
```

This should give you all the basic environment variables needed to run the `make` commands as they are called in CI jobs, in case you want to debug environment configuration issues.

### Running tests

First, make sure you followed the [requirements](#getting-started). Now, we need to be able to access a Kubernetes cluster where SKAMPI has been deployed.

Then, we can configure our Kubernetes cluster:
```
export KUBECONFIG=<path to the kubeconfig>
kubectl get nodes
```

Finally, one can run the tests by running:
```
poetry shell
export KUBE_NAMESPACE=<skampi namespace>
kubectl get pods -n $KUBE_NAMESPACE
make k8s-test CONFIG=<mid or low>
```

There are a few variables we can use to change the testing behavior:

* `PYTEST_MARK`: Allows to set the default test selection expression for the telescope tests
* `PYTEST_SUBSYS_MARK`: Allows to an extra expression (anded with `PYTEST_MARK`) to select subsystem tests
* `PYTEST_COUNT`: Set the number of times the tests are executed
* `HELM_RELEASE`: Sets the Helm release to consider when testing (it will auto-detect as well)
* `XRAY_UPLOAD_ENABLED`: Controlls if the the test results are uploaded to XRay or not

Also, the following flags are avilable (set to `true`/`false`):
* Skallop:
  * `SKALLOP_LOG_FILTER_ERRORS`
  * `DISABLE_MAINTAIN_ON`
  * `USE_OLD_DISH_IDS`
  * `USE_ONLY_POLLING`
  * `DEBUG_WAIT`
  * `USE_POD_KUBECONFIG`
  * `MOCK_SUT`
  * `CHECK_INFRA_PER_TEST`
  * `CHECK_INFRA_PER_SESSION`
* Tests:
  * `DEBUG_ENTRYPOINT`
  * `SHOW_STEP_FUNCTIONS`
  * `ATTR_SYNCH_ENABLED`
  * `ATTR_SYNCH_ENABLED_GLOBALLY`
  * `LIVE_LOGGING_EXTENDED`
  * `LIVE_LOGGING`
  * `REPLAY_EVENTS_AFTERWARDS`
  * `CAPTURE_LOGS`
  * `DEVENV`

Check the Makefile for other variables that might be necessary to successfully run the tests.

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
