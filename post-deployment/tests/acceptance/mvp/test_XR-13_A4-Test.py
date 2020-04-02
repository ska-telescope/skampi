#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XR-13_A4-Test
----------------------------------
Acceptance test to deallocate the resources from subarray for MVP.
"""
import sys

sys.path.append('/app')
import time
import pytest
import logging
from time import sleep
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from tango import DeviceProxy, DevState
from resources.test_support.helpers import wait_for, obsState, resource, watch


@pytest.fixture
def result():
    return {}
    
@scenario("../../../features/1_XR-13_XTP-494.feature", "A4-Test, Sub-array deallocation of resources")

def test_deallocate_resources():
    """Deallocate Resources."""
    pass

@given('A running telescope with "4" dishes are allocated to "subarray 1"')
def set_to_running(result):
    SKAMid().start_up()
    #watch_State = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State")
    watch_receptorIDList = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("receptorIDList")
    result['response'] = SubArray(1).allocate(ResourceAllocation(dishes=[Dish(1), Dish(2), Dish(3), Dish(4)]))
    logging.info("subarray state: " + resource('ska_mid/tm_subarray_node/1').get("State"))
    watch_receptorIDList.wait_until_value_changed()
    return result

@when("I deallocate the resources")
def deallocate_resources(result):
    result = SubArray(1).deallocate()
    logging.info("ReleaseResources command is involked on subarray ")


@then('"subarray 1" should go into OFF state')
def subarray_state_OFF():
    logging.info("Now deallocating resources ... ")
    logging.info("subarray state: " + resource('ska_mid/tm_subarray_node/1').get("State"))
    # Confirm
    assert_that(resource('ska_mid/tm_subarray_node/1').get("State") == "OFF")
    assert_that(resource('ska_mid/tm_subarray_node/1').get("obsState")).is_equal_to("IDLE")
    logging.info("subarray obsState: " + resource('ska_mid/tm_subarray_node/1').get("obsState"))
    # Confirm
    logging.info("Subarray is now deallocated")


@then('ReceptorList for "subarray 1" should be empty')
def receptorID_list_empty():
    watch_receptorIDList = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("receptorIDList")
    # gather info
    receptorIDList_val = watch_receptorIDList.get_value_when_changed()
    # confirm
    assert_that(receptorIDList_val == [])
    logging.info("ReceptorIDList is empty")
    # put telescope to standby
    SKAMid().standby()

