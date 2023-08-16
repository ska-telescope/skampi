import json
import logging

import pytest
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from tests.resources.models.obsconfig.config import Observation

from ...conftest import SutTestSettings

logger = logging.getLogger(__name__)


@pytest.mark.sdpln
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@scenario(
    "features/sdpln_assign_resources_error.feature",
    "Error propagation",
)
def test_error_propogation_from_tmc_subarray_in_low():
    """Release resources from tmc subarrays in mid."""


@given("a TMC SDP subarray Leaf Node", target_fixture="composition")
def an_telescope_subarray(
    set_sdp_ln_error_entry_point,
    base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """
    an telescope subarray.

    :param set_sdp_ln_error_entry_point: To set up entry point for tmc leafnode.
    :param base_composition : An object for base composition
    :return: base composition
    """
    return base_composition


@when("I assign resources for the second time with same eb_id")
def i_assign_resources_to_sdpsln(
    sut_settings: SutTestSettings,
    entry_point: fxt_types.entry_point,
):
    """
    I assign resources to it
    :param sut_settings: settings for system under test
    :param entry_point: entry point fixture
    """
    global unique_id

    tel = names.TEL()
    observation = Observation()
    subarray_name = tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node
    subarray = con_config.get_device_proxy(subarray_name)
    config = observation.generate_sdp_assign_resources_config().as_json
    error_json = json.loads(config)
    error_json["execution_block"]["eb_id"] = "eb-mvp01-20230809-49670"
    new_config = json.dumps(error_json)

    result_code, unique_id = subarray.command_inout("AssignResources", new_config)
    logger.info(f"Result code for second assign resources {result_code}")


@then("the lrcr event throws error")
def lrcr_event(
    sut_settings: SutTestSettings,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    tel = names.TEL()
    subarray_name = tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node

    context_monitoring.re_init_builder()

    context_monitoring.wait_for(subarray_name).for_attribute(
        "sdpSubarrayObsState"
    ).to_become_equal_to("EMPTY", ignore_first=False, settings=integration_test_exec_settings)

    context_monitoring.wait_for(subarray_name).for_attribute(
        "longRunningCommandResult"
    ).to_become_equal_to(
        [
            f"('{unique_id[0]}', 'Exception occured on device: ska_low/tm_subarray_node/1: Exception occurred on the following devices:\nska_low/tm_leaf_node/csp_subarray01: [2, \"Task queued\"]\nska_low/tm_leaf_node/sdp_subarray01: Execution block eb-mvp01-20230809-49670 already exists\n')"
        ],
        settings=integration_test_exec_settings,
    )
