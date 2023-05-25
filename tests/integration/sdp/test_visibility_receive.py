"""
SDP Visibility Receive processing script test.

This version of the test doesn't implement AssignResources and
Configure separately, instead, it uses an starting point,
which already assumes that the subarray is READY to start a scan.

For this, we use the `configured_subarray` fixture, which
makes sure that AssignResources and Configure are executed
before the code reaches the steps implemented in this test.

It is still and end-to-end functionality test, but
the implementation is relying heavily on skampi and skallop
for the first two commands.
"""

import json
import logging
import os
import time

import pytest
import requests
from assertpy import assert_that
from integration.sdp.vis_receive_utils import (
    POD_CONTAINER,
    check_data_present,
    compare_data,
    deploy_cbf_emulator,
    pvc_exists,
    wait_for_pod,
    wait_for_predicate,
)
from pytest_bdd import given, scenario, then, when
from requests.models import Response
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_management.subarray_scanning import scanning_subarray

from .. import conftest
from .vis_receive_utils import K8sElementManager

pytest_plugins = ["unit.test_cluster_k8s"]

LOG = logging.getLogger(__name__)

INGRESS = os.environ.get("INGRESS_HOST")
NAMESPACE = os.environ.get("KUBE_NAMESPACE")
NAMESPACE_SDP = os.environ.get("KUBE_NAMESPACE_SDP")
PVC_NAME = os.environ.get("SDP_DATA_PVC_NAME", "shared")


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.visibility
@pytest.mark.skalow
@pytest.mark.sdp
@scenario(
    "features/sdp_visibility_receive.feature",
    "Execute visibility receive script for a single scan",
)
def test_visibility_receive_in_low(assign_resources_test_exec_settings):
    """
    SDP Visibility receive test.

    :param assign_resources_test_exec_settings: Object for assign_resources_test_exec_settings
    """


@pytest.fixture(name="update_sut_settings")
def fxt_update_sut_settings_vis_rec(sut_settings: conftest.SutTestSettings):
    """
    Update SUT settings. Specify that we're running the
    visibility receive test.

    :param sut_settings: the SUT test settings.
    """
    tel = names.TEL()
    if tel.skalow:
        sut_settings.nr_of_subarrays = 1
    sut_settings.test_case = "vis-receive"


@given("the test volumes are present and the test data are downloaded")
def local_volume(k8s_element_manager: K8sElementManager, fxt_k8s_cluster):
    """
    Check if the local volumes are present and the data
    have been successfully downloaded.

    :param k8s_element_manager: Kubernetes element manager
    :param fxt_k8s_cluster: fixture to use a KUBECONFIG file (if present),
                for performing k8s commands (see unit.test_cluster_k8s)
    """  # noqa: DAR401
    if NAMESPACE is None or NAMESPACE_SDP is None:
        raise ValueError("Env var KUBE_NAMESPACE or KUBE_NAMESPACE_SDP is not defined")

    receive_pod = "sdp-receive-data"
    sender_pod = "sdp-sender-data"
    data_container = POD_CONTAINER

    LOG.info("Check for existing PVC")
    assert pvc_exists(PVC_NAME, NAMESPACE_SDP), f"PVC in {NAMESPACE_SDP} doesn't exist"
    assert pvc_exists(PVC_NAME, NAMESPACE), f"PVC in {NAMESPACE} doesn't exist"

    LOG.info("Create Pod for receiver and sender")
    k8s_element_manager.create_pod(receive_pod, NAMESPACE_SDP, PVC_NAME)
    k8s_element_manager.create_pod(sender_pod, NAMESPACE, PVC_NAME)

    ms_file_mount_location = "/mnt/data/AA05LOW.ms/"

    # Check if the measurement set has been download into pods
    def _wait_for_receive_data():
        receiver_result = check_data_present(
            receive_pod,
            data_container,
            NAMESPACE_SDP,
            ms_file_mount_location,
        )
        if receiver_result.returncode == 0:
            LOG.info("MS data downloaded into receive pod")
            return True
        return False

    def _wait_for_sender_data():
        sender_result = check_data_present(
            sender_pod,
            data_container,
            NAMESPACE,
            ms_file_mount_location,
        )
        if sender_result.returncode == 0:
            LOG.info("MS data downloaded into sender pod")
            return True
        return False

    wait_for_predicate(_wait_for_receive_data, "MS data not present in volume.", timeout=100)()
    wait_for_predicate(_wait_for_sender_data, "MS data not present in volume.", timeout=100)()

    LOG.info("PVCs are present, pods created, and data downloaded successfully")


# use given from sdp/conftest.py
# @given("an SDP subarray in READY state")


