import logging
from pathlib import Path
import tarfile
from tempfile import TemporaryFile, TemporaryDirectory
from typing import cast
from kubernetes.client.api.core_v1_api import CoreV1Api
from kubernetes.stream import stream
import os


def search_for_pod(v1_api: CoreV1Api, **kwargs: str) -> str | None:
    """Search for a pod in current namespace according to given key value pairs.

    :param v1_api: the kubernetes client api to use
    :return: The name of the pod if found, otherwise returns None
    """
    selector_str = ",".join([f"{key}={value}" for key, value in kwargs.items()])
    namespace = get_kube_namespace()
    assert namespace, (
        "Unable to interact with kubernetes without a given namespace, "
        "Did you set KUBE_NAMESPACE?"
    )
    result = v1_api.list_namespaced_pod(namespace, label_selector=selector_str)
    if result.items:
        return cast(str, result.items[0].metadata.name)
    else:
        return None


def get_kube_namespace() -> str:
    """get the namespace defined by KUBE_NAMESPACE

    :return: the namespace
    :raises: AssertionError when no KUBE_NAMESPACE value is found
    """
    namespace = os.getenv("KUBE_NAMESPACE")
    assert namespace, (
        "Unable to interact with kubernetes without a given namespace, "
        "Did you set KUBE_NAMESPACE?"
    )
    return namespace


def cp_str_json_file_to_pod(
    api: CoreV1Api,
    source_file: str,
    pod_name: str,
    namespace: str,
    destination_path: str,
):
    """Copy a json or text file to a given path mounted to a given pod

    :param api: the kubernetes client api to use
    :param source_file: the path of file located in host
    :param namespace: the cluster namespace where pod is located
    :param pod_name: the name identifying the pod
    :param destination_path: the path of where the file must be mounted on the pod
    """
    source_file_path = Path(source_file)
    assert source_file_path.suffix in [
        ".json",
        ".txt",
    ], f"Only json and txt files are supported, you gave {source_file_path.suffix}"

    exec_command = ["tar", "xvf", "-", "-C", "/"]
    response = stream(
        api.connect_get_namespaced_pod_exec,
        pod_name,
        namespace,
        command=exec_command,
        stderr=True,
        stdin=True,
        stdout=True,
        tty=False,
        _preload_content=False,
    )

    with TemporaryDirectory() as temp_dir:
        if source_file_path.suffix == ".json":
            # save json file as a text file since only text based files work
            text_file_path = Path(f"{temp_dir}/text_file.txt")
            with open(text_file_path, "wt") as text_file:
                with open(source_file_path, "rt") as json_file:
                    text_file.write(json_file.read())
        else:
            text_file_path = source_file_path
        with TemporaryFile() as tar_buffer:
            with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                tar.add(name=text_file_path, arcname=destination_path)
            tar_buffer.seek(0)
            data = tar_buffer.read()

            while response.is_open():
                response.update(timeout=1)
                if response.peek_stdout():
                    logging.info(f"STDOUT: {response.read_stdout()}")
                if response.peek_stderr():
                    logging.info(f"STDERR: {response.read_stderr()}")
                if data:
                    response.write_stdin(data)
                    data = None
                else:
                    break
            response.close()