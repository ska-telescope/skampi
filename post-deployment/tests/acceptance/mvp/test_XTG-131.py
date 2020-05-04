#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTG-131
----------------------------------
Acceptance tests for MVP.
"""

import logging
import pytest
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
from resources.test_support.helpers import resource, watch, waiter

LOGGER = logging.getLogger(__name__)

@pytest.mark.fast
@scenario("../../../features/XTG-131.feature", "Dish to full power standby mode")
def test_dish_full_power_mode():
    """Set Dish to full power standby mode"""

@given("Dish Master reports OPERATE Dish mode")
def pre_condition():
    logging.info('Dish 0001 dishMode: ' + resource('mid_d0001/elt/master').get('dishMode'))
    assert_that(resource('mid_d0001/elt/master').get('dishMode')).is_equal_to('OPERATE')

@when("I command Dish Master to STANDBY_FP Dish mode")
def set_dish_standby_fp(create_dish_master_proxy):
    create_dish_master_proxy.SetStandbyFPMode()
    # Using waiter object to wait for the mode change to happen
    the_waiter = waiter()
    the_waiter.waits.append(watch(resource('mid_d0001/elt/master')).for_a_change_on('dishMode'))
    the_waiter.wait()
    logging.info('Dish 0001 dishMode: ' + resource('mid_d0001/elt/master').get('dishMode'))

@then("Dish Master reports STANDBY_FP Dish mode")
def check_dish_standby_fp():
    logging.info('Dish 0001 dishMode: ' + resource('mid_d0001/elt/master').get('dishMode'))
    assert_that(resource('mid_d0001/elt/master').get('dishMode')).is_equal_to('STANDBY-FP')

@then("Dish Master (device) is in STANDBY state")
def check_master_device_state():
    logging.info('Dish 0001 state: ' + resource('mid_d0001/elt/master').get('State'))
    assert_that(resource('mid_d0001/elt/master').get('State')).is_equal_to('STANDBY')

