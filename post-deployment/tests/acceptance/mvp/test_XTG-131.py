#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTG-131
----------------------------------
Acceptance tests for MVP.
"""

import logging
import pytest
from functools import partial
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then, parsers
from tango import DeviceProxy
from resources.test_support.helpers import resource, watch


LOGGER = logging.getLogger(__name__)
scenario = partial(scenario, "../../../features/XTG-131.feature")
mode_cmd_map = {
    "STANDBY-LP": "SetStandbyLPMode",
    "STANDBY-FP": "SetStandbyFPMode",
    "OPERATE": "SetOperateMode"
}


def _change_dish_mode(dev_proxy, cmd, device_name):
    getattr(dev_proxy, cmd)()
    watch_dish_mode = watch(resource(device_name)).for_a_change_on('dishMode')
    watch_dish_mode.wait_until_value_changed()

# define steps for scenario
@given(parsers.parse("{device_name} reports {expected} Dish mode"))
def device_proxy(device_name, expected):
    dev_proxy = DeviceProxy(device_name)
    # standbyfp mode is used as initial condition since it can be reached from other dish modes
    _change_dish_mode(dev_proxy, 'SetStandbyFPMode', device_name)
    _change_dish_mode(dev_proxy, mode_cmd_map[expected], device_name)
    logging.info(device_name + ' initial dishMode: ' + resource(device_name).get('dishMode'))
    assert_that(resource(device_name).get('dishMode')).is_equal_to(expected)
    return dev_proxy

@when(parsers.parse("I command {device_name} to {requested} Dish mode"))
def set_dish_mode(device_name, requested, device_proxy):
    _change_dish_mode(device_proxy, mode_cmd_map[requested], device_name)
    logging.info(device_name + ' requested dishMode: ' + resource(device_name).get('dishMode'))

@then(parsers.parse("{device_name} reports {desired} Dish mode"))
def check_dish_mode(device_name, desired):
    logging.info(device_name + ' desired dishMode: ' + resource(device_name).get('dishMode'))
    assert_that(resource(device_name).get('dishMode')).is_equal_to(desired)

@then(parsers.parse("{device_name} is in {desired} state"))
def check_master_device_state(device_name, desired):
    logging.info(device_name + ' desired state: ' + resource(device_name).get('State'))
    assert_that(resource(device_name).get('State')).is_equal_to(desired)


# mid_d0001/elt/master
@pytest.mark.fast
@scenario("mid_d0001/elt/master from STANDBY-LP to STANDBY-FP")
def test_mid_d0001_from_standbylp_to_standbyfp_mode():
    pass

@pytest.mark.fast
@scenario("mid_d0001/elt/master from STANDBY-FP to OPERATE")
def test_mid_d0001_from_standbyfp_to_operate_mode():
    pass

@pytest.mark.fast
@scenario("mid_d0001/elt/master from OPERATE to STANDBY-FP")
def test_mid_d0001_from_operate_to_standbyfp():
    pass

@pytest.mark.fast
@scenario("mid_d0001/elt/master from STANDBY-FP to STANDBY-LP")
def test_mid_d0001_from_standbyfp_to_standbylp():
    pass
