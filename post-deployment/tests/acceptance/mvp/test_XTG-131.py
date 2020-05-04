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
from resources.test_support.helpers import resource, watch


LOGGER = logging.getLogger(__name__)
scenario = partial(scenario, "../../../features/XTG-131.feature")
mode_cmd_map = {
    "STANDBY-LP": "SetStandbyLPMode",
    "STANDBY-FP": "SetStandbyFPMode",
    "OPERATE": "SetOperateMode"
}


def _change_dish_mode(cmd, dev_proxy):
    getattr(dev_proxy, cmd)()
    watch_dish_mode = (watch(resource('mid_d0001/elt/master')).for_a_change_on('dishMode'))
    watch_dish_mode.wait_until_value_changed()

@pytest.fixture
def set_initial_dish_mode(create_dish_master_proxy):
    # standbyfp mode is used as initial condition since it can be reached from other dish modes
    _change_dish_mode('SetStandbyFPMode', create_dish_master_proxy)
    _change_dish_mode('SetStandbyLPMode', create_dish_master_proxy)

# define steps for scenario
@given(parsers.parse("Dish Master reports {expected:D} Dish mode"))
def pre_condition(expected):
    logging.info('Dish 0001 initial dishMode: ' + resource('mid_d0001/elt/master').get('dishMode'))
    assert_that(resource('mid_d0001/elt/master').get('dishMode')).is_equal_to(expected)

@when(parsers.parse("I command Dish Master to {requested:D} Dish mode"))
def set_dish_mode(requested, create_dish_master_proxy):
    _change_dish_mode(mode_cmd_map[requested], create_dish_master_proxy)
    logging.info('Dish 0001 requested dishMode: ' + resource('mid_d0001/elt/master').get('dishMode'))

@then(parsers.parse("Dish Master reports {desired:D} Dish mode"))
def check_dish_mode(desired):
    logging.info('Dish 0001 desired dishMode: ' + resource('mid_d0001/elt/master').get('dishMode'))
    assert_that(resource('mid_d0001/elt/master').get('dishMode')).is_equal_to(desired)

@then(parsers.parse("Dish Master (device) is in {desired:D} state"))
def check_master_device_state(desired):
    logging.info('Dish 0001 desired state: ' + resource('mid_d0001/elt/master').get('State'))
    assert_that(resource('mid_d0001/elt/master').get('State')).is_equal_to(desired)


# Note: scenarios have to be executed in sequential order in order for the tests to pass
@pytest.mark.fast
@scenario("Dish from STANDBY-LP to STANDBY-FP")
def test_dish_standbylp_to_standbyfp_mode(set_initial_dish_mode):
    pass

@pytest.mark.fast
@scenario("Dish from STANDBY-FP to OPERATE")
def test_dish_standbyfp_to_operate_mode():
    pass

@pytest.mark.fast
@scenario("Dish from OPERATE to STANDBY-FP")
def test_dish_operate_to_standbyfp():
    pass

@pytest.mark.fast
@scenario("Dish from STANDBY-FP to STANDBY-LP")
def test_dish_standbyfp_to_standbylp():
    pass
