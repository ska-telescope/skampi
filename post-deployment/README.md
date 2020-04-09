# MVP Post Deployment tests 

This section contains the testing scripts and configuration data for performing tests on a deployed MVP.

## Concepts 

The tests aims to verify correct behaviour of the deployed system as a whole. It therefore access the system via the front door and views its state using a set of predefined frameworks and monitoring components

## Architecture

To ensure the test scripts are executing via the front door they have to be invoked using only parts of teh MVP that is part of the system under test. Depending on the type of test it may be neccesarry for these parts to be deployed as packages. Refer to the SUT_requirements.txt file for specifying these dependencies.
Note that during interactive development the testing deployment consists two parts

1. A kubernetes testing pod (`testing-pod`) based on a predefined testing image used for both ci testing and interactive developement testing
2. A host path storage that mounts on your host system at the location of where the makefile invoked the pod (i.e. the skampi root). 

The host path storage is basically a means of working inside the testing pods (e.g. actively developing tests and running) whilst still being able to save your code to the skampi repository and commit to the repo.

## Getting Started

### Using it interactively

*this section assumes you are using a visul code IDE *
 
In the git repository, cloned on your kubernetes enabled machine, navigate to the root directory:

```bash
cd ~/skampi/
```

To deploy the acceptance tester in interactive mode run:

```bash
make deploy_testing_pod
```

The system will install  `testing-pod` on the `KUBE_NAMESPACE` namespace using the exact same image used for ci testing (thus ensuring your interactive tests will also work on ci pipeline) The `testing-pod` will mount to the `skampi` repository at `/app/skampi/`. 

The testing pod aslo has an ssh server running that you can access by updating you ssh config file as follows:


```shell
Host testing_pod
    Hostname <your host ip>
    Port 2020
    User tango
```
The password for entering the pod is `vscodessh`

You can use these settings to enter the pod using vscode's remote ssh extensions
Alternatively you can enter the bash shell of the pod using `make attach_testing_pod`

Upon entering the container execution enviornment chage diretory:
```shell
cd skampi/post-deployment
```


Thereafter, install the dependencies:

```shell
make install
```
To run tests:

```shell
make test
```

To run the tests in a non interactive way you simply run from the skampi root:

```shell
make k8s_test
```

### Running tests automatically

To run a test autimatically the test runner pod is used as deployed by the ci pipeline. This forms part of the general testing that gets run during the testing stage and gets invoked by:

```shell
make K8s_test:
```
Note that the testing configuration is set up so that it will ignore tests ending with "_dev". This allows one to isolate tests that are committed to master but not yet released for testing the pipeline.

Before commiting your code to master make sure the the tests execute during the test pipeline by running above command.

