# MVP Acceptance Tests  

This section contains the testing scripts and configuration data for performing end to end tests on the MVP.

## Concepts 

The tests aims to replicate a user operating on the system to achieve a set of user requirements. To help with automation the interface is via a text based interactive OET console. Thus the entrypoint into the system is on the OET. Future tests should also explore the greater use of GUI's (e.g. webjive) as entry points.

To observe the system requires looking at the internal state of the system. This is currently implemented using the TANGO framework but in future may include accessing the kubernetes framework and other SDP related communication frameworks.

## Architecture

To ensure the test scripts are executing via the OET they have to be invoked on an exact replica of the OET execution environment. Thus the container (and therefore pod) used in performing the test must be loaded with the exact same image (or package) that will be used in deploying the MVP during production. For testing the MVP in the CI pipeline this is acheived by ensuring the test runner is loaded with the same container image as used for the oet. During development the user can make use of an interactive pod that gets deployed with a skampi repository as its volume using the same image as for the oet container.

Note that during interactive development the testing deployment consists of two parts:

1. The git storage (Persistance Volume CLaim and Persistance Volume)
2. The test pod (mounting on the storage)

The git storage allows the skampi repository to be mounted as a volume onto the container. This allows the tester to interactively work on the testing scripts whilst executing them on an container instance.

## Getting Started

### Using it interactively

*this section assumes you are using a visul code IDE *
 
In the git repository, cloned on your kubernetes enabled machine, navigate to the root directory:

```bash
cd ~/skampi/test-harness/tests/acceptance_tests/
```

To deploy the acceptance tester in interactive mode run:

```bash
make acc_deploy_interactive
```

The system will install a storage pv and pvc (or update it) and instantiate an `acceptance-testing-pod` on the `integration` namespace using the exact same `oet-ssh` image currently configured. The `acceptance-testing-pod` will mount to the `skampi` repository at `/home/tango/skampi/`. You can get the status of the deployment running:

```bash
make acc_get_status
```

afterwards you can get the shh connection details by running:

```bash
$ make acc_get_ssh_par
$ Use this port to shh in: 31910
```

Replace `31910` with the value you get. Then set up a remote ssh connection in visual studio by pasting this in the configuration:

```yaml
Host engage-VM-acceptance-testing
  HostName <your machine IP>
  Port <your port nr>
  User tango
```

Upon entering the container execution enviornment, you should install the python extension on your IDE. The shell will normally open in iTango that allows you to test commands on the OET. When exiting iTango (`exit()`), navigate to skampi to work on your testing scripts `/home/tango/skampi/`. To run tests manualy you need to first invoke the correct interpreter:

```shell
. /venv/bin/activate
```

Thereafter, the neccessarry dependencies will be loaded allowing you access to the correct oet.domain libraries. During development you can navigate to the test-harness folder:

```shell
cd test-harness/
```
To install tests depencies on your development pod run

```shell
make install
```

Tests are initiated by:

```shell
py.test
```

### Running tests automatically

To run a test autimatically the test runner pod is used as deployed by the ci pipeline. This forms part of the general testing that gets run during the testing stage and gets invoked by:

```shell
make K8s_test:
```
Note that the testing configuration is set up so that it will ignore tests ending with "_dev". This allows one to isolate tests that are committed to master but not yet released for testing the pipeline.

Before commiting your code to master make sure the the tests execute during the test pipeline by running above command.