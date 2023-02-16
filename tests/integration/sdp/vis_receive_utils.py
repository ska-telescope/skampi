import logging
import subprocess

from kubernetes import client, watch
from kubernetes.stream import stream

LOG = logging.getLogger(__name__)

TIMEOUT = 15
REC_POD = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {"name": "receive-data"},
    "spec": {
        "containers": [
            {
                "image": "python:3.10-slim",
                "name": "data-prep",
                "command": [
                    "/bin/bash",
                    "-c",
                    "apt-get update; apt-get -y install curl;"
                    "curl https://gitlab.com/ska-telescope/sdp/ska-sdp-realtime-receive-core/-/raw/main/data/AA05LOW.ms.tar.gz "
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


def wait_for_pod(
    pod_name: str,
    namespace: str,
    phase: str,
    timeout: int = TIMEOUT,
    pod_condition: str = "",
):
    """Wait for the pod to be Running.

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
    for event in watch_pod.stream(
        func=core_api.list_namespaced_pod,
        namespace=namespace,
        timeout_seconds=timeout,
    ):
        pod = event["object"]
        if (
            pod_name in pod.metadata.name
            and pod.status.phase == phase
            and check_condition(pod)
        ):
            watch_pod.stop()
            return True
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
        "".join(exec_command),
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
            LOG.info("STDERR: %s", api_response.read_stderr().strip())
    api_response.close()
