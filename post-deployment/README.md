# MVP Post Deployment tests 

This section contains the testing scripts and configuration data for performing tests on a deployed MVP.

## Concepts 

The tests aims to verify correct behaviour of the deployed system as a whole. It therefore access the system via the front door and views its state using a set of predefined frameworks and monitoring components

## Architecture

To ensure the test scripts are executing via the front door they have to be invoked using only parts of the MVP that is part of the system under test. Depending on the type of test it may be neccesarry for these parts to be deployed as packages. Refer to the SUT_requirements.txt file for specifying these dependencies.
Note that during interactive development the dev-testing helm application consists of the following parts:

1. A kubernetes testing pod (`dev-testing`) based on a predefined testing image used for both ci testing and interactive developement testing
2. A host path storage that mounts on your host system at the location of where the makefile invoked the pod (i.e. the skampi root). 
3. A side car container (disabled by default) that runs a web server on the testing pod, allowing you to activate a test from a REST command
4. A log consumer pod (`log-consumer`) that aggregates logs from tango devices
4. Kubernetes role bindings giving the pod neccesarry permissions to perform kubernetes operations on the namespace


The host path storage is basically a means of working inside the testing pods (e.g. actively developing tests and running) whilst still being able to save your code to the skampi repository and commit to the repo.

## Getting Started

### Using it interactively

*this section assumes you are using a visul code IDE *
 
In the git repository, cloned on your kubernetes enabled machine, navigate to the root directory:

```bash
cd ~/ska-skampi/
```

To deploy the acceptance tester in interactive mode run:

```bash
make set_up_dev_testing
```

The system will install a helm chart `dev-testing` on the `KUBE_NAMESPACE` namespace using the exact same image used for ci testing (thus ensuring your interactive tests will also work on ci pipeline) The testing-pod )`dev-testing-0` will mount to the `skampi` repository at `/app/skampi/`. 

The testing pod also has an ssh server running that you can access by updating you ssh config file as follows:


```shell
Host testing_pod
    Hostname <your host ip>
    Port 32022
    User tango
```
The password for entering the pod is `vscodessh`. There is also an option to load your public key file onto the dev-testing pod. To do this, place your public key in  `~/.ssh/public_keys/my_key.pub`. Then run `make cp_key KEY_NAME=my_key`

To use the ssh server for developing requires that you have Vscode with `remote extension` installed. This is a plugin that spawns a vscode server process on the pod and allows you to have a debug and terminal service attaced to the pod using the IDE. As this can be resource  intensive, ensure that your network are not limited in bandwith.

The testing environment becomes pre loaded with extensions for testing in vscode. However it is  best to set up your root space as `skampi/post-deployment` to make sure the extension loads the test modules correctly


### Running tests automatically

To run a test autimatically the test runner pod is used as deployed by the ci pipeline. This forms part of the general testing that gets run during the testing stage and gets invoked by:

```shell
make K8s_test:
```
Note that the testing configuration is set up so that it will ignore tests ending with "_dev". This allows one to isolate tests that are committed to master but not yet released for testing the pipeline.

Before commiting your code to master make sure the the tests execute during the test pipeline by running above command.

