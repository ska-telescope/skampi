# third party dependencies
import logging
import functools
import os
from sys import exec_prefix
from kubernetes.stream import stream
from contextlib import contextmanager
from kubernetes import config, client
from collections import namedtuple
import pytest
from tango import DeviceProxy

# direct dependencies
from resources.test_support.helpers import resource
from resources.test_support.persistance_helping import (
    update_resource_config_file,
    load_config_from_file,
    update_scan_config_file,
)

# MVP code
from ska.scripting.domain import Telescope, SubArray

LOGGER = logging.getLogger(__name__)


## pytest fixtures
ENV_VARS = ["HELM_RELEASE", "KUBE_NAMESPACE", "TANGO_HOST"]
RunContext = namedtuple("RunContext", ENV_VARS)


@pytest.fixture(scope="session")
def run_context():
    # list of required environment vars
    values = list()

    for var in ENV_VARS:
        assert os.environ.get(var)  # all ENV_VARS must have values set
        values.append(os.environ.get(var))

    return RunContext(*values)


class K8_env:
    """
    An object to help with managing the k8 context in order to
    ensure tests are not effected by dirty environments
    """

    def __init__(self, run_context: RunContext) -> None:
        try:
            config.load_incluster_config()
        except config.ConfigException:
            # if Config exception try loading it from config file
            # assumes this is therefore run from a bash shell with different user than root
            _, active_context = config.list_kube_config_contexts()
            config.load_kube_config(context=active_context["name"])
        self.v1 = client.CoreV1Api()
        self.extensions_v1_beta1 = client.ExtensionsV1beta1Api()
        self.env = run_context
        self.clean_config_etcd()

    def _lookup_by(self, item, key: str, value: str) -> bool:
        if item.metadata.labels is not None:
            return item.metadata.labels.get(key) == value
        else:
            return False

    def clean_config_etcd(self) -> None:
        exec_command = ["sh", "-c", 'ETCDCTL_API=3 etcdctl del --prefix ""']
        app_name = "etcd"
        namespace = self.env.KUBE_NAMESPACE
        logging.debug(f"lookging for sdp in namespace:{namespace}")
        try:
            pods = self.v1.list_namespaced_pod(namespace).items
        except Exception as e:
            logging.warning(e)
            raise e
        assert (
            pods is not None
        ), f"error in cleaning config db: no pods installed in namespace {namespace} not found"
        pod = [p.metadata.name for p in pods if self._lookup_by(p, "app", app_name)]
        assert (
            len(pod) > 0
        ), f"error in cleaning config db: pod labeled as {app_name} not found"
        assert (
            len(pod) < 2
        ), f"error in cleaning config db: duplicate pods labeled as {app_name} found"
        pod = pod[0]
        resp = stream(
            self.v1.connect_get_namespaced_pod_exec,
            pod,
            namespace,
            command=exec_command,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )
        logging.info(f"cleaning configdb:{resp}")


@pytest.fixture(scope="session", autouse=True)
def k8(run_context) -> None:
    """
    An fixture to help with managing the k8 context in order to
    ensure tests are not effected by dirty environments
    """
    yield K8_env(run_context)
