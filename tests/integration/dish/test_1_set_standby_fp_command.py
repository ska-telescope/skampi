"""
Verify that dish lmc mode transitions

(R.LMC.SM.12, R.LMC.SM.1, R.LMC.SM.2, R.LMC.SM.6
R.LMC.SM.22 except MAINTENANCE, R.LMC.SM.13, R.LMC.SM.15, R.LMC.SM.16)
"""
import logging
import time

import pytest
from integration.dish.utils import (
    retrieve_attr_value,
    wait_for_change_on_resource,
)
from pytest_bdd import scenario, then, when
from pytest_bdd.parsers import parse

LOGGER = logging.getLogger(__name__)


@pytest.mark.skamid
@scenario(
    "dish_leaf_node_set_standby_fp.feature",
    "Test dishleafnode SetStandbyFPMode command",
)
def test_set_standby_fp_mode():
    # pylint: disable=missing-function-docstring
    pass


@when(
    parse("I issue SetStandbyFPMode on dish_leaf_node"),
    target_fixture="desired_dish_mode",
)
def desired_dish_mode(
    dish_leaf_node_device_name, dish_manager_device_name, devices_under_test
):
    # pylint: disable=missing-function-docstring
    cmd_modes_map = {
        "SetStandbyLPMode": "STANDBY_LP",
        "SetStandbyFPMode": "STANDBY_FP",
        "SetOperateMode": "OPERATE",
        "SetStowMode": "STOW",
    }
    desired_dish_mode = cmd_modes_map["SetStandbyFPMode"]
    dish_leaf_node_proxy = devices_under_test[dish_leaf_node_device_name]
    dish_leaf_node_proxy.command_inout("SetStandbyFPMode")
    wait_for_change_on_resource(
        devices_under_test[dish_manager_device_name], "dishMode", "STANDBY_FP"
    )
    return desired_dish_mode


@then(
    parse(
        "dish_manager dishMode and state should report"
        " desired_dish_mode and STANDBY"
    )
)
def check_dish_mode_and_state(
    desired_dish_mode, dish_manager_device_name, devices_under_test
):
    # pylint: disable=missing-function-docstring
    dish_master_proxy = devices_under_test[dish_manager_device_name]
    current_dish_mode = retrieve_attr_value(dish_master_proxy, "dishMode")
    current_dish_state = retrieve_attr_value(dish_master_proxy, "State")
    assert current_dish_mode == desired_dish_mode
    assert current_dish_state == "STANDBY"
    LOGGER.info(
        f"{dish_master_proxy} dishMode: {current_dish_mode}, "
        f"State: {current_dish_state}"
    )


@then(
    parse(
        "dish_structure operatingMode and powerState should "
        "report STANDBY_FP and FULL_POWER"
    )
)
def check_ds_operating_mode_and_power_state(
    dish_structure_device_name, devices_under_test
):
    # pylint: disable=missing-function-docstring
    dish_structure_proxy = devices_under_test[dish_structure_device_name]
    current_operating_mode = retrieve_attr_value(
        dish_structure_proxy, "operatingMode"
    )
    current_power_state = retrieve_attr_value(
        dish_structure_proxy, "powerState"
    )
    assert current_operating_mode == "STANDBY_FP"
    assert current_power_state == "FULL_POWER"
    LOGGER.info(
        f"{dish_structure_proxy} operatingMode: {current_operating_mode}"
        f", powerState: {current_power_state}"
    )


@then(
    parse(
        "spf operatingMode and powerState should report "
        "OPERATE and FULL_POWER"
    )
)
def check_spf_operating_mode_and_power_state(
    spf_device_name, devices_under_test
):
    # pylint: disable=missing-function-docstring
    spf_proxy = devices_under_test[spf_device_name]
    current_operating_mode = retrieve_attr_value(spf_proxy, "operatingMode")
    current_power_state = retrieve_attr_value(spf_proxy, "powerState")
    assert current_operating_mode == "OPERATE"
    assert current_power_state == "FULL_POWER"
    LOGGER.info(
        f"{spf_proxy} operatingMode: {current_operating_mode},"
        f"powerState: {current_power_state}"
    )


@then(parse("spfrx operatingMode should report DATA_CAPTURE"))
def check_spfrx_operating_mode(spfrx_device_name, devices_under_test):
    # pylint: disable=missing-function-docstring
    spfrx_proxy = devices_under_test[spfrx_device_name]
    current_operating_mode = retrieve_attr_value(spfrx_proxy, "operatingMode")
    assert current_operating_mode == "DATA_CAPTURE"
    LOGGER.info(f"{spfrx_proxy} operatingMode: {current_operating_mode}")
