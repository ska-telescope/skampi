import logging

import pytest
import tango
from integration.dish.dish_enums import DishMode
from integration.dish.utils import retrieve_attr_value
from pytest_bdd import given, scenario, then, when
from pytest_bdd.parsers import parse

LOGGER = logging.getLogger(__name__)


@pytest.mark.xfail(reason="DishLeafNode command Configure not yet implemented!")
@pytest.mark.skamid
@scenario(
    "dish_leaf_node_set_operate_mode.feature",
    "Test dishleafnode SetOperateMode command",
)
def test_set_operate_mode():
    # pylint: disable=missing-function-docstring
    pass


@given(parse("dish_manager dishMode reports {dish_mode}"))
def check_dish_manager_dish_mode(dish_mode, dish_manager, modes_helper):
    # pylint: disable=missing-function-docstring
    modes_helper.ensure_dish_manager_mode(dish_mode)
    current_dish_mode = retrieve_attr_value(dish_manager, "dishMode")
    LOGGER.info(f"{dish_manager} dishMode: {current_dish_mode}")


@given("dish_manager configuredBand reports B2")
def check_dish_manager_configured_band(dish_manager):
    configured_band = retrieve_attr_value(dish_manager, "configuredBand")
    assert configured_band == "B2"

@when("I issue SetOperateMode command on dish_leaf_node")
def set_operate_mode(dish_leaf_node, dish_manager, dish_manager_event_store):
    # pylint: disable=missing-function-docstring
    dish_manager.subscribe_event(
        "dishMode",
        tango.EventType.CHANGE_EVENT,
        dish_manager_event_store,
    )

    dish_leaf_node.SetOperateMode()
    LOGGER.info("DishLeafNode requested to set operate mode on dish")


@then("dish_manager dishMode should report OPERATE")
def check_dish_manager_dish_mode(dish_manager, dish_manager_event_store):
    # pylint: disable=missing-function-docstring
    dish_manager_event_store.wait_for_value(DishMode["OPERATE"], timeout=60)
    current_dish_mode = retrieve_attr_value(dish_manager, "dishMode")
    LOGGER.info(f"{dish_manager} dishMode: {current_dish_mode}")
