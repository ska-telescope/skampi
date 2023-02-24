import enum
import logging
import os
import subprocess
import tempfile
import time

import pytest
import yaml
from kubernetes import client, watch
from kubernetes.stream import stream

LOG = logging.getLogger(__name__)

TIMEOUT = 15
REC_POD = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {"name": "receive-data"},
    "spec": {
        "securityContext": {"runAsUser": 0},  # run as root so that we can download data
        "containers": [
            {
                "image": "artefact.skao.int/ska-sdp-realtime-receive-modules:3.5.0",
                "name": "data-prep",
                "command": [
                    "/bin/bash",
                    "-c",
                    "apt-get update; apt-get -y install curl;"
                    "curl https://gitlab.com/ska-telescope/sdp/ska-sdp-realtime-receive-core/-/raw/3.6.0/data/AA05LOW.ms.tar.gz "
                    "--output /mnt/data/AA05LOW.ms.tar.gz;"
                    "cd /mnt/data/; tar -xzf AA05LOW.ms.tar.gz; cd -;"
                    " trap : TERM; sleep infinity & wait",
                ],
                "volumeMounts": [{"mountPath": "/mnt/data", "name": "data"}],
            }
        ],
        "volumes": [
            {"name": "data", "persistentVolumeClaim": {"claimName": "testing"}}
        ],
    },
}


class K8sElementManager:
    """
    An object that keeps track of the k8s elements it creates, the order in
    which they are created, how to delete them, so that users can perform this
    reverse deletion on request.
    """

    def __init__(self):
        self.to_remove = []

    def cleanup(self):
        """
        Delete all known created objects in the reverse order in which they
        were created.
        """
        LOG.info("Run cleanup")
        for cleanup_function, data in self.to_remove[::-1]:
            cleanup_function(*data)

    def create_pod(self, pod_name, namespace, pvc_name):
        """Create the requested POD and keep track of it for later deletion.

        :param pod_name: name of the pod to be created
        :param namespace: namespace
        :param pvc_name: name of the sdp data pvc

        """
        # Get API handle
        core_api = client.CoreV1Api()
        pod_spec = REC_POD.copy()

        # Update the name of the data pvc and the type of pod
        pod_spec["metadata"]["name"] = pod_name
        pod_spec["spec"]["volumes"][0]["persistentVolumeClaim"]["claimName"] = pvc_name

        # Check Pod does not already exist
        k8s_pods = core_api.list_namespaced_pod(namespace)
        for item in k8s_pods.items:
            assert (
                item.metadata.name != pod_spec["metadata"]["name"]
            ), f"Pod {item.metadata.name} already exists"

        core_api.create_namespaced_pod(namespace, pod_spec)

        self.to_remove.append((delete_pod, (pod_name, namespace)))

    def helm_install(self, release, chart, namespace, values_file):
        """
        Install the requested Helm chart and keep track of it for later
        deletion.

        :param release: The name of the release
        :param chart: The name of the chart
        :param namespace: The namespace where the chart will be installed
        :param values_file: A file with values to be handed over to the chart
        """
        cmd = [
            "helm",
            "install",
            release,
            chart,
            "-n",
            namespace,
            "-f",
            values_file,
            "--wait",
        ]
        subprocess.run(cmd, check=True)

        self.to_remove.append((helm_uninstall, (release, namespace)))

    def output_directory(
        self, dataproduct_directory, pod_name, container_name, namespace
    ):
        """Remove the output directory once the test is finished."""
        self.to_remove.append(
            (
                delete_directory,
                (dataproduct_directory, pod_name, container_name, namespace),
            )
        )


def helm_uninstall(release, namespace):
    """Uninstall a Helm chart

    :param release: The name of the release
    :param namespace: The namespace where the chart lives
    """
    cmd = [
        "helm",
        "uninstall",
        release,
        "-n",
        namespace,
        "--wait",
        "--no-hooks",
    ]
    subprocess.run(cmd, check=True)


