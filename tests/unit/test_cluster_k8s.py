"""Basic cluster functionality tests."""
import logging
import os
import subprocess
import time

import pytest
import requests
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException


@pytest.fixture(name="assets_dir")
def fxt_assets_dir():
    cur_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.realpath(os.path.join(cur_path, "..", "resources", "assets"))


@pytest.fixture(name="manifest")
def fxt_manifest(assets_dir):
    # Ensure manifest file exists
    manifest_filepath = os.path.realpath(
        os.path.join(assets_dir, "cluster_unit_test_resources.yaml")
    )
    logging.info(f"FILE PATH: {manifest_filepath}")
    assert os.path.isfile(manifest_filepath)
    return manifest_filepath


@pytest.fixture(autouse=True)
def fxt_k8s_cluster(assets_dir):
    """
    Get the kubeconfig for a cluster that could potentially be:
    1. a 'local' Minikube cluster
    2. a Cloud deployment (Gitlab CI)
    3. a PSI cluster

    Getting the kubeconfig for these different scenarios is slightly different.

    :param assets_dir: A string representing the path to the directory containing
        the necessary assets for accessing the Kubernetes cluster.
    """
    kubeconfig_filepath = None
    if "KUBECONFIG" in os.environ:
        logging.info("kubeconfig already exists in ENV VAR, skipping: " + os.environ["KUBECONFIG"])
        kubeconfig_filepath = os.environ["KUBECONFIG"]
    else:
        if os.path.isfile(os.path.join(os.environ["HOME"], ".kube", "config")):
            path = os.path.join(os.environ["HOME"], ".kube", "config")
            logging.info(f"kubeconfig already exists, skipping: {path}")
            kubeconfig_filepath = os.path.join(os.environ["HOME"], ".kube", "config")
        else:
            logging.info(f"Defaulting to loading kubeconfig from {kubeconfig_filepath}.")
            kubeconfig_filepath = os.path.join(assets_dir, "kubeconfig")

    assert os.path.isfile(kubeconfig_filepath)

    logging.info(f"loading kubeconfig from {kubeconfig_filepath}.")
    os.environ["KUBECONFIG"] = kubeconfig_filepath
    config.load_kube_config(kubeconfig_filepath)

    try:
        nodes = subprocess.run(
            ["kubectl", "get", "nodes", "-o", "wide"],
            check=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        for line in nodes.stdout.split("\n"):
            logging.info(line)
    except subprocess.CalledProcessError as err:
        logging.warning("'kubectl get nodes' returned the following error: %s", str(err))


@pytest.fixture(name="test_namespace")
def fxt_test_namespace(manifest):
    """
    The tests run in a namespace that may vary given the setup.
    When run locally, no CI job exists - thus the default namespace
    is used. As a 'local default', in case users don't want to use their
    default namespace, we provide the preset value `ci-local` in the makefiles

    :param manifest:  A dictionary containing the manifest data
        for the namespace setup to be tested

    :yields: Namespace
    """
    logging.info(f"Current working directory: {os.getcwd()}")
    logging.info(f"Manifest returns: {manifest}")

    # Run test in default ns on local cluster, specific namespace in CI job
    if "CLUSTER_TEST_NAMESPACE" in os.environ:
        _namespace = os.environ["CLUSTER_TEST_NAMESPACE"]
        try:
            namespaces = client.CoreV1Api().list_namespace()
        except Exception as e:
            pytest.skip(f"Kubernetes not found: {e}")
        if not any(ns.metadata.name == _namespace for ns in namespaces.items):
            namespace = client.V1Namespace(
                kind="Namespace",
                api_version="v1",
                metadata=client.V1ObjectMeta(name=_namespace),
            )
            client.CoreV1Api().create_namespace(namespace)
            logging.info(f"Namespace {namespace.metadata.name} created")
        else:
            logging.info(f"Namespace {_namespace} already existed - bad sign for test" " setup")

    else:
        _namespace = "default"

    yield _namespace

    if _namespace != "default":
        client.CoreV1Api().delete_namespace(name=_namespace, async_req=True)


@pytest.fixture(name="persistentvolumeclaim")
def fxt_pvc(test_namespace):
    pvc_name = "pvc-test"
    api = client.CoreV1Api()
    pvc_body = client.V1PersistentVolumeClaim(
        api_version="v1",
        kind="PersistentVolumeClaim",
        metadata=client.V1ObjectMeta(
            name=pvc_name,
        ),
        spec=client.V1PersistentVolumeClaimSpec(
            storage_class_name="nfss1",
            access_modes=["ReadWriteMany"],
            resources=client.V1ResourceRequirements(requests={"storage": "1Gi"}),
        ),
    )

    try:
        response = api.create_namespaced_persistent_volume_claim(
            namespace=test_namespace, body=pvc_body
        )
        logging.info("Response is %s", response)
    except ApiException as e:
        logging.error("That didn't work: %s" % e)

    pvcs = api.list_namespaced_persistent_volume_claim(namespace=test_namespace)
    logging.info(f"PVC {pvcs.items[0].metadata.name} currently" f" {pvcs.items[0].status.phase}")
    assert len(pvcs.items) == 1

    yield pvc_name
    logging.info("Destroying PersistentVolumeClaim")
    delete_pvc = api.delete_namespaced_persistent_volume_claim(
        name="pvc-test", namespace=test_namespace
    )
    assert delete_pvc, "Unable to delete PVC"


@pytest.fixture(name="all_the_things")
def fxt_deployments_and_services(test_namespace, manifest, persistentvolumeclaim):
    logging.info(f"Creating resources in namespace: {test_namespace}")
    k_cmd = [
        "kubectl",
        "-n",
        test_namespace,
        "-f",
        manifest,
        "apply",
    ]

    let_there_be_things = subprocess.run(
        k_cmd, check=True, stdout=subprocess.PIPE, universal_newlines=True
    )
    for line in let_there_be_things.stdout.split("\n"):
        logging.info(line)

    yield let_there_be_things.returncode

    k_cmd = [
        "kubectl",
        "-n",
        test_namespace,
        "delete",
        "--grace-period=0",
        "--ignore-not-found",
        "-f",
        manifest,
    ]

    logging.info("Destroying all the things")
    destroy_the_things = subprocess.run(k_cmd, check=True)
    assert destroy_the_things.returncode == 0


@pytest.fixture(name="ingress")
def fxt_create_ingress(test_namespace, assets_dir):
    """
    Load the cluster_test_ingress.yaml file
    patch the host names with namespace
    create ingress with temp manifest
    Teardown

    :param test_namespace: A test namespace for cluster
    :param assets_dir: A string representing the path to the directory containing
        the necessary assets for accessing the Kubernetes cluster.

    TODO: This is needed because the currently used version of the python
    kubernetes lib doesn't have the V1 ingress API implemented yet.
    Therefore this method can be updated in future to use the API directly.

    :yields: Return Code
    """
    import yaml

    manifest_filepath = os.path.realpath(os.path.join(assets_dir, "cluster_test_ingress.yaml"))
    patched_manifest_filepath = os.path.join(assets_dir, "tmp_ingress.yaml")
    with open(manifest_filepath) as f:
        ingress = yaml.safe_load(f)
        if ingress["spec"]["rules"][0]["host"] == "nginx1":
            logging.info(f"Setting Host to nginx1-{test_namespace}")
            ingress["spec"]["rules"][0]["host"] = "nginx1-" + test_namespace
        if ingress["spec"]["rules"][1]["host"] == "nginx2":
            logging.info(f"Setting Host nginx2 to nginx2-{test_namespace}")
            ingress["spec"]["rules"][1]["host"] = "nginx2-" + test_namespace
        with open(patched_manifest_filepath, "w") as pf:
            yaml.safe_dump(ingress, pf, default_flow_style=False)

    k_cmd_ingress = [
        "kubectl",
        "-n",
        test_namespace,
        "-f",
        patched_manifest_filepath,
        "apply",
    ]

    ingress_result = subprocess.run(
        k_cmd_ingress,
        check=True,
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )

    for line in ingress_result.stdout.split("\n"):
        logging.info(line)

    yield ingress_result.returncode

    k_cmd = [
        "kubectl",
        "-n",
        test_namespace,
        "delete",
        "--grace-period=0",
        "--ignore-not-found",
        "-f",
        patched_manifest_filepath,
    ]

    logging.info("Destroying ingress")
    destroy_ingress = subprocess.run(k_cmd, check=True)
    os.remove(patched_manifest_filepath)

    assert destroy_ingress.returncode == 0


# TODO: PATCH THE INGRESS RESOURCE SO THAT
# IT IS CREATED WITH NAMESPACED HOSTNAME
def write_to_volume(write_service_name, test_namespace, all_the_things, ingress):
    # def write_to_volume(write_service_name, test_namespace, all_the_things):
    logging.info(f"Result of creating all the things: {all_the_things}")

    command_to_run = "echo $(date) > /usr/share/nginx/html/index.html"
    exec_command = ["/bin/sh", "-c", command_to_run]

    v1 = client.CoreV1Api()
    podname = (
        v1.list_namespaced_pod(test_namespace, label_selector="app=" + write_service_name)
        .items[0]
        .metadata.name
    )

    k_cmd = ["kubectl", "-n", test_namespace, "exec", "-i", podname, "--"]
    command = k_cmd + exec_command
    logging.info(f"Executing command {exec_command} on pod {podname}")
    logging.info(f"Full array: {command}")

    write_result = subprocess.run(command, check=True)
    assert write_result.returncode == 0, "Writing to test pod failed"


def curl_service_with_shared_volume(host0, host1, test_namespace):
    # See patch applied to ingress
    host0 = host0 + "-" + test_namespace
    host1 = host1 + "-" + test_namespace

    logging.info("Attempting to curl")
    host = client.Configuration().get_default_copy().host
    logging.info(f"HOST: {host}")
    logging.info(f"Services: {host0}, {host1}; Namespace: {test_namespace}")
    if "LOADBALANCER_IP" in os.environ:
        ip = os.environ["LOADBALANCER_IP"]
    else:
        logging.info("No IP address for Loadbalancer set, using host")
        ip = host.split("//")[1].split(":")[0]
    logging.info(f"LOADBALANCER_IP this is where we go to test: {ip}")
    url1 = "http://" + ip + "/" + host0 + "/"
    url2 = "http://" + ip + "/" + host1 + "/"
    headers1 = {"Host": host0}
    headers2 = {"Host": host1}
    logging.info(f"URL1: {url1}, headers: {headers1}")
    logging.info(f"URL2: {url2}, headers: {headers2}")
    result1 = requests.get(url1, headers=headers1, timeout=5)
    result2 = requests.get(url2, headers=headers2, timeout=5)
    logging.info("Result1: {}".format(result1.text))
    logging.info("Status1: {}".format(result1.status_code))
    logging.info("Result2: {}".format(result2.text))
    logging.info("Status2: {}".format(result2.status_code))
    assert result1.status_code == 200, f"Expected a 200 response, got {result1.status_code}"
    assert result2.status_code == 200, f"Expected a 200 response, got {result2.status_code}"
    assert result1.text == result2.text, f"{result1.text} ain't {result2.text}"


def wait_for_pod(test_namespace, service_name):
    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(test_namespace, label_selector="app=" + service_name)
    logging.info("Checking Pod Readiness...")
    wait_for_seconds = 1.0
    while True:
        all_running = True
        for item in ret.items:
            if not item.status.phase == "Running":
                all_running = False
                time.sleep(wait_for_seconds)
                wait_for_seconds += wait_for_seconds / 3
                if wait_for_seconds > 10:
                    break
                logging.info(
                    f"{item.metadata.name} not yet ready, waiting for" f" {wait_for_seconds}"
                )
                continue

            for status_container in item.status.container_statuses:
                if not status_container.ready:
                    all_running = False
                    break

        if all_running:
            break
        else:
            ret = v1.list_namespaced_pod(test_namespace, label_selector="app=" + service_name)
    logging.info("Pod Ready")


@pytest.mark.skipif(os.getenv("CLUSTER_TESTS") == "skip", reason="Skipping Cluster Tests")
@pytest.mark.infra
def test_cluster(test_namespace, all_the_things, ingress):
    wait_for_pod(test_namespace, "nginx1")
    logging.info("Test: Deployment nginx1 Ready")
    wait_for_pod(test_namespace, "nginx2")
    logging.info("Test: Deployment nginx2 Ready")
    write_to_volume("nginx1", test_namespace, all_the_things, ingress)
    logging.info("Test: Successfully executed a write to a shared volume")
    curl_service_with_shared_volume("nginx1", "nginx2", test_namespace)  # this is the actual test
    logging.info("Test: Successfully executed a write to a shared volume")
    curl_service_with_shared_volume("nginx1", "nginx2", test_namespace)  # this is the actual test
