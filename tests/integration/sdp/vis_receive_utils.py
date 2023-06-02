"""
Utility functions and classes used for the visibility receive test.
These were copied from the ska-sdp-integration repository
"""
import functools
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
POD_CONTAINER = "data-prep"
POD_COMMAND = [
    "/bin/bash",
    "-c",
    "apt-get update; apt-get -y install curl;"
    "curl https://gitlab.com/ska-telescope/sdp/ska-sdp-realtime-receive-core/-/raw/3.6.0/data/AA05LOW.ms.tar.gz "  # noqa: E501
    "--output /mnt/data/AA05LOW.ms.tar.gz;"
    "cd /mnt/data/; tar -xzf AA05LOW.ms.tar.gz; cd -;"
    " trap : TERM; sleep infinity & wait",
]
DATA_POD_DEF = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {"name": "receive-data"},
    "spec": {
        "securityContext": {"runAsUser": 0},  # run as root so that we can download data
        "containers": [
            {
                "image": "artefact.skao.int/ska-sdp-realtime-receive-modules:3.5.0",  # noqa: E501
                "name": POD_CONTAINER,
                "command": POD_COMMAND,
                "volumeMounts": [{"mountPath": "/mnt/data", "name": "data"}],
            }
        ],
        "volumes": [{"name": "data", "persistentVolumeClaim": {"claimName": "testing"}}],
    },
}


def _k8s_pod_exec(
    exec_command: list,
    pod_name: str,
    container_name: str,
    namespace: str,
    stdout: bool = True,
):
    """
    Execute a command in a Kubernetes Pod

    :param exec_command: command to be executed
            (eg ["bash", "-c", tar_command])
    :param pod_name: pod name where command is executed
    :param container_name: container name within pod
    :param namespace: namespace where pod is running
    :param stdout: enable stdout on channel

    :return: api response - channel connection object
    """
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
        stderr=True,
        stdin=False,
        stdout=stdout,
        tty=False,
        _preload_content=False,
    )

    return api_response


class K8sElementManager:
    """
    An object that keeps track of the k8s elements it creates and the order in
    which they are created, so that users can perform reverse deletion
    of these items on request.

    It creates and deletes:
    - pods
    - helm charts
    - directories within a pod
    """

    def __init__(self):
        self.to_remove = []

    def cleanup(self):
        """
        Delete all known created objects in the reverse order in which they
        were created.
        """
        LOG.info("Run cleanup")

        # wait for pods to be deleted after deletion starts;
        # this should spead up as compared to when one pod has to be
        # completely deleted before the deletion of the next one could start
        to_wait = []

        for cleanup_function, data in self.to_remove[::-1]:
            cleanup_function(*data)

            if cleanup_function == self.delete_pod:
                to_wait.append(data)

        for data in to_wait:
            pod_name, namespace = data
            wait_for_predicate(pod_deleted, f"Pod {pod_name} delete", timeout=100)(
                pod_name, namespace
            )

    def create_pod(self, pod_name: str, namespace: str, pvc_name: str):
        """
        Create the requested POD and keep track of it for later deletion.

        :param pod_name: name of the pod to be created
        :param namespace: namespace in which to create the pod
        :param pvc_name: name of the SDP data PVC that needs to be mounted
                         into the pod
        """
        core_api = client.CoreV1Api()
        pod_spec = DATA_POD_DEF.copy()

        # Update the name of the pod and the data PVC
        pod_spec["metadata"]["name"] = pod_name
        pod_spec["spec"]["volumes"][0]["persistentVolumeClaim"]["claimName"] = pvc_name

        # Check Pod does not already exist
        k8s_pods = core_api.list_namespaced_pod(namespace)
        for item in k8s_pods.items:
            assert (
                item.metadata.name != pod_spec["metadata"]["name"]
            ), f"Pod {item.metadata.name} already exists"

        core_api.create_namespaced_pod(namespace, pod_spec)
        self.to_remove.append((self.delete_pod, (pod_name, namespace)))

    @staticmethod
    def delete_pod(pod_name: str, namespace: str):
        """
        Delete namespaced pod.

        :param pod_name: name of pod to be deleted
        :param namespace: namespace where pod exists
        """
        core_api = client.CoreV1Api()
        core_api.delete_namespaced_pod(
            pod_name, namespace, async_req=False, grace_period_seconds=0
        )

    def helm_install(self, release: str, chart: str, namespace: str, values_file: str):
        """
        Install the requested Helm chart and keep track of it for later
        deletion.

        :param release: The name of the release
        :param chart: The name of the chart
        :param namespace: The namespace where the chart will be installed
        :param values_file: A path to file with values to be
                    handed over to the chart
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

        self.to_remove.append((self.helm_uninstall, (release, namespace)))

    @staticmethod
    def helm_uninstall(release: str, namespace: str):
        """
        Uninstall a Helm chart

        :param release: The name of the release to be uninstalled
        :param namespace: The namespace where the release lives
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

    def output_directory(
        self,
        dataproduct_directory: str,
        pod_name: str,
        container_name: str,
        namespace: str,
    ):
        """
        Remove the output data directory once the test is finished.

        :param dataproduct_directory:
                    directory where data products are saved by test
        :param pod_name: name of pod through which we access the data directory
        :param container_name: name of container within pod
        :param namespace: namespace where pod lives
        """
        self.to_remove.append(
            (
                self.delete_directory,
                (dataproduct_directory, pod_name, container_name, namespace),
            )
        )

    @staticmethod
    def delete_directory(
        dataproduct_directory: str,
        pod_name: str,
        container_name: str,
        namespace: str,
    ):
        """
        Delete a directory

        :param dataproduct_directory: directory where test outputs are written
        :param pod_name: name of pod through which we access the data directory
        :param container_name: name of container within pod
        :param namespace: namespace where pod lives

        Method assumes that the PVC where data are saved
            is mounted at /mnt/data/
        """
        del_command = ["rm", "-rf", f"/mnt/data/{dataproduct_directory}"]
        resp = _k8s_pod_exec(del_command, pod_name, container_name, namespace)
        _consume_response(resp)
        assert resp.returncode == 0


