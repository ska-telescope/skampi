# MVP Acceptance Tests  

This section contains the testing scripts and configuration data for performing end to end tests on the MVP.

## Concepts 

The tests aims to replicate a user operating on the system to achieve a set of user requirements. To help with automation the interface is via a text based interactive OET console. Thus the entrypoint into the system is on the OET. Future tests should also explore the greater use of GUI's (e.g. webjive) as entry points.

To observe the system requires looking at the internal state of the system. This is currently implemented using the TANGO framework but in future may include accessing the kubernetes framework and other SDP related communication frameworks.

## Architecture

To ensure the test scripts are executing via the OET they have to be invoked on an exact replica of the OET execution environment. Thus an acceptance tester is deployed using the exact same container (and its configuration) used for the OET. In essence therefore, the acceptance tester become the OET.

The deployment consists of two parts:

1. The git storage (Persistance Volume CLaim and Persistance Volume)
2. The test pod (mounting on the storage)

The git storage allows the skampi repository to be mounted as a volume onto the container. This allows the tester to interactively work on the testing scripts whilst executing them on an container instance.

## Getting Started

### Using it interactively

*this section assumes you are using a visul code IDE*
 
In the git repository, cloned on your kubernetes enabled machine, navigate to the acceptance testing folder:

```bash
cd tests/acceptance_tests/
```

To deploy the acceptance tester in interactive mode run:

```bash
make deploy_interactive
```

The system will install a storage pv and pvc (or update it) and instantiate an `acceptance-testing-pod` on the `integration` namespace using the exact same `oet-ssh` image currently configured. The `acceptance-testing-pod` will mount to the `skampi` repository at `/home/tango/skampi/`. You can get the status of the deployment running:

```bash
make get_status
```

afterwards you can get the shh connection details by running:

```bash
$ make get_ssh_par
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

Thereafter, the neccessarry dependencies will be loaded allowing you access to the correct oet.domain libraries.
Tests are initiated by:

```shell
make cont_test
```

The get your IDE to point to the same execution environment paste the following code into the  `/.vscode/settings.json` file:

```json
"python.pythonPath": "/venv/bin/python3"
```
### Running tests automatically

To run a test autimatically the pod is configured slightly differently as a test job that gets invoked by the following command on your machine:

```shell
make deploy_test_job:
```

This command can then be used in a CI setup to run acceptance tests are part of a pipeline.