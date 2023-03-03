"""
SDP Visibility Receive processing script test.

This is an end-to-end SDP test, with each step being
implemented separately, i.e. the steps to perform the following
steps are implemnted explicitly:
- AssignResources
- Configure
- Scan

It is using underlying skampi and skallop code as much as possible.
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
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from integration.conftest import SutTestSettings
from integration.sdp.vis_receive_utils import (
    pvc_exists,
    wait_for_pod,
    check_data_present,
    wait_for_predicate,
    deploy_sender,
    wait_for_obs_state,
    compare_data,
    POD_CONTAINER
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
    "features/sdp_visibility_receive.feature", "Execute visibility receive script for a single scan (full)"
)
def test_visibility_receive_in_low(assign_resources_test_exec_settings):
    """."""


@pytest.fixture(name="update_sut_settings")
def fxt_update_sut_settings_vis_rec(sut_settings: conftest.SutTestSettings):
    tel = names.TEL()
    if tel.skalow:
        sut_settings.nr_of_subarrays = 1
    sut_settings.test_case = "vis-receive"


# use given from sdp/conftest.py
# @given("an SDP subarray")


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


# @given("I deploy the visibility receive script") same as AssignResources in conftest.py


@pytest.fixture(scope="function")
def check_rec_adds(
    entry_point: fxt_types.entry_point,
    sut_settings: SutTestSettings,
):
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(
        tel.sdp.subarray(sut_settings.subarray_id)
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


@pytest.fixture(name="configuration")
def config(
    check_rec_adds,
    set_up_subarray_log_checking_for_sdp,
    sdp_base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: SutTestSettings,
) -> conf_types.ScanConfiguration:
    """an SDP subarray in IDLE state."""
    subarray_allocation_spec.receptors = sut_settings.receptors
    subarray_allocation_spec.subarray_id = sut_settings.subarray_id
    # will use default composition for the allocated subarray
    # subarray_allocation_spec.composition
    return sdp_base_configuration


@pytest.fixture(name="configure_sdp")
def configure_sdp_fixt(
    entry_point: fxt_types.entry_point,
    configuration: conf_types.ScanConfiguration,
    sut_settings: SutTestSettings,
):
    """I configure it for a scan."""
    tel = names.TEL()
    subarray_id = sut_settings.subarray_id
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(subarray_id))
    obs_state = sdp_subarray.read_attribute("obsState").value
    assert_that(obs_state).is_equal_to(ObsState.IDLE)

    receptors = sut_settings.receptors
    scan_duration = sut_settings.scan_duration
    sb_id = entry_point.observation.processing_blocks[0].sbi_ids[0]

    entry_point.configure_subarray(
        subarray_id, receptors, configuration, sb_id, scan_duration
    )

    LOG.info("Subarray is configured.")

    yield

    # need to call End, to move it to IDLE (from which ReleaseAllResources works)
    LOG.info("Calling End")
    sdp_subarray.command_inout("End")
    # wait_for_obs_state(sdp_subarray, "IDLE", timeout=30)


@given("the SDP subarray is configured")
def i_configure_it_for_a_scan(configure_sdp):
    """Configure via fixture"""


@when("SDP is commanded to capture data from a scan")
def run_scan(
    k8s_element_manager,
    entry_point: fxt_types.entry_point,
    sut_settings: SutTestSettings,
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
    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
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

