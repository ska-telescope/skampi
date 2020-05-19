#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XR-13_A4-Test
----------------------------------
Acceptance test to deallocate the resources from subarray for MVP.
"""
import sys

import time
import pytest
import logging
from time import sleep
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
##SUT
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
#SUT infra
from tango import DeviceProxy, DevState
#local dependencies
from resources.test_support.helpers import  obsState, resource, watch
from resources.test_support.controls import set_telescope_to_standby,set_telescope_to_running,\
    telescope_is_in_standby,take_subarray,restart_subarray

LOGGER = logging.getLogger(__name__)

@pytest.fixture
def result():
    return {}

@pytest.mark.skip(reason="no way of currently testing this")
@scenario("../../../features/1_XR-13_XTP-494.feature", "A4-Test, Sub-array deallocation of resources")
def test_deallocate_resources():
    """Deallocate Resources."""
    pass

@given('A running telescope with "4" dishes are allocated to "subarray 1"')
def set_to_running(result):
    LOGGER.info("A running telescope with '4' dishes are allocated to 'subarray 1'")
    assert(telescope_is_in_standby())
    LOGGER.info("Starting up telescope")
    set_telescope_to_running()
    LOGGER.info("Assigning 4 dishes")
    take_subarray(1).to_be_composed_out_of(4)

@when("I deallocate the resources")
def deallocate_resources():
    SubArray(1).deallocate()
    LOGGER.info("ReleaseResources command is involked on subarray ")


@then('"subarray 1" should go into OFF state')
def subarray_state_OFF():
    LOGGER.info("Now deallocating resources ... ")
    LOGGER.info("subarray state: " + resource('ska_mid/tm_subarray_node/1').get("State"))
    # Confirm
    assert_that(resource('ska_mid/tm_subarray_node/1').get("State") == "OFF")
    assert_that(resource('ska_mid/tm_subarray_node/1').get("obsState")).is_equal_to("IDLE")
    LOGGER.info("subarray obsState: " + resource('ska_mid/tm_subarray_node/1').get("obsState"))
    # Confirm
    LOGGER.info("Subarray is now deallocated")


@then('ReceptorList for "subarray 1" should be empty')
def receptorID_list_empty():
    watch_receptorIDList = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("receptorIDList")
    # gather info
    receptorIDList_val = watch_receptorIDList.get_value_when_changed()
    # confirm
    assert_that(receptorIDList_val == [])
    logging.info("ReceptorIDList is empty")

def teardown_function(function):
    LOGGER.info("Put Telescope back to standby")
    set_telescope_to_standby()