def pvc_exists(pvc_name: str, namespace: str):
    """
    Check if PVC with name `pvc_name` exists in `namespace`

    :param pvc_name: name of the PVC to check
    :param namespace: namespace where to look for the PVC

    :return: boolean value if pvc exists
    """
    core_api = client.CoreV1Api()

    k8s_pvc = core_api.list_namespaced_persistent_volume_claim(namespace)
    for item in k8s_pvc.items:
        if item.metadata.name == pvc_name:
            return True
    return False


def pod_deleted(pod_name: str, namespace: str):
    """
    Check if pod with name `pod_name` has been
    deleted from `namespace`

    :param pod_name: name of the pod to check
    :param namespace: namespace where to look for the PVC
    :return: boolean value if pod is deleted or not
    """
    core_api = client.CoreV1Api()

    k8s_pod = core_api.list_namespaced_pod(namespace)
    for item in k8s_pod.items:
        if item.metadata.name == pod_name:
            return False
    return True


def wait_for_pod(
    pod_name: str,
    namespace: str,
    phase: str,
    timeout: int = TIMEOUT,
    pod_condition: str = "",
):
    """
    Wait for the pod to be Running.

    :param pod_name: name of the pod
    :param namespace: namespace
    :param phase: phase of the pod
    :param timeout: time to wait for the change
    :param pod_condition: if given, the condition through which the pod must
        have passed

    :returns: whether the pod was in the indicated status within the timeout
    """
    core_api = client.CoreV1Api()

    if pod_condition:

        def check_condition(k8s_pod):
            return any(
                c.status == "True" for c in k8s_pod.status.conditions if c.type == pod_condition
            )

    else:

        def check_condition(_):
            return True

    watch_pod = watch.Watch()

    for event in watch_pod.stream(
        func=core_api.list_namespaced_pod,
        namespace=namespace,
        timeout_seconds=timeout,
    ):
        pod = event["object"]

        if pod_name in pod.metadata.name and pod.status.phase == phase and check_condition(pod):
            watch_pod.stop()
            return True

    return False


