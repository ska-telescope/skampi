#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""
import sys

sys.path.append('/app')

import pytest
import logging
from time import sleep
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then

from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from tango import DeviceProxy, DevState
from test_support.helpers import wait_for, obsState, resource, watch, waiter, map_dish_nr_to_device_name
import logging

LOGGER = logging.getLogger(__name__)

@pytest.fixture
def result():
    return {}

@scenario("1_XR-13_XTP-494.feature", "A1-Test, Sub-array resource allocation")
@pytest.mark.skip(reason="WIP untill after refactoring")
def test_allocate_resources():
    """Assign Resources."""

@given("A running telescope for executing observations on a subarray")
def set_to_running():
    the_waiter = waiter()
    the_waiter.set_wait_for_starting_up()
    SKAMid().start_up()
    the_waiter.wait()

@when("I allocate 4 dishes to subarray 1")
def allocate_four_dishes(result):
    the_waiter = waiter()
    dish_devices = [map_dish_nr_to_device_name(x) for x in range(1,4+1)]
    the_waiter.set_wait_for_assign_resources(dish_devices)

    result['response'] = SubArray(1).allocate(ResourceAllocation(dishes=[Dish(1), Dish(2), Dish(3), Dish(4)]))

    #wait for certain values to be changed (refer to helpers for what is currently defined as neccesarry to wait)
    the_waiter.wait()
    LOGGER.info(the_waiter.logs)

    return result

@then("I have a subarray composed of 4 dishes")
def check_subarray_composition(result):
    #check that there was no error in response
    assert_that(result['response']).is_equal_to(ResourceAllocation(dishes=[Dish(1), Dish(2), Dish(3), Dish(4)]))
    #check that this is reflected correctly on TMC side
    assert_that(resource('ska_mid/tm_subarray_node/1').get("receptorIDList")).is_equal_to((1, 2, 3, 4))
    #check that this is reflected correctly on CSP side
    assert_that(resource('mid_csp/elt/subarray_01').get('receptors')).is_equal_to((1, 2, 3, 4))
    assert_that(resource('mid_csp/elt/master').get('receptorMembership')).is_equal_to((1, 1, 1, 1))
    #TODO need to find a better way of testing sets with sets
    #assert_that(set(resource('mid_csp/elt/master').get('availableReceptorIDs'))).is_subset_of(set((4,3)))
    #check that this is reflected correctly on SDP side - no code at the current implementation

@then("the subarray is in the condition that allows scan configurations to take place")
def check_subarry_state():
    #check that the TMC report subarray as being in the ON state and obsState = IDLE
    assert_that(resource('ska_mid/tm_subarray_node/1').get("State")).is_equal_to("ON")
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('IDLE')
    #check that the CSP report subarray as being in the ON state and obsState = IDLE
    assert_that(resource('mid_csp/elt/subarray_01').get('State')).is_equal_to('ON')
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('IDLE')
    #check that the SDP report subarray as being in the ON state and obsState = IDLE
    assert_that(resource('mid_sdp/elt/subarray_1').get('State')).is_equal_to('ON')
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('IDLE')

def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_mid/tm_subarray_node/1').get("State") == "ON"):
        the_waiter = waiter()
        dish_devices = [map_dish_nr_to_device_name(x) for x in range(1,4+1)]
        the_waiter.set_wait_for_tearing_down_subarray(dish_devices)
        SubArray(1).deallocate()
        the_waiter.wait()
        LOGGER.info(the_waiter.logs)

    the_waiter = waiter()
    the_waiter.set_wait_for_going_to_standby()
    SKAMid().standby()
    the_waiter.wait()
    LOGGER.info(the_waiter.logs)
    
