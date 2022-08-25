"""
Verify that dish lmc mode transitions

(R.LMC.SM.12, R.LMC.SM.1, R.LMC.SM.2, R.LMC.SM.6
R.LMC.SM.22 except MAINTENANCE, R.LMC.SM.13, R.LMC.SM.15, R.LMC.SM.16)
"""
import logging

import pytest
import tango
from integration.dish.dish_enums import DishMode
from integration.dish.utils import retrieve_attr_value
from pytest_bdd import given, scenario, then, when
from pytest_bdd.parsers import parse
from tango import DevState

LOGGER = logging.getLogger(__name__)


@pytest.mark.skamid
@scenario(
    "dish_leaf_node_set_standby_fp.feature",
    "Test dishleafnode SetStandbyFPMode command",
)
def test_set_standby_fp_mode():
    # pylint: disable=missing-function-docstring
    pass


@given(parse("dish_manager dishMode reports {dish_mode}"))
def check_dish_manager_dish_mode(dish_mode, dish_manager, modes_helper):
    # pylint: disable=missing-function-docstring
    modes_helper.ensure_dish_manager_mode(dish_mode)
    current_dish_mode = retrieve_attr_value(dish_manager, "dishMode")
    LOGGER.info(f"{dish_manager} dishMode: {current_dish_mode}")

@when("I issue SetStandbyFPMode on dish_leaf_node")
def issue_set_standby_fp_mode(dish_leaf_node, dish_manager, dish_manager_event_store):
    # pylint: disable=missing-function-docstring
    attrs_subscr = ["dishMode", "State"]
    for attr in attrs_subscr:
        dish_manager.subscribe_event(
            attr,
            tango.EventType.CHANGE_EVENT,
            dish_manager_event_store,
        )
    dish_manager_event_store.clear_queue()

    # request SetStandbyFPMode cmd
    dish_leaf_node.command_inout("SetStandbyFPMode")


@then("dish_manager dishMode and state should report STANDBY_FP and STANDBY")
def check_dish_mode_and_state(
    dish_manager, dish_manager_event_store,
):
    # pylint: disable=missing-function-docstring
    # check that the events for requested dishMode are received
    attr, val = 0, 1
    dish_evts = dish_manager_event_store.get_queue_values(timeout=60)
    LOGGER.info(dish_evts)

    # DISHMODE
    dish_mode_evts = [
        evt[val]
        for evt in dish_evts
        if evt[attr] == "dishmode"
    ]
    assert DishMode["STANDBY_FP"] in dish_mode_evts
   
    current_dish_mode = retrieve_attr_value(dish_manager, "dishMode")
    LOGGER.info(
        f"{dish_manager} dishMode: {current_dish_mode}, "
    )


@then("dish_structure operatingMode and powerState should report STANDBY_FP and FULL_POWER")
def check_ds_operating_mode_and_power_state(dish_structure):
    # pylint: disable=missing-function-docstring
    current_operating_mode = retrieve_attr_value(
        dish_structure, "operatingMode"
    )
    current_power_state = retrieve_attr_value(
        dish_structure, "powerState"
    )
    assert current_operating_mode == "STANDBY_FP"
    assert current_power_state == "FULL_POWER"
    LOGGER.info(
        f"{dish_structure} operatingMode: {current_operating_mode}"
        f", powerState: {current_power_state}"
    )


@then("spf operatingMode and powerState should report OPERATE and FULL_POWER")
def check_spf_operating_mode_and_power_state(
    spf,
):
    # pylint: disable=missing-function-docstring
    current_operating_mode = retrieve_attr_value(spf, "operatingMode")
    current_power_state = retrieve_attr_value(spf, "powerState")
    assert current_operating_mode == "OPERATE"
    assert current_power_state == "FULL_POWER"
    LOGGER.info(
        f"{spf} operatingMode: {current_operating_mode},"
        f"powerState: {current_power_state}"
    )


@then("spfrx operatingMode should report DATA_CAPTURE")
def check_spfrx_operating_mode(spfrx):
    # pylint: disable=missing-function-docstring
    current_operating_mode = retrieve_attr_value(spfrx, "operatingMode")
    assert current_operating_mode == "DATA_CAPTURE"
    LOGGER.info(f"{spfrx} operatingMode: {current_operating_mode}")