def _consume_response(api_response):
    """
    Consumes and logs the stdout/stderr from a stream response

    :param api_response: stream with the results of a pod command execution
    """
    while api_response.is_open():
        api_response.update(timeout=1)
        if api_response.peek_stdout():
            LOG.info("STDOUT: %s", api_response.read_stdout().strip())
        if api_response.peek_stderr():
            LOG.debug("STDERR: %s", api_response.read_stderr().strip())
    api_response.close()


def check_data_present(pod_name: str, container_name: str, namespace: str, mount_location: str):
    """
    Check if the data are present in pod

    :param pod_name: name of the pod
    :param container_name: name of the container within the pod
    :param namespace: namespace where pod lives
    :param mount_location: mount location for data in the container

    :returns: exit code of the command
    """
    exec_command = ["ls", mount_location]
    resp = _k8s_pod_exec(
        exec_command,
        pod_name,
        container_name,
        namespace,
        stdout=False,
    )
    _consume_response(resp)
    return resp


def wait_for_predicate(
    func: callable,
    description: str,
    timeout: int = TIMEOUT,
    interval: float = 0.5,
):
    """
    Wait for predicate to be true.

    :param func: callable to test
    :param description: description to use if test fails
    :param timeout: timeout in seconds
    :param interval: interval between tests of the predicate in seconds
    :return: wrapper for wait for predicate function
    """

    @functools.wraps(func)  # preserves information about the original function
    def wrapper(*args, **kwargs):
        start = time.time()
        while True:
            if func(*args, **kwargs):
                break
            if time.time() >= start + timeout:
                pytest.fail(f"{description} not achieved after {timeout} seconds")
            time.sleep(interval)

    return wrapper


def compare_data(pod_name: str, container_name: str, namespace: str, measurement_set: str):
    """
    Compare the data sent with the data received using ms-assert.
    This compares two Measurement Sets.

    :param pod_name: name of the pod through which we connect to data PVC
    :param container_name: name of the container in pod
    :param namespace: namespace where pod lives
    :param measurement_set: name of the Measurement Set to compare

    :returns: exit code of the command
    """
    exec_command = [
        "ms-asserter",
        "/mnt/data/AA05LOW.ms",
        f"/mnt/data/{measurement_set}",
        "--minimal",
        "true",
    ]
    resp = _k8s_pod_exec(exec_command, pod_name, container_name, namespace)
    _consume_response(resp)
    return resp


def deploy_cbf_emulator(endpoint: tuple, scan_id: int, k8s_element_manager: K8sElementManager):
    """
    Deploy the CBF emulator and check that it finished sending the data.

    :param endpoint: A 2-tuple `(host, port)` indicating the first endpoint
        where the receiver is expected to be listening on
    :param scan_id: ID of the scan that is being executed
    :param k8s_element_manager: Kubernetes element manager
    """
    host, port = endpoint

    # Construct command for the sender
    command = [
        "emu-send",
        "/mnt/data/AA05LOW.ms",
        "-o",
        "transmission.transport_protocol=tcp",
        "-o",
        "transmission.method=spead2_transmitters",
        "-o",
        "transmission.num_streams=2",
        "-o",
        "transmission.rate=10416667",
        "-o",
        "reader.num_repeats=1",
        "-o",
        f"transmission.target_host={host}",
        "-o",
        f"transmission.target_port_start={port}",
        "-o",
        f"transmission.scan_id={scan_id}",
        "-o",
        "transmission.telescope=low",
    ]
    values = {
        "command": command,
        "receiver": {"hostname": host, "address_resolution_timeout": 60},
        "pvc": {"name": os.environ.get("SDP_DATA_PVC_NAME", "shared")},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as file:
        file.write(yaml.dump(values))

    filename = file.name
    namespace = os.environ.get("KUBE_NAMESPACE")
    sender_name = f"cbf-send-scan-{scan_id}"

    LOG.info("Deploying CBF sender for Scan %d on chart %s", scan_id, sender_name)
    k8s_element_manager.helm_install(
        sender_name,
        "tests/resources/charts/cbf-sender",
        namespace,
        filename,
    )

    # wait for CBF emulator to finish sending data
    assert wait_for_pod(
        sender_name,
        namespace,
        "Succeeded",
        timeout=300,
    )
