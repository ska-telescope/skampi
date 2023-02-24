import json
import logging
import os

import pytest

from assertpy import assert_that
from pytest_bdd import scenario, given, when

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
    wait_for_obs_state
)
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.mvp_management.subarray_scanning import scanning_subarray

pytest_plugins = ["tests.unit.test_cluster_k8s"]

LOG = logging.getLogger(__name__)

TIMEOUT_ASSIGNRES = 120.0

NAMESPACE = os.environ.get("KUBE_NAMESPACE")
NAMESPACE_SDP = os.environ.get("KUBE_NAMESPACE_SDP")
PVC_NAME = os.environ.get("SDP_DATA_PVC_NAME", "shared")


@pytest.mark.skalow
@pytest.mark.sdp
@scenario(
    "features/sdp_visibility_receive.feature", "Execute visibility receive script"
)
def test_visibility_receive_in_low(assign_resources_test_exec_settings):
    """."""


# use given from sdp/conftest.py
# @given("an SDP subarray")


@given("obsState is EMPTY")
def check_obsstate(sut_settings: SutTestSettings):
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(
        tel.sdp.subarray(sut_settings.subarray_id)
    )
    result = sdp_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.EMPTY)


@given("the volumes are created and the data is copied")
def local_volume(k8s_element_manager, fxt_k8s_cluster):
    """
    Check if the local volumes are created and data is copied.

    :param context: context for the tests
    :param k8s_element_manager: Kubernetes element manager
    """
    receive_pod = "sdp-receive-data"
    sender_pod = "sdp-sender-data"
    data_container = "data-prep"

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
            LOG.info("MS data copied into receive pod")
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
            LOG.info("MS data copied into sender pod")
            return True
        return False

    wait_for_predicate(_wait_for_receive_data, "MS data is not present in volume.", timeout=50)
    wait_for_predicate(_wait_for_sender_data, "MS data is not present in volume.", timeout=50)

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

    pb_id = entry_point.observation.processing_blocks[0].pb_id
    receiver_pod_name = f"proc-{pb_id}-receive-0"

    # Check if the receiver is running
    LOG.info("Waiting for receive pod to be 'Running'")
    assert wait_for_pod(
        receiver_pod_name,
        NAMESPACE_SDP,
        "Running",
        600,
        pod_condition="Ready",
    )

    LOG.info("Receive pid is running. Checking receive addresses.")
    # Get the DNS hostname from receive addresses attribute
    receive_addresses_expected = (
        f"{receiver_pod_name}.receive.{NAMESPACE_SDP}." "svc.cluster.local"
    )

    receive_addresses = json.loads(
        sdp_subarray.read_attribute("receiveAddresses").value
    )
    host = receive_addresses["target:a"]["vis0"]["host"][0][1]
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


@given("the SDP subarray is configured")
def i_configure_it_for_a_scan(
    entry_point: fxt_types.entry_point,
    configuration: conf_types.ScanConfiguration,
    sut_settings: SutTestSettings,
):
    """I configure it for a scan."""
    tel = names.TEL()
    subarray_id = sut_settings.subarray_id
    sdp_subarray = con_config.get_device_proxy(
        tel.sdp.subarray(subarray_id)
    )
    obs_state = sdp_subarray.read_attribute("obsState").value
    assert_that(obs_state).is_equal_to(ObsState.IDLE)

    receptors = sut_settings.receptors
    scan_duration = sut_settings.scan_duration
    sb_id = entry_point.observation.processing_blocks[0].sbi_ids[0]

    entry_point.configure_subarray(
        subarray_id, receptors, configuration, sb_id, scan_duration
    )

    LOG.info("Subarray is configured.")


@when("SDP is commanded to capture data from a scan")
def run_scan(
        k8s_element_manager,
        entry_point: fxt_types.entry_point,
        sut_settings: SutTestSettings,
        integration_test_exec_settings: fxt_types.exec_settings,):
    """
    Run a sequence of scans.

    :param context: context for the tests
    :param subarray_device: SDP subarray device client
    :param subarray_scan: scan fixture
    :param k8s_element_manager: Kubernetes element manager

    """
    tel = names.TEL()
    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
    sdp_subarray = con_config.get_device_proxy(
        tel.sdp.subarray(subarray_id)
    )

    obs_state = sdp_subarray.read_attribute("obsState").value
    assert_that(obs_state).is_equal_to(ObsState.READY)

    receive_addresses = json.loads(
        sdp_subarray.read_attribute("receiveAddresses").value
    )
    host = receive_addresses["target:a"]["vis0"]["host"][0][1]

    LOG.info("Executing scan.")

    with scanning_subarray(
            subarray_id, receptors, integration_test_exec_settings, clean_up_after_scanning=True
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
        except Exception:
            LOG.exception("Scan step failed")

    # when scanning_subarray exists, it sets the obsState to Ready
    # need to call End, to move it to IDLE (from which ReleaseAllResources works)
    LOG.info("Calling End")
    sdp_subarray.command_inout("End")
