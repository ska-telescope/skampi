#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-813
----------------------------------
Acceptance tests for MVP.
"""

import logging
import pytest
from functools import partial
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then, parsers
from tango import DeviceProxy # type: ignore
from resources.test_support.helpers import monitor, resource, watch


LOGGER = logging.getLogger(__name__)

mode_cmd_map = {
    "STANDBY_LP": "SetStandbyLPMode",
    "STANDBY_FP": "SetStandbyFPMode",
    "OPERATE": "SetOperateMode",
}
# to be used in teardown
device_proxies = {}


def _change_dish_mode(dev_proxy, cmd, device_name):
    dev_proxy.command_inout(cmd)
    watch_dish_mode = watch(resource(device_name)).for_a_change_on("dishMode")
    assert isinstance(watch_dish_mode, monitor)
    watch_dish_mode.wait_until_value_changed()


def pre_condition(dev_proxy, device_name, expected):
    """verify the device dish mode before executing mode transition requests"""
    actual = resource(device_name).get("dishMode")
    LOGGER.info(f"Resource actual dishMode: {actual}. Expected dishMode: {expected}")
    if actual != expected:
        # standbyfp is used as initial condition because it can be reached from other
        # dish modes but dont request standbyfp if this is the current dish mode
        if actual != "STANDBY_FP":
            _change_dish_mode(dev_proxy, "SetStandbyFPMode", device_name)
        _change_dish_mode(dev_proxy, mode_cmd_map[expected], device_name)
    assert_that(resource(device_name).get("dishMode")).is_equal_to(expected)
    LOGGER.info(f"{device_name} initial dishMode: {resource(device_name).get('dishMode')}")


@pytest.fixture(autouse=True, scope="module")
def restore_dish_state(request):
    """A teardown function which will ensure that all dishes used in the test are restored to
    STANDBY state
    """

    def put_dish_in_standby_fp_mode():
        LOGGER.info("Restoring all dishes to STANDBY state")
        for dev_name, dev_proxy in device_proxies.items():
            _change_dish_mode(dev_proxy, "SetStandbyFPMode", dev_name)

    request.addfinalizer(put_dish_in_standby_fp_mode)


@pytest.mark.fast
@pytest.mark.skamid
@pytest.mark.quarantine
@scenario("XTP-813.feature", "Test dish master simulator dishMode change")
def test_mode_transitions():
    pass


@given("<dish_master> reports <start_mode> Dish mode", target_fixture='device_proxy')
def device_proxy(dish_master, start_mode):
    # update the device_proxies collection for teardown
    if dish_master not in device_proxies:
        dev_proxy = DeviceProxy(dish_master)
        device_proxies[dish_master] = dev_proxy

    pre_condition(device_proxies[dish_master], dish_master, start_mode)
    return device_proxies[dish_master]


@when("I command <dish_master> to <end_mode> Dish mode")
def set_dish_mode(device_proxy, dish_master, end_mode):
    _change_dish_mode(device_proxy, mode_cmd_map[end_mode], dish_master)
    LOGGER.info(f"{dish_master} requested dishMode: {end_mode}")


@then("<dish_master> reports <end_mode> Dish mode")
def check_dish_mode(dish_master, end_mode):
    assert_that(resource(dish_master).get("dishMode")).is_equal_to(end_mode)
    LOGGER.info(f"{dish_master} desired dishMode: {resource(dish_master).get('dishMode')}")


@then("<dish_master> is in <end_state> state")
def check_master_device_state(dish_master, end_state):
    assert_that(resource(dish_master).get("State")).is_equal_to(end_state)
    LOGGER.info(f"{dish_master} desired state: {resource(dish_master).get('State')}")
