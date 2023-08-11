"""Test recovery of subarraynode stuck in resourcing"""
import json
import logging

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from tests.resources.models.tmc_model.entry_point import ASSIGN_RESOURCE_JSON_LOW

from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)

@pytest.mark.tmc
@pytest.mark.skalow
@pytest.mark.assign
@scenario(
    "features/recover_assign_in_resourcing.feature",
    "fix skb-185",
)
def test_recover_subarraynode_stuck_in_resourcing_tmc_in_low():
    """Test recovery of subarraynode stuck in resourcing"""


@given("a TMC", target_fixture="composition")
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


@given("resources are again assigned to the subarray with same eb_id")
def assign_resources_with_same_eb_id(
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


@given("sdp subarray throws error and stays in obsState EMPTY")
def check_long_running_command_result_error(
    sut_settings: SutTestSettings,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    tel = names.TEL()
    subarray_name = tel.tm.subarray(sut_settings.subarray_id)
    central_node_name = tel.tm.central_node

    context_monitoring.re_init_builder()

    context_monitoring.wait_for(subarray_name).for_attribute("obsstate").to_become_equal_to(
        "RESOURCING", ignore_first=False, settings=integration_test_exec_settings
    )
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(sut_settings.subarray_id))
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.EMPTY)

    context_monitoring.wait_for(central_node_name).for_attribute(
        "longRunningCommandResult"
    ).to_become_equal_to(
        [
            f"('{unique_id[0]}', 'Execution block eb-mvp01-20230809-49670 already exists')",
            f"('{unique_id[0]}', '3')",
        ],
        settings=integration_test_exec_settings,
    )


@given("the resources are assigned to csp subarray")
def check_csp_subarray__in_idle(sut_settings: SutTestSettings):
    tel = names.TEL()
    subarray_name = tel.csp.subarray(sut_settings.subarray_id)
    subarray = con_config.get_device_proxy(subarray_name)
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)


@given("the subarray node stucks in obsState RESOURCING")
def check_subarray_in_resourcing(sut_settings: SutTestSettings):
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)


@when("I release resources from the csp subarray")
def invoke_release_resources_on_csp_subarray(sut_settings: SutTestSettings):
    tel = names.TEL()
    subarray_name = tel.csp.subarray(sut_settings.subarray_id)
    subarray = con_config.get_device_proxy(subarray_name)
    subarray.set_timeout_millis(6000)
    _ = subarray.command_inout("ReleaseAllResources")


@then("csp subarray changes obsState to EMPTY")
def check_csp_suabrray_in_empty(
    sut_settings: SutTestSettings,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    tel = names.TEL()
    subarray_name = tel.csp.subarray(sut_settings.subarray_id)
    context_monitoring.re_init_builder()

    context_monitoring.wait_for(subarray_name).for_attribute("obsState").to_become_equal_to(
        "EMPTY", ignore_first=False, settings=integration_test_exec_settings
    )


@then("subarray node changes its obsState back to EMPTY")
def check_subarray_in_empty(
    sut_settings: SutTestSettings,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    tel = names.TEL()
    subarray_name = tel.tm.subarray(sut_settings.subarray_id)
    context_monitoring.re_init_builder()

    context_monitoring.wait_for(subarray_name).for_attribute("obsState").to_become_equal_to(
        "EMPTY", ignore_first=False, settings=integration_test_exec_settings
    )
