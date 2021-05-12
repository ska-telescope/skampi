import os
import pytest
import logging

from tango import DeviceProxy
from collections import namedtuple
from kubernetes import config, client

## shared fixtures
from resources.test_support.fixtures import run_context
from skallop.mvp_fixtures.subarray_composition import (
    fxt_allocated_subarray,
    fxt_allocate_subarray_settings,
    fxt_allocating_subarray,
    fxt_sb_config,
)
from skallop.mvp_fixtures.subarray_configuration import (
    fxt_configured_subarray,
    fxt_configure_subarray_settings,
    fxt_configuring_subarray,
)
from skallop.mvp_fixtures.telescope import (
    fxt_fixed_telescope,
    fxt_running_telescope,
    fxt_running_telescope_settings,
)
from skallop.mvp_fixtures.env_handling import (
    fxt_factory,
    fxt_inject_factory,
    fxt_entry_point,
    fxt_exec_env,
)

"""
RunContext is a metadata object to access values from the environment, 
i.e. data that is injected in by the Makefile. Useful if tests need to 
be aware of the k8s context they are running in, such as the HELM_RELEASE.

This will allow tests to resolve hostnames and other dynamic properties.

Example:

def test_something(run_context):
    HOSTNAME = 'some-pod-{}'.format(run_context.HELM_RELEASE)

"""


@pytest.fixture(scope="class")
def create_centralnode_proxy():
    centralnode_proxy = DeviceProxy("ska_mid/tm_central/central_node")
    return centralnode_proxy


@pytest.fixture(scope="class")
def create_subarray1_proxy():
    subarray1_proxy = DeviceProxy("ska_mid/tm_subarray_node/1")
    return subarray1_proxy


@pytest.fixture(scope="class")
def create_subarray2_proxy():
    subarray2_proxy = DeviceProxy("ska_mid/tm_subarray_node/2")
    return subarray2_proxy


@pytest.fixture(scope="class")
def create_subarray3_proxy():
    subarray3_proxy = DeviceProxy("ska_mid/tm_subarray_node/3")
    return subarray3_proxy


@pytest.fixture(scope="class")
def create_cspsubarray1_proxy():
    cspsubarray1_proxy = DeviceProxy("mid_csp/elt/subarray_01")
    return cspsubarray1_proxy


@pytest.fixture(scope="class")
def create_sdpsubarray1_proxy():
    sdpsubarray1_proxy = DeviceProxy("mid_sdp/elt/subarray_1")
    return sdpsubarray1_proxy


"""
Client that provides access to the Kubernetes API from the namespace the test 
runner pod is running in. 

https://github.com/kubernetes-client/python/blob/master/kubernetes/README.md

"""


@pytest.fixture(scope="session")
def k8s_api():
    config.load_incluster_config()

    KubernetesApi = namedtuple("KubernetesApi", ["v1", "extensions_v1_beta1"])

    return KubernetesApi(client.CoreV1Api(), client.ExtensionsV1beta1Api())