def delete_pod(pod_name: str, namespace: str):
    """Delete namespaced pod.

    :param pod_name: name of pod to be deleted
    :param namespace: namespace
    """
    # Get API handle
    core_api = client.CoreV1Api()

    pod_to_remove = pod_name
    core_api.delete_namespaced_pod(pod_to_remove, namespace, async_req=False)


def delete_directory(
    dataproduct_directory, pod_name, container_name, namespace
):
    """Delete a directory

    :param dataproduct_directory: The directory where outputs are written
    :param pod_name: name of the pod
    :param container_name: name of the container
    :param namespace: The namespace where the chart will be installed

    """
    del_command = ["rm", "-rf", f"/mnt/data/{dataproduct_directory}"]
    resp = k8s_pod_exec(
        del_command, pod_name, container_name, namespace, stdin=False
    )
    _consume_response(resp)
    assert resp.returncode == 0


def pvc_exists(pvc_name: str, namespace: str):
    """Check if the pvc from the env variable exists.

    :param pvc_name: name of the sdp data pvc

    """
    core_api = client.CoreV1Api()

    k8s_pvc = core_api.list_namespaced_persistent_volume_claim(namespace)
    for item in k8s_pvc.items:
        if item.metadata.name == pvc_name:
            return True
    return False


class Comparison(enum.Enum):
    """Comparisons for waiting for pods."""

    # pylint: disable=unnecessary-lambda-assignment

    EQUALS = lambda x, y: x == y  # noqa: E731
    CONTAINS = lambda x, y: x in y  # noqa: E731


def wait_for_pod(
    pod_name: str,
    namespace: str,
    phase: str,
    timeout: int = TIMEOUT,
    name_comparison: Comparison = Comparison.EQUALS,
    pod_condition: str = "",
):
    """Wait for the pod to be Running.

    :param pod_name: name of the pod
    :param namespace: namespace
    :param phase: phase of the pod
    :param timeout: time to wait for the change
    :param name_comparison: the type of comparison used to match a pod name
    :param pod_condition: if given, the condition through which the pod must
    have passed

    :returns: whether the pod was in the indicated status within the timeout
    """
    # pylint: disable=too-many-arguments

    # Get API handle
    core_api = client.CoreV1Api()

    if pod_condition:

        def check_condition(pod):
            return any(
                c.status == "True"
                for c in pod.status.conditions
                if c.type == pod_condition
            )

    else:

        def check_condition(_):
            return True

    watch_pod = watch.Watch()
    start_time = int(time.time())

    for event in watch_pod.stream(
        func=core_api.list_namespaced_pod,
        namespace=namespace,
        timeout_seconds=timeout,
    ):
        pod = event["object"]

        if (
            name_comparison(pod_name, pod.metadata.name)
            and pod.status.phase == phase
            and check_condition(pod)
        ):
            watch_pod.stop()
            return True

        # return False a second before timeout is hit, else no error is raised
        if (start_time + timeout-10) <= time.time():
            return False

    return False


def k8s_pod_exec(
    exec_command,
    pod_name,
    container_name,
    namespace,
    stdin=True,
    stdout=True,
    stderr=True,
):
    """Execute a command in a Kubernetes Pod

    param exec_command: command to be executed (eg ["bash", "-c", tar_command])
    param pod_name: Pod name
    param container_name: Container name
    param namespace: Namespace
    param stdin: Enable stdin on channel
    param stdout: Enable stdout on channel
    param stderr: Enable stderr on channel

    returns api_response: Channel connection object
    """
    # pylint: disable=too-many-arguments

    # Get API handle
    core_api = client.CoreV1Api()
    LOG.debug(
        "Executing command in container %s/%s/%s: %s",
        namespace,
        pod_name,
        container_name,
        " ".join(exec_command),
    )

    api_response = stream(
        core_api.connect_get_namespaced_pod_exec,
        pod_name,
        namespace,
        command=exec_command,
        container=container_name,
        stderr=stderr,
        stdin=stdin,
        stdout=stdout,
        tty=False,
        _preload_content=False,
    )

    return api_response


