#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTG-131
----------------------------------
Acceptance tests for MVP.
"""

import logging
import pytest
from time import sleep
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from resources.test_support.helpers import wait_for, obsState, resource, watch, take_subarray, restart_subarray, waiter, \
    map_dish_nr_to_device_name, update_file, DeviceLogging

LOGGER = logging.getLogger(__name__)

@pytest.mark.fast
@scenario("../../../features/XTG-131.feature", "Dish to full power standby mode")
def test_dish_full_power_mode():
    """Set Dish to full power standby mode"""

@given("Dish Master reports STANDBY_LP Dish mode")
def pre_condition(create_dish_master_proxy):
    logging.info("Dish 0001 dishMode: " + str(create_dish_master_proxy.dishMode))
    create_dish_master_proxy.SetStandbyLPMode()
    logging.info("Dish 0001 dishMode: " + str(create_dish_master_proxy.dishMode))
    assert_that(create_dish_master_proxy.dishMode).is_equal_to(3)

@when("I command Dish Master to STANDBY_FP Dish mode")
def set_dish_standby_fp():
    # TODO: set dish to standby FP mode
    pass

@then("Dish Master reports STANDBY_FP Dish mode")
def check_dish_standby_fp():
    # TODO: test that dish is in standby FP mode
    logging.info("Dish 0001 dishMode: " + resource('mid_d0001/elt/master').get("dishMode"))
    assert_that(resource('mid_d0001/elt/master').get('dishmode')).is_equal_to(3)

def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function call.
    """
    pass

