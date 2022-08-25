import logging
import time
from datetime import datetime, timedelta

import pytest
import tango
import json
from integration.dish.dish_enums import DishMode
from integration.dish.utils import retrieve_attr_value
from pytest_bdd import given, scenario, then, when
from pytest_bdd.parsers import parse

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="module", name="event_subs")
def fixture_event_subs():
    # pylint: disable=missing-function-docstring
    return {"evt_id": None, "cb": None}


@pytest.mark.xfail(reason="DishLeafNode commands Configure and Track not yet implemented!")
@pytest.mark.skamid
@scenario(
    "dish_leaf_node_track.feature", "Test dishleafnode Track command"
)
def test_track():
    # pylint: disable=missing-function-docstring
    pass

@given(parse("dish_manager dishMode reports {dish_mode}"))
def check_dish_manager_dish_mode(dish_mode, dish_manager, modes_helper):
    # pylint: disable=missing-function-docstring
    modes_helper.ensure_dish_manager_mode(dish_mode)
    current_dish_mode = retrieve_attr_value(dish_manager, "dishMode")
    LOGGER.info(f"{dish_manager} dishMode: {current_dish_mode}")


@given(parse("dish_manager pointingState reports READY"))
def check_dish_manager_pointing_state(dish_mode, dish_manager, modes_helper):
    # pylint: disable=missing-function-docstring
    # modes_helper.ensure_dish_manager_mode(dish_mode)
    pointing_state = retrieve_attr_value(dish_manager, "pointingState")
    assert pointing_state == "READY"
    LOGGER.info(f"{dish_manager} pointingState: {pointing_state}")


@when("I issue Track on dish_leaf_node")
def issue_track_command(
    dish_leaf_node,
    dish_manager,
    dish_manager_event_store,
):
    # pylint: disable=missing-function-docstring
    # subscribe to change event for dishMode
    dish_manager.subscribe_event(
        "dishMode",
        tango.EventType.CHANGE_EVENT,
        dish_manager_event_store,
    )
    dish_manager_event_store.clear_queue()
    input = (
        '{"pointing": {"target":{"system":"ICRS","name":"Polaris Australis","RA":"21:08:47.92","dec":"-88:57:22.9"}},'
            '"dish":{"receiverBand":"2"}}'
    )
    dish_leaf_node.Track(input)
    # dish_manager.Track()
    LOGGER.info("DishLeafNode requested to track on dish")

@then("dish_manager dishMode should report OPERATE")
def check_dish_mode(dish_manager, dish_manager_event_store):
    # pylint: disable=missing-function-docstring
    current_dish_mode = retrieve_attr_value(dish_manager, "dishMode")
    assert current_dish_mode == "OPERATE"
    LOGGER.info(f"{dish_manager} dishMode: {current_dish_mode}")

@then("dish_structure operatingMode POINT")
def check_dish_structure_operating_mode(dish_structure):
    # pylint: disable=missing-function-docstring
    # wait_for_change_on_resource(dish_manager_proxy, "dishMode", "OPERATE")
    operating_mode = retrieve_attr_value(
        dish_structure, "operatingMode"
    )
    assert operating_mode == "POINT"
    LOGGER.info(f"{dish_structure} operatingMode: {operating_mode}")


@then("spf operatingMode should report OPERATE")
def check_spf_operating_mode(spf):
    # pylint: disable=missing-function-docstring
    operating_mode = retrieve_attr_value(
        spf, "operatingMode"
    )
    assert operating_mode == "OPERATE"
    LOGGER.info(f"{spf} operatingMode: {operating_mode}")


@then("spfrx operatingMode should report DATA_CAPTURE")
def check_spfrx_operating_mode(spfrx):
    # pylint: disable=missing-function-docstring
    operating_mode = retrieve_attr_value(
        spfrx, "operatingMode"
    )
    assert operating_mode == "DATA_CAPTURE"
    LOGGER.info(f"{spfrx} operatingMode: {operating_mode}")
