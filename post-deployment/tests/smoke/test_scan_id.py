"""
The scan used in this test has been adapted from:
https://gitlab.com/ska-telescope/observation-execution-tool/-/blob/master/scripts/notebooks/sb_observing_test.ipynb

The configuration data in ../../resources/test_data/scan_id_test has been copied from:
https://gitlab.com/ska-telescope/observation-execution-tool/-/tree/master/scripts/data
"""

import logging
import os

from datetime import timedelta
from pathlib import Path

import tango
import pytest

from oet.domain import SKAMid
from oet.domain import SubArray
from oet import observingtasks
from oet.command import SCAN_ID_GENERATOR
from ska.pdm.entities.sb_definition import SBDefinition
from ska.cdm.messages.subarray_node.configure import ConfigureRequest
from ska.cdm.schemas import CODEC as cdm_CODEC
from ska.pdm.entities.field_configuration import Target
from ska.pdm.schemas import CODEC as pdm_CODEC
from ska.cdm.messages.subarray_node.configure.core import (
    ReceiverBand as cdm_ReceiverBand,
)
from resources.test_support.helpers import resource, watch
from resources.test_support.controls import take_subarray
from skuid.client import SkuidClient


LOGGER = logging.getLogger(__name__)

KUBE_NAMESPACE = os.environ.get("KUBE_NAMESPACE", "integration")
HELM_RELEASE = os.environ.get("HELM_RELEASE", "test")
SKUID_URL = f"skuid-skuid-{KUBE_NAMESPACE}-{HELM_RELEASE}.{KUBE_NAMESPACE}.svc.cluster.local:9870"


TEST_DATA_PATH = Path.joinpath(
    Path(__file__).parents[2], "resources", "test_data", "scan_id_test"
)
ALLOCATE_FILE = Path.joinpath(TEST_DATA_PATH, "example_allocate.json")
SB_FILE = Path.joinpath(TEST_DATA_PATH, "example_sb.json")
CONFIG_FILE = Path.joinpath(TEST_DATA_PATH, "example_configure.json")


@pytest.fixture(scope="module")
def add_teardown(request, autouse=True):
    """
    Add a finalizer to ensure we always put the subarray back in a defined
    state regardless of test outcome.
    """

    def release():
        if resource("ska_mid/tm_subarray_node/1").get("obsState") == "IDLE":
            SubArray(1).deallocate()
        if resource("ska_mid/tm_subarray_node/1").get("obsState") == "READY":
            SubArray(1).end_sb()
            SubArray(1).deallocate()
        if resource("ska_mid/tm_subarray_node/1").get("obsState") == "CONFIGURING":
            restart_subarray(1)
        take_subarray(1).and_release_all_resources()
        SKAMid().standby()
        LOGGER.info("Released all test resources")

    request.addfinalizer(release)


def get_next_scan_id_from_service():
    """Use the skuid service to retrieve a scan ID"""
    client = SkuidClient(SKUID_URL)
    return client.fetch_scan_id()


@pytest.mark.xfail
def test_oet_uses_skuid_service():
    """Ensure that the oet library uses the skuid service i.e RemoteScanIdGenerator
    """
    assert "RemoteScanIdGenerator" in str(SCAN_ID_GENERATOR)


@pytest.mark.xfail
@pytest.mark.timeout(360)
def test_scan_id():
    """Ensure that oet uses skuid when building a scan.
    """
    scan_id_before_scan = get_next_scan_id_from_service()
    LOGGER.info("Scan id before scan: %s", scan_id_before_scan)
    LOGGER.info("ska_mid/tm_subarray_node/1 state :%s", resource("ska_mid/tm_subarray_node/1").get("State"))

    # Make sure the state is `disabled` before running the scan
    subarray_resource = resource("ska_mid/tm_subarray_node/1")
    subarray_resource.assert_attribute("State").equals("DISABLE")

    subarray_watch = watch(subarray_resource).for_a_change_on("State")
    telescope = SKAMid()
    telescope.start_up()
    subarray_watch.wait_until_value_changed_to("OFF")

    # Set up the subarray
    subarray_id = 1
    subarray = SubArray(subarray_id)
    allocated = subarray.allocate_from_file(ALLOCATE_FILE)

    # Set up the SB
    sched_block: SBDefinition = pdm_CODEC.load_from_file(SBDefinition, SB_FILE)

    # Set the configurations
    cdm_config: ConfigureRequest = cdm_CODEC.load_from_file(
        ConfigureRequest, CONFIG_FILE
    )
    scan_definitions = {
        scan_definition.id: scan_definition
        for scan_definition in sched_block.scan_definitions
    }
    field_configurations = {
        field_configuration.id: field_configuration
        for field_configuration in sched_block.field_configurations
    }
    dish_configurations = {
        dish_configuration.id: dish_configuration
        for dish_configuration in sched_block.dish_configurations
    }
    scan_definition_id = sched_block.scan_sequence[0]

    scan_definition = scan_definitions[scan_definition_id]

    field_configuration_id = scan_definition.field_configuration_id
    field_configuration = field_configurations[field_configuration_id]
    sb_scan_duration = scan_definition.scan_duration
    cdm_config.tmc.scan_duration = timedelta(seconds=sb_scan_duration)
    targets = field_configuration.targets
    target: Target = targets[0]
    cdm_config.pointing.target.coord = target.coord
    pdm_rx = None
    dish_configuration = dish_configurations[scan_definition.dish_configuration_id]
    pdm_rx = dish_configuration.receiver_band
    cdm_config.dish.receiver_band = cdm_ReceiverBand(pdm_rx.value)
    observingtasks.configure_from_cdm(subarray_id, cdm_config)

    # Do the scan
    subarray.scan()

    scan_id_after_scan = get_next_scan_id_from_service()

    # expected_scan_id_used should be read as an attribute from a device
    expected_scan_id_used = scan_id_before_scan + 1
    LOGGER.info("Scan id expected: %s", expected_scan_id_used)
    LOGGER.info("Scan id after scan: %s ", scan_id_after_scan)

    assert scan_id_after_scan > expected_scan_id_used > scan_id_before_scan
