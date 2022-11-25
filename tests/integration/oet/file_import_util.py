# This utility helps in importing file from your host to kubernetes pod at run time.
import os
import tarfile
from tempfile import TemporaryFile
from kubernetes import client, config
from kubernetes.stream import stream

try:
    """
    Get the kubeconfig for a cluster that could potentially be:
    1. a 'local' Minikube cluster
    2. a Cloud deployment (Gitlab CI)
    3. a PSI cluster

    Getting the kubeconfig for these different scenarios is slightly different.
    """
    kubeconfig_filepath = None
    if "KUBECONFIG" in os.environ:
        logging.info(
            "kubeconfig already exists in ENV VAR, skipping: "
            + os.environ["KUBECONFIG"]
        )
        kubeconfig_filepath = os.environ["KUBECONFIG"]
    else:
        if os.path.isfile(os.path.join(os.environ["HOME"], ".kube", "config")):
            logging.info(
                "kubeconfig already exists, skipping: "
                + os.path.join(os.environ["HOME"], ".kube", "config")
            )
            kubeconfig_filepath = os.path.join(os.environ["HOME"], ".kube", "config")
        else:
            logging.info(
                f"Defaulting to loading kubeconfig from {kubeconfig_filepath}."
            )
            kubeconfig_filepath = os.path.join(assets_dir, "kubeconfig")

    logging.info(f"loading kubeconfig from {kubeconfig_filepath}.")
    config.load_kube_config(kubeconfig_filepath)
except TypeError:
    config.load_incluster_config()

api = client.CoreV1Api()

if "CLUSTER_TEST_NAMESPACE" in os.environ:
    cluster_name_space = os.environ["CLUSTER_TEST_NAMESPACE"]
    logging.info(
        "cluster namespace name: "
        + os.environ["CLUSTER_TEST_NAMESPACE"]
    )
else:
    cluster_name_space = "default"

def copy_file_to_pod(pod_name,  exec_command,  source_file_path, namespace=cluster_name_space, api_instance=api,
                     destination_file_path="/tmp/oda"):

    resp = stream(api_instance.connect_get_namespaced_pod_exec, pod_name, namespace,
                  command=exec_command,
                  stderr=True, stdin=True,
                  stdout=True, tty=False,
                  _preload_content=False)

    with TemporaryFile() as tar_buffer:
        with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
            tar.add(name=source_file_path, arcname=destination_file_path + "/" + source_file_path)
        tar_buffer.seek(0)

        commands = list()
        commands.append(tar_buffer.read())

        while resp.is_open():
            resp.update(timeout=1)
            if resp.peek_stdout():
                print("STDOUT: %s" % resp.read_stdout())
            if resp.peek_stderr():
                print("STDERR: %s" % resp.read_stderr())
            if commands:
                c = commands.pop(0)
                resp.write_stdin(c)
            else:
                break
        resp.close()


# Copying file from client -> pod
# print('copying file from client -> pod')
# pod = "ska-oso-oet-rest-test-0"
# namespace = "ska-oso-oet"
# exec_command = ['tar', 'xvf', '-', '-C', '/']
# source_file_path="mid_test.json"
# copy_file_to_pod(pod_name=pod, namespace=namespace, exec_command=exec_command, api_instance=api, source_file_path=source_file_path)
# print("file copied")
