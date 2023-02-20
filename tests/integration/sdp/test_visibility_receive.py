import logging
import os

import pytest

from assertpy import assert_that
from pytest_bdd import scenario, given, when

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from tests.integration.conftest import SutTestSettings
from tests.integration.sdp.vis_receive_utils import (
    pvc_exists,
    wait_for_pod,
    check_data_present,
    wait_for_predicate
)
from tests.resources.models.mvp_model.states import ObsState

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
    assert wait_for_pod(
        receiver_pod_name,
        NAMESPACE_SDP,
        "Running",
        600,
        pod_condition="Ready",
    )

    yield

    # for now this will make sure that the PB is finished
    # and receiver removed at the end of the test
    LOG.info("Calling End")
    sdp_subarray.command_inout("End")

    # # Get the DNS hostname from receive addresses attribute
    # receive_addresses_expected = (
    #     f"{receiver_pod_name}.receive.{NAMESPACE_SDP}." "svc.cluster.local"
    # )
    #
    # # TODO: got this far; receive_addresses don't work
    # receive_addresses = json.loads(
    #     sdp_subarray.read_attribute("receiveAddresses").value
    # )
    # logging.warning("recadr: ", receive_addresses)
    # host = receive_addresses["science"]["vis0"]["host"][0][1]
    # assert host == receive_addresses_expected


@when("SDP is commanded to capture data from 2 successive scans")
def run_scan(check_rec_adds):
    pass
