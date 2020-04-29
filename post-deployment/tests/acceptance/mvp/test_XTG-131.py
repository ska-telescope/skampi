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

@scenario("../../../features/XTG-131.feature", "Dish to full power standby mode")
def test_dish_full_power_mode():
    """Set Dish to full power standby mode"""

@given("Dish Master reports STANDBY_LP Dish mode")
def pre_condition():
    the_waiter = waiter()
    the_waiter.set_wait_for_starting_up()
    SKAMid().start_up()
    the_waiter.wait()
    LOGGER.info(the_waiter.logs)

@when("I command Dish Master to STANDBY_FP Dish mode")
def set_dish_standby_fp():
    assert_that(resource('mid_d0001/elt/master').get('dishmode')).is_equal_to('3')

@then("Dish Master reports STANDBY_FP Dish mode")
def check_dish_standby_fp():
    assert_that(resource('mid_d0001/elt/master').get('dishmode')).is_equal_to('3')
    logging.info("Dish 0001 dishmode: " + resource('mid_d0001/elt/master').get("dishmode"))

def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    the_waiter = waiter()
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "IDLE"):
        the_waiter.set_wait_for_tearing_down_subarray()
        LOGGER.info("tearing down composed subarray (IDLE)")
        SubArray(1).deallocate()
        the_waiter.wait()
        LOGGER.info(the_waiter.logs)
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "READY"):
        LOGGER.info("tearing down configured subarray (READY)")
        the_waiter.set_wait_for_ending_SB()
        SubArray(1).end_sb()
        the_waiter.wait()
        LOGGER.info(the_waiter.logs)
        the_waiter.set_wait_for_tearing_down_subarray()
        SubArray(1).deallocate()
        the_waiter.wait()
        LOGGER.info(the_waiter.logs)
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
        LOGGER.info("tearing down configuring subarray")
        restart_subarray(1)
    the_waiter.set_wait_for_going_to_standby()
    SKAMid().standby()
    LOGGER.info("standby command is executed on telescope")
    the_waiter.wait()
    LOGGER.info(the_waiter.logs)

