#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""
import random
import signal
from datetime import date,datetime
from random import choice
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
from  time  import sleep
import logging
import json
#local dependencies
from resources.test_support.helpers import wait_for, obsState, resource, watch, waiter, \
    map_dish_nr_to_device_name,watch
from resources.test_support.log_helping import DeviceLogging
from resources.test_support.state_checking import StateChecker
from resources.test_support.persistance_helping import update_scan_config_file
from resources.test_support.logging_decorators import log_it
from resources.test_support.sync_decorators import sync_configure_oet,time_it
from resources.test_support.controls import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,take_subarray,restart_subarray
import pytest
#SUT dependencies
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish


LOGGER = logging.getLogger(__name__)

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

@scenario("../../../features/1_XR-13_XTP-494.feature", "A2-Test, Sub-array transitions from IDLE to READY state")
def test_configure_subarray():
    """Configure Subarray."""

@given("I am accessing the console interface for the OET")
def start_up():
    LOGGER.info("Given I am accessing the console interface for the OETy")
    assert(telescope_is_in_standby())
    LOGGER.info("Starting up telescope")
    set_telescope_to_running()



@given("sub-array is in IDLE state")
def assign():
    take_subarray(1).to_be_composed_out_of(2)
    LOGGER.info("Subarray 1 is ready and composed out of 4 dishes")

@when("I call the configure scan execution instruction")
def config():

    @log_it('AX-13_A2',devices_to_log,non_default_states_to_check)
    @sync_configure_oet
    @time_it(120)
    def test_SUT():
        file = 'resources/test_data/TMC_integration/configure1.json'
        update_scan_config_file(file)
        SubArray(1).configure_from_file(file, 2, with_processing = False)
    test_SUT()

    

@then("sub-array is in READY state for which subsequent scan commands can be directed to deliver a basic imaging outcome")
def check_state():
    LOGGER.info("Checking the results")
    # check that the TMC report subarray as being in the obsState = READY
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('READY')
    # check that the CSP report subarray as being in the obsState = READY
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('READY')
    # check that the SDP report subarray as being in the obsState = READY
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('READY')
    LOGGER.info("Results OK")


def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "IDLE"):
        #this means there must have been an error
        if (resource('ska_mid/tm_subarray_node/1').get('State') == "ON"):
            LOGGER.info("tearing down composed subarray (IDLE)")
            take_subarray(1).and_release_all_resources()  
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "READY"):
        #this means test must have passed
        LOGGER.info("tearing down configured subarray (READY)")
        take_subarray(1).and_end_sb_when_ready().and_release_all_resources() 
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
        LOGGER.warn("Subarray is still in configuring! Please restart MVP manualy to complete tear down")
        restart_subarray(1)
        #raise exception since we are unable to continue with tear down
        raise Exception("Unable to tear down test setup")
    LOGGER.info("Put Telescope back to standby")
    set_telescope_to_standby()

