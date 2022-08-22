import logging
import time

import pytest
from integration.dish.utils import (
    retrieve_attr_value,
    wait_for_change_on_resource,
)
from pytest_bdd import scenario, then, when
from pytest_bdd.parsers import parse
from tango import CmdArgType

LOGGER = logging.getLogger(__name__)


@pytest.mark.skamid
@scenario(
    "dish_leaf_node_set_operate_mode.feature",
    "Test dishleafnode SetOperateMode command",
)
def test_set_operate_mode():
    # pylint: disable=missing-function-docstring
    pass


@when(parse("I issue SetOperateMode command on dish_leaf_node"))
def set_operate_mode(dish_leaf_node_device_name, devices_under_test):
    # pylint: disable=missing-function-docstring
    dish_leaf_node_proxy = devices_under_test[dish_leaf_node_device_name]
    dish_leaf_node_proxy.SetOperateMode()
    LOGGER.info("DishLeafNode requested to set operate mode on dish")


@then("dish_manager dishMode should report OPERATE")
def check_dish_manager_dish_mode(dish_manager_device_name, devices_under_test):
    # pylint: disable=missing-function-docstring
    dish_manager_proxy = devices_under_test[dish_manager_device_name]
    wait_for_change_on_resource(dish_manager_proxy, "dishMode", "OPERATE")
    current_dish_mode = retrieve_attr_value(dish_manager_proxy, "dishMode")
    assert current_dish_mode == "OPERATE"
    LOGGER.info(f"{dish_manager_proxy} dishMode: {current_dish_mode}")
