import json
import logging

import pytest
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from resources.models.mvp_model.states import ObsState
from assertpy import assert_that

from tests.resources.models.tmc_model.entry_point import ASSIGN_RESOURCE_JSON_LOW

from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)



@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@scenario(
    "features/tmc_assign_skb.feature",
    "Verification of skb-185",
)
def test_error_propogation_from_tmc_subarray_in_low():
    """Assign resources from tmc subarrays in mid."""


# And I assign resources and release for the first time from the central node


@given("an TMC", target_fixture="composition")
def an_telescope_subarray(
    set_tmc_error_entry_point,
    base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """
    an telescope subarray.

    :param set_tmc_error_entry_point: To set up entry point for tmc.
    :param base_composition : An object for base composition
    :return: base composition
    """
    return base_composition


# And I assign resources and release for the first time from the central node


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
    central_node_name = tel.tm.central_node
    central_node = con_config.get_device_proxy(central_node_name, fast_load=True)
    error_json = ASSIGN_RESOURCE_JSON_LOW
    error_json["execution_block"]["eb_id"] = "eb-mvp01-20230809-49670"
    new_config = json.dumps(error_json)

    result_code, unique_id = central_node.command_inout("AssignResources", new_config)
    logger.info(f"Result code for second assign resources {result_code}")


@then("the tmc throws error and stays in obsState EMPTY")
def lrcr_event(
    sut_settings: SutTestSettings,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    tel = names.TEL()
    subarray_name = tel.tm.subarray(sut_settings.subarray_id)

    context_monitoring.re_init_builder()

    context_monitoring.wait_for(subarray_name).for_attribute("obsstate").to_become_equal_to(
        "RESOURCING", ignore_first=False, settings=integration_test_exec_settings
    )
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(sut_settings.subarray_id))
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.EMPTY)

    context_monitoring.wait_for(subarray_name).for_attribute(
        "longRunningCommandResult"
    ).to_become_equal_to(
        [
            f"('{unique_id[0]}', 'Execution block eb-mvp01-20230809-49670 already exists')",
            f"('{unique_id[0]}', '3')",
        ],
        settings=integration_test_exec_settings,
    )