@pytest.fixture
def check_rec_adds(configured_subarray: fxt_types.configured_subarray):
    """
    Wait for receive pod to be Running and check that the
    receive addresses have been updated correctly.

    :param configured_subarray: skallop configured_subarray fixture
    """
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(configured_subarray.id))

    receive_addresses = json.loads(sdp_subarray.read_attribute("receiveAddresses").value)
    # Get the DNS hostname from receive addresses attribute
    host = receive_addresses["target:a"]["vis0"]["host"][0][1]
    receiver_pod_name = host.split(".")[0]

    # Check if the receiver is running
    LOG.info("Waiting for receive pod to be 'Running'")
    assert wait_for_pod(
        receiver_pod_name,
        NAMESPACE_SDP,
        "Running",
        timeout=600,
        pod_condition="Ready",
    )

    LOG.info("Receive pod is running. Checking receive addresses.")
    receive_addresses_expected = f"{receiver_pod_name}.receive.{NAMESPACE_SDP}"

    assert host == receive_addresses_expected


@when("SDP is commanded to capture data from a scan")
def run_scan(
    check_rec_adds,
    k8s_element_manager: K8sElementManager,
    configured_subarray: fxt_types.configured_subarray,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    Run a scan.

    :param check_rec_adds: fixture to wait for Receiver to run and to
                check receive addresses are correctly set
    :param k8s_element_manager: Kubernetes element manager
    :param configured_subarray: skallop configured_subarray fixture
    :param integration_test_exec_settings: test specific execution settings
    """  # noqa: DAR401
    LOG.info("Running scan step.")
    tel = names.TEL()
    subarray_id = configured_subarray.id
    receptors = configured_subarray.receptors
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(subarray_id))

    obs_state = sdp_subarray.read_attribute("obsState").value
    assert_that(obs_state).is_equal_to(ObsState.READY)

    receive_addresses = json.loads(sdp_subarray.read_attribute("receiveAddresses").value)
    host = receive_addresses["target:a"]["vis0"]["host"][0][1]

    LOG.info("Executing scan.")

    err = None
    with scanning_subarray(
        subarray_id,
        receptors,
        integration_test_exec_settings,
        clean_up_after_scanning=True,
    ):
        try:
            scan_id = 1
            obs_state = sdp_subarray.read_attribute("obsstate").value
            assert_that(obs_state).is_equal_to(ObsState.SCANNING)
            LOG.info("Scanning")
            deploy_cbf_emulator(host, scan_id, k8s_element_manager)

        except Exception as err:
            err = err
            LOG.exception("Scan step failed")

    if err:
        # raise error after Subarray went back to READY
        # so that ReleaseAllResource can work
        raise err


@pytest.fixture
def dataproduct_directory(entry_point: fxt_types.entry_point):
    """
    The directory where output files will be written.

    :param entry_point: entry point to test
    :return: dataproduct directory
    """
    eb_id = entry_point.observation.execution_block.eb_id
    pb_id = entry_point.observation.processing_blocks[0].pb_id
    return f"/product/{eb_id}/ska-sdp/{pb_id}"


@then("the data received matches with the data sent")
def check_measurement_set(
    dataproduct_directory,
    k8s_element_manager: K8sElementManager,
    sut_settings: conftest.SutTestSettings,
):
    """
    Check the data received are same as the data sent.

    :param dataproduct_directory: The directory where outputs are written
    :param k8s_element_manager: Kubernetes element manager
    :param sut_settings: SUT settings fixture
    """
    # Wait 10 seconds before checking the measurement set.
    # This gives enough time for the receiver for finish writing the data.
    time.sleep(10)

    receive_pod = "sdp-receive-data"
    data_container = POD_CONTAINER

    # Add data product directory to k8s element manager for cleanup
    parse_dir = dataproduct_directory.index("ska-sdp")
    data_eb_dir = dataproduct_directory[:parse_dir]
    k8s_element_manager.output_directory(
        data_eb_dir,
        receive_pod,
        data_container,
        NAMESPACE_SDP,
    )

    result = compare_data(
        receive_pod,
        data_container,
        NAMESPACE_SDP,
        f"{dataproduct_directory}/output.scan-1.ms",
    )
    assert result.returncode == 0
    LOG.info("Data sent matches the data received")


@then("a list of data products can be retrieved")
def retrieveDataProducts() -> Response:
    """
    Check the data products are available
    """

    response = requests.get(f"http://{INGRESS}/{NAMESPACE}/dataproduct/api/dataproductlist")
    assert response.status_code == 200


@then("an available data product can be downloaded")
def downloadDataProduct():
    """
    Check the data products can be downloaded.
    """

    with open("tests/test-download-data-product.json", "r") as json_file:
        data = json.load(json_file)

    response = requests.post(f"http://{INGRESS}/{NAMESPACE}/dataproduct/api/download", data)
    assert response.status_code == 200

    LOG.info("Data product downloaded")
