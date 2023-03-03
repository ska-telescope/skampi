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

from assertpy import assert_that
from pytest_bdd import scenario, given, when, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from integration.sdp.vis_receive_utils import (
    pvc_exists,
    wait_for_pod,
    check_data_present,
    wait_for_predicate,
    deploy_sender,
    wait_for_obs_state,
    compare_data,
    POD_CONTAINER,
)
from resources.models.mvp_model.states import ObsState
from .. import conftest

from ska_ser_skallop.mvp_management.subarray_scanning import scanning_subarray

pytest_plugins = ["unit.test_cluster_k8s"]

LOG = logging.getLogger(__name__)

NAMESPACE = os.environ.get("KUBE_NAMESPACE")
NAMESPACE_SDP = os.environ.get("KUBE_NAMESPACE_SDP")
PVC_NAME = os.environ.get("SDP_DATA_PVC_NAME", "shared")


@pytest.mark.skalow
@pytest.mark.sdp
@scenario(
    "features/sdp_visibility_receive.feature", "Execute visibility receive script for a single scan"
)
def test_visibility_receive_in_low(assign_resources_test_exec_settings):
    """."""


@pytest.fixture(name="update_sut_settings")
def fxt_update_sut_settings_vis_rec(sut_settings: conftest.SutTestSettings):
    tel = names.TEL()
    if tel.skalow:
        sut_settings.nr_of_subarrays = 1
    sut_settings.test_case = "vis-receive"


@given("the volumes are created and the data is copied")
def local_volume(k8s_element_manager, fxt_k8s_cluster):
    """
    Check if the local volumes are created and data is copied.

    :param context: context for the tests
    :param k8s_element_manager: Kubernetes element manager
    """
    receive_pod = "sdp-receive-data"
    sender_pod = "sdp-sender-data"
    data_container = POD_CONTAINER

    LOG.info("Check for existing PVC")
    assert pvc_exists(PVC_NAME, NAMESPACE_SDP), f"PVC in {NAMESPACE_SDP} doesn't exist"
    assert pvc_exists(PVC_NAME, NAMESPACE), f"PVC in {NAMESPACE} doesn't exist"

    LOG.info("Create Pod for receiver and sender")
    k8s_element_manager.create_pod(receive_pod, NAMESPACE_SDP, PVC_NAME)
    k8s_element_manager.create_pod(sender_pod, NAMESPACE, PVC_NAME)

    # Wait for pods
    assert wait_for_pod(receive_pod, NAMESPACE_SDP, "Running", timeout=300)
    assert wait_for_pod(sender_pod, NAMESPACE, "Running", timeout=300)

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

    wait_for_predicate(
        _wait_for_receive_data, "MS data is not present in volume.", timeout=100
    )
    wait_for_predicate(
        _wait_for_sender_data, "MS data is not present in volume.", timeout=100
    )

    LOG.info("PVCs and pods created, and data copied successfully")


# use given from sdp/conftest.py
# @given("an SDP subarray in READY state")


@pytest.fixture()
def check_rec_adds(
    configured_subarray
):
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(
        tel.sdp.subarray(configured_subarray.id)
    )

    receive_addresses = json.loads(
        sdp_subarray.read_attribute("receiveAddresses").value
    )
    host = receive_addresses["target:a"]["vis0"]["host"][0][1]
    receiver_pod_name = host.split(".")[0]

    # Check if the receiver is running
    LOG.info("Waiting for receive pod to be 'Running'")
    assert wait_for_pod(
        receiver_pod_name,
        NAMESPACE_SDP,
        "Running",
        600,
        pod_condition="Ready",
    )

    LOG.info("Receive pod is running. Checking receive addresses.")
    # Get the DNS hostname from receive addresses attribute
    receive_addresses_expected = (
        f"{receiver_pod_name}.receive.{NAMESPACE_SDP}." "svc.cluster.local"
    )

    assert host == receive_addresses_expected


@when("SDP is commanded to capture data from a scan")
def run_scan(
    check_rec_adds,
    k8s_element_manager,
    configured_subarray,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    Run a sequence of scans.

    :param context: context for the tests
    :param subarray_device: SDP subarray device client
    :param subarray_scan: scan fixture
    :param k8s_element_manager: Kubernetes element manager

    """
    LOG.info("Running scan step.")
    tel = names.TEL()
    subarray_id = configured_subarray.id
    receptors = configured_subarray.receptors
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(subarray_id))

    obs_state = sdp_subarray.read_attribute("obsState").value
    assert_that(obs_state).is_equal_to(ObsState.READY)

    receive_addresses = json.loads(
        sdp_subarray.read_attribute("receiveAddresses").value
    )
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
            # this gives 2 instead of 1, because (I think) when I call this here
            # this is the second time it's called, so it increases the number by 1
            # scan_id = entry_point.observation.get_scan_id(backwards=True)["id"]
            scan_id = 1

            obs_state = sdp_subarray.read_attribute("obsstate").value
            assert_that(obs_state).is_equal_to(ObsState.SCANNING)
            LOG.info("Scanning")
            deploy_sender(host, scan_id, k8s_element_manager)
        except Exception as err:
            LOG.exception("Scan step failed")

    if err:
        # raise error after Subarray went back to READY
        # so that ReleaseAllResource can work
        raise err


@pytest.fixture
def dataproduct_directory(entry_point):
    """
    The directory where output files will be written.

    :param assign_resources_config: AssignResources configuration
    """
    eb_id = entry_point.observation.execution_block.eb_id
    pb_id = entry_point.observation.processing_blocks[0].pb_id
    return f"/product/{eb_id}/ska-sdp/{pb_id}"


@then("the data received matches with the data sent")
def check_measurement_set(dataproduct_directory, k8s_element_manager, sut_settings):
    """
    Check the data received are same as the data sent.

    :param context: context for the tests
    :param dataproduct_directory: The directory where outputs are written

    """
    # Wait 10 seconds before checking the measurement.
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

    # try:
    result = compare_data(
        receive_pod,
        data_container,
        NAMESPACE_SDP,
        f"{dataproduct_directory}/output.scan-1.ms",
    )
    assert result.returncode == 0
    LOG.info("Data sent matches the data received")

