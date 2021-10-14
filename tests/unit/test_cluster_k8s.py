"""Basic cluster functionality tests."""
import logging
import pytest
import os
import requests
import time
import subprocess
from kubernetes import config, client
from kubernetes.stream import stream

# @pytest_fixture(scope="module", name="genesis")
# def fxt_create_all_the_things()
    # creation = subprocess.run(k_cmd).returncode

@pytest.fixture(name="manifest", scope="module")
def fxt_manifest():
    return os.path.realpath(os.path.join(os.getcwd(),'..','reources','assets','cluster_unit_test_resources.yaml'))

@pytest.fixture(name="test_namespace", scope="module")
def fxt_test_namespace(manifest):

    logging.info(f"Current working directory: {os.getcwd()}")    
    logging.info(f"Manifest returns: {manifest}")

    if "CI_JOB_ID" in os.environ:
        _namespace = 'ci-' + os.environ["CI_JOB_ID"]
    else:
        _namespace = "default"
    yield _namespace

    k_cmd = ["kubectl", "-n", _namespace, "delete", "--grace-period=0", "--ignore-not-found", "--force", "-f", "tests/resources/assets/cluster_integration_test_resources.yaml"]
    destroyed_result = subprocess.run(k_cmd).returncode

    assert destroyed_result == 0

    # v1 = client.CoreV1Api()
    # beta = client.ExtensionsV1beta1Api()
    # appsv1 = client.AppsV1Api()

    # for ingress in beta.list_namespaced_ingress(_namespace).items:
    #     beta.delete_namespaced_ingress(
    #         ingress.metadata.name, _namespace, grace_period_seconds=0
    #     )

    # for svc in v1.list_namespaced_service(_namespace).items:
    #     v1.delete_namespaced_service(
    #         svc.metadata.name, _namespace, grace_period_seconds=0
    #     )

    # for cfgm in v1.list_namespaced_config_map(_namespace).items:
    #     v1.delete_namespaced_config_map(
    #         cfgm.metadata.name, _namespace, grace_period_seconds=0
    #     )

    # for depl in appsv1.list_namespaced_deployment(_namespace).items:
    #     appsv1.delete_namespaced_deployment(
    #         depl.metadata.name, _namespace, grace_period_seconds=0
    #     )

    # for pvc in v1.list_namespaced_persistent_volume_claim(_namespace).items:
    #     v1.delete_namespaced_persistent_volume_claim(
    #         pvc.metadata.name, _namespace, grace_period_seconds=0
    #     )

    # v1.delete_persistent_volume("pvtest", grace_period_seconds=0)

    v1.delete_namespace(_namespace)


@pytest.fixture(autouse=True, scope="module")
def k8s_cluster():
    logging.info("loading kubeconfig")
    config.load_kube_config()


def write_to_volume(write_service_name, test_namespace):
    command = "echo $(date) > /usr/share/nginx/html/index.html"
    exec_command = ["/bin/sh", "-c", command]
    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(
        test_namespace, label_selector="app=" + write_service_name
    )
    logging.debug(
        "Executing command " + command + " on pod " + ret.items[0].metadata.name
    )
    resp = stream(
        v1.connect_get_namespaced_pod_exec,
        ret.items[0].metadata.name,
        test_namespace,
        command=exec_command,
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
    )
    logging.info(resp)


def curl_service_with_shared_volume(host0, host1, test_namespace):
    host = client.Configuration().get_default_copy().host
    logging.debug(f"HOST: {host}")
    logging.debug(f"Services: {host0}, {host1}; Namespace: {test_namespace}")
    ip = host.split("//")[1].split(":")[0]
    url = "http://" + ip + "/"
    logging.debug(f"URL1: {url}")
    result1 = requests.get(url, headers={"Host": host0})
    result2 = requests.get(url, headers={"Host": host1})
    logging.info("Result1: {}".format(result1.text))
    logging.info("Status1: {}".format(result1.status_code))
    logging.info("Result2: {}".format(result2.text))
    logging.info("Status2: {}".format(result2.status_code))
    assert (
        result1.status_code == 200
    ), f"Expected a 200 response, got {result1.status_code}"
    assert (
        result2.status_code == 200
    ), f"Expected a 200 response, got {result2.status_code}"
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
                    f"{item.metadata.name} not yet ready, waiting for {wait_for_seconds}"
                )
                continue

            for status_container in item.status.container_statuses:
                if not status_container.ready:
                    all_running = False
                    break

        if all_running:
            break
        else:
            ret = v1.list_namespaced_pod(
                test_namespace, label_selector="app=" + service_name
            )
    logging.info("Pod Ready")


def test_cluster(test_namespace):
    wait_for_pod(test_namespace, "nginx1")
    wait_for_pod(test_namespace, "nginx2")
    write_to_volume("nginx1", test_namespace)
    curl_service_with_shared_volume(
        "nginx1", "nginx2", test_namespace
    )  # this is the actual test