def check_data_present(
    pod_name: str, container_name: str, namespace: str, mount_location: str
):
    """Check if the data are present in pod

    :param pod_name: name of the pod
    :param container_name: name of the container
    :param namespace: namespace
    :param mount_location: mount location for data in the container

    :returns: exit code of the command
    """
    exec_command = ["ls", mount_location]
    resp = k8s_pod_exec(
        exec_command,
        pod_name,
        container_name,
        namespace,
        stdin=False,
        stdout=False,
    )
    _consume_response(resp)
    return resp


def _consume_response(api_response):
    """Consumes and logs the stdout/stderr from a stream response

    :param api_response: stream with the results of a pod command execution
    """
    while api_response.is_open():
        api_response.update(timeout=1)
        if api_response.peek_stdout():
            LOG.info("STDOUT: %s", api_response.read_stdout().strip())
        if api_response.peek_stderr():
            LOG.debug("STDERR: %s", api_response.read_stderr().strip())
    api_response.close()


def wait_for_predicate(predicate, description, timeout=TIMEOUT, interval=0.5):
    """
    Wait for predicate to be true.

    :param predicate: callable to test
    :param description: description to use if test fails
    :param timeout: timeout in seconds
    :param interval: interval between tests of the predicate in seconds

    """
    start = time.time()
    while True:
        if predicate():
            break
        if time.time() >= start + timeout:
            pytest.fail(f"{description} not achieved after {timeout} seconds")
        time.sleep(interval)


def wait_for_obs_state(device, obs_state, timeout=TIMEOUT):
    """
    Wait for obsState to have the expected value.

    :param device: device proxy
    :param obs_state: the expected value
    :param timeout: timeout in seconds
    """

    def predicate():
        return device.read_attribute("obsState").name == obs_state

    description = f"obsState {obs_state}; current one is {device.read_attribute('obsState').name}"
    wait_for_predicate(predicate, description, timeout=timeout)


def deploy_sender(host, scan_id, k8s_element_manager):
    """
    Deploy the cbf sender and check the cbf sender finished sending the data.

    :param context: context for the tests
    :param subarray_device: SDP subarray device client
    :param k8s_element_manager: Kubernetes element manager
    :param assign_resources_config: configuration passed to AssignResources
        command

    """

    # Construct command for the sender
    command = [
        "emu-send",
        "/mnt/data/AA05LOW.ms",
        "-o",
        "transmission.transport_protocol=tcp",
        "-o",
        "transmission.method=spead2_transmitters",
        "-o",
        "transmission.channels_per_stream=6912",
        "-o",
        "transmission.rate=10416667",
        "-o",
        "reader.num_repeats=1",
        "-o",
        f"transmission.target_host={host}",
        "-o",
        f"transmission.scan_id={scan_id}",
    ]
    values = {
        "command": command,
        "receiver": {"hostname": host, "address_resolution_timeout": 60},
        "pvc": {"name": os.environ.get("SDP_DATA_PVC_NAME", "shared")},
    }

    # Deploy the sender
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as file:
        file.write(yaml.dump(values))

    filename = file.name
    sender_name = f"cbf-send-scan-{scan_id}"
    LOG.info("Deploying CBF sender for Scan %d on chart %s", scan_id, sender_name)
    k8s_element_manager.helm_install(
        sender_name,
        "tests/resources/charts/cbf-sender",
        os.environ.get("KUBE_NAMESPACE"),
        filename,
    )

    assert wait_for_pod(
        sender_name,
        os.environ.get("KUBE_NAMESPACE"),
        "Succeeded",
        300,
        name_comparison=Comparison.CONTAINS,
    )


def compare_data(
    pod_name: str, container_name: str, namespace: str, measurement_set: str
):
    """Compare the data sent with the data received.

    :param pod_name: name of the pod
    :param container_name: name of the container
    :param namespace: namespace
    :param measurement_set: name of the Measurement Set to compare

    :returns: exit code of the command
    """
    # To test if the sent and received data match using ms-asserter

    exec_command = [
        "ms-asserter",
        "/mnt/data/AA05LOW.ms",
        f"/mnt/data/{measurement_set}",
        "--minimal",
        "true",
    ]
    resp = k8s_pod_exec(
        exec_command, pod_name, container_name, namespace, stdin=False
    )
    _consume_response(resp)
    return resp
