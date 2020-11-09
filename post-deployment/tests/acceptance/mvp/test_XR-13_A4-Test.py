#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XR-13_A4-Test
----------------------------------
Acceptance test to deallocate the resources from subarray for MVP.
"""
import sys
import os

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
from resources.test_support.logging_decorators import log_it
from resources.test_support.sync_decorators import sync_release_resources

LOGGER = logging.getLogger(__name__)

DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True

devices_to_log = [
    'ska_mid/tm_subarray_node/1',
    'mid_csp/elt/subarray_01',
    'mid_csp_cbf/sub_elt/subarray_01',
    'mid_sdp/elt/subarray_1',
    'mid_d0001/elt/master',
    'mid_d0002/elt/master',
    'mid_d0003/elt/master',
    'mid_d0004/elt/master']
non_default_states_to_check = {
    'mid_d0001/elt/master' : 'pointingState',
    'mid_d0002/elt/master' : 'pointingState',
    'mid_d0003/elt/master' : 'pointingState',
    'mid_d0004/elt/master' : 'pointingState'}

@pytest.fixture
def result():
    return {}

@pytest.mark.select
@pytest.mark.skamid
#@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
@scenario("1_XR-13_XTP-494.feature", "A4-Test, Sub-array deallocation of resources")
def test_deallocate_resources():
    """Deallocate Resources."""
    pass

@given('A running telescope with "4" dishes are allocated to "subarray 1"')
def set_to_running(result):
    LOGGER.info("A running telescope with '2' dishes are allocated to 'subarray 1'")
    assert(telescope_is_in_standby())
    LOGGER.info("Starting up telescope")
    set_telescope_to_running()
    LOGGER.info("Assigning 2 dishes")
    take_subarray(1).to_be_composed_out_of(2)

@when("I deallocate the resources")
def deallocate_resources():
    @log_it('AX-13_A4',devices_to_log,non_default_states_to_check)
    @sync_release_resources
    def release():
        SubArray(1).deallocate()
    release()
    LOGGER.info("ReleaseResources command is involked on subarray ")


@then('"subarray 1" should go into OFF state')
def subarray_state_OFF():
    LOGGER.info("Now deallocating resources ... ")
    LOGGER.info("subarray state: " + resource('ska_mid/tm_subarray_node/1').get("State"))
    # Confirm
    #assert_that(resource('ska_mid/tm_subarray_node/1').get("State") == "OFF")
    assert_that(resource('ska_mid/tm_subarray_node/1').get("obsState")).is_equal_to("EMPTY")
    LOGGER.info("subarray obsState: " + resource('ska_mid/tm_subarray_node/1').get("obsState"))
    # Confirm
    LOGGER.info("Subarray is now deallocated")


@then('ReceptorList for "subarray 1" should be empty')
def receptorID_list_empty():
   # watch_receptorIDList = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("receptorIDList")
    # gather info
   # receptorIDList_val = watch_receptorIDList.get_value_when_changed()
    # confirm
    resource('ska_mid/tm_subarray_node/1').assert_attribute('receptorIDList').equals(None)
   # assert_that(receptorIDList_val == [])
    logging.info("ReceptorIDList is empty")

def teardown_function(function):
    LOGGER.info("Put Telescope back to standby")
    set_telescope_to_standby()

