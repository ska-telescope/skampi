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
import logging
import os
import json
#local dependencies
from resources.test_support.helpers import obsState, resource, watch, waiter, \
    map_dish_nr_to_device_name,watch
from resources.test_support.log_helping import DeviceLogging
from resources.test_support.persistance_helping import update_scan_config_file
from resources.test_support.sync_decorators import sync_configure_oet,time_it
from resources.test_support.controls import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,take_subarray,restart_subarray, tmc_is_on
import pytest
#SUT dependencies
from ska.scripting.domain import Telescope, SubArray

DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True


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

@pytest.fixture
def result():
    return {}

@pytest.mark.select
@pytest.mark.quarantine
@pytest.mark.skamid
# @pytest.mark.skip(reason="sdp subarray still in IDLE after tmc returned to READY, see SKB-22")
#@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
@scenario("1_XR-13_XTP-494.feature", "A2-Test, Sub-array transitions from IDLE to READY state")
def test_configure_subarray():
    """Configure Subarray."""

@given("I am accessing the console interface for the OET")
def start_up():
    LOGGER.info("Before starting the telescope checking if the TMC is in ON state")
    assert(tmc_is_on())
    LOGGER.info("Before starting the telescope checking if the telescope is in StandBy.")
    assert telescope_is_in_standby()
    LOGGER.info("Telescope is in StandBy.")
    LOGGER.info("Starting up telescope")
    set_telescope_to_running()
    LOGGER.info("Telescope is in ON telescopeState")


@given("sub-array is in IDLE state")
def assign(result):
    LOGGER.info("Allocate 2 dishes to Subarray 1")
    pilot, sdp_block = take_subarray(1).to_be_composed_out_of(2)
    result['sdp_block'] = sdp_block
    LOGGER.info("Subarray 1 is ready and composed out of 2 dishes")
    LOGGER.info("SDP block in AssignResources json input is :" + str(result))
    return result

@when("I call the configure scan execution instruction")
def config(result):
   
    @sync_configure_oet
    #TODO: Confirm if @time_it is required. Currently commenting as seem to be not required
    # @time_it(120)
    def test_SUT(sdp_block):
        file = 'resources/test_data/OET_integration/configure1.json'
        update_scan_config_file(file, sdp_block)
        LOGGER.info("SDP block is :" +str(sdp_block))
        LOGGER.info("Invoking Configure command on Subarray 1")
        SubArray(1).configure_from_file(file, 6, with_processing = False)
    test_SUT(result['sdp_block'])
    LOGGER.info("Result[SDP block] :" + str(result['sdp_block']))
    LOGGER.info("Configure command on Subarray 1 is successful")


@then("sub-array is in READY state for which subsequent scan commands can be directed to deliver a basic imaging outcome")
def check_state():
    LOGGER.info("Checking the results for Configure command execution")
    # check that the SDP report subarray as being in the obsState = READY
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('READY')
    # check that the CSP report subarray as being in the obsState = READY
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('READY')
    # check that the TMC report subarray as being in the obsState = READY
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('READY')
    LOGGER.info("Results OK for Configure command")


def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_mid/tm_subarray_node/1').get('State') == "ON"):
        #this means there must have been an error
        if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "IDLE"):
            LOGGER.info("tearing down composed subarray (IDLE)")
            take_subarray(1).and_release_all_resources()  
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "READY"):
        #this means test must have passed
        LOGGER.info("tearing down configured subarray (READY)")
        take_subarray(1).and_end_sb_when_ready().and_release_all_resources()
        LOGGER.info("EndSb and ReleaseResources is involked on Subarray 1")
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
        LOGGER.warn("Subarray is still in configuring! Please restart MVP manualy to complete tear down")
        restart_subarray(1)
        #raise exception since we are unable to continue with tear down
        raise Exception("Unable to tear down test setup")
    LOGGER.info("Put Telescope back to standby")
    set_telescope_to_standby()
    LOGGER.info("Telescope is in standby")
