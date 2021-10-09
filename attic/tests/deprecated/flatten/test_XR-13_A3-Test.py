#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""

import random
import os
import signal
from concurrent import futures
from time import sleep
import threading
from datetime import date
from random import choice
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
import pytest
from ska.scripting.domain import Telescope, SubArray
from tango import DeviceProxy, DevState
from resources.test_support.helpers import  obsState, resource, watch, waiter, map_dish_nr_to_device_name
import logging
from resources.test_support.controls import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,take_subarray,restart_subarray, tmc_is_on
from resources.test_support.sync_decorators import  sync_scan_oet,sync_configure_oet,time_it

LOGGER = logging.getLogger(__name__)

import json

DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True



@pytest.fixture
def fixture():
    return {}

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

@pytest.mark.select
@pytest.mark.quarantine
@pytest.mark.skamid
# @pytest.mark.skip(reason="disabled  due to bug SKB-38")
@scenario("1_XR-13_XTP-494.feature", "A3-Test, Sub-array performs an observational imaging scan")
def test_subarray_scan():
    """Imaging Scan Operation."""

@given("I am accessing the console interface for the OET")
def start_up():
    LOGGER.info("Before starting the telescope checking if the TMC is in ON state")
    assert(tmc_is_on())
    LOGGER.info("Before starting the telescope checking if the telescope is in StandBy")
    assert(telescope_is_in_standby())
    LOGGER.info("Telescope is in StandBy.")
    LOGGER.info("Starting up the telescope")
    set_telescope_to_running()
    LOGGER.info("Telescope started.")

@given("Sub-array is in READY state")
def set_to_ready():
    LOGGER.info("Allocate 2 dishes to Subarray 1")
    pilot, sdp_block = take_subarray(1).to_be_composed_out_of(2)
    LOGGER.info("AssignResources is successful on Subarray 1 with 2 dishes allocated")
    LOGGER.info("Invoking configure command on the Subarray.")
    take_subarray(1).and_configure_scan_by_file(sdp_block)
    LOGGER.info("Configure is successful on Subarray")

@given("duration of scan is 10 seconds")
def scan_duration(fixture):
    fixture['scans'] = '{"interface":"https://schema.skao.intg/ska-tmc-scan/2.0","transaction_id":"txn-....-00001","scan_id":1}'
    return fixture

@when("I call the execution of the scan instruction")
def invoke_scan_command(fixture):
    #TODO add method to clear thread in case of failure
    @sync_scan_oet
    def scan():
        def send_scan(duration):
            # TODO: Update the api when new tmc-mid chart is published
            SubArray(1).scan()
            # SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
            # SubarrayNode.Scan('{"interface":"https://schema.skao.intg/ska-tmc-scan/2.0","transaction_id":"txn-....-00001","scan_id":1}')
        LOGGER.info("Scan command is invoked on Subarray 1")
        executor = futures.ThreadPoolExecutor(max_workers=1)
        return executor.submit(send_scan,fixture['scans'])
    fixture['future'] = scan()
    return fixture

@then("Sub-array changes to a SCANNING state")
def check_ready_state(fixture):
    # check that the TMC report subarray as being in the obsState = READY
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('SCANNING')
    #current functionality implies TMC may be in scanning even though CSP is not yet
    #logging.info("TMC-subarray obsState: " + resource('ska_mid/tm_subarray_node/1').get("obsState"))
    #assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('SCANNING')
    #logging.info("CSP-subarray obsState: " + resource('mid_csp/elt/subarray_01').get("obsState"))
    #check that the SDP report subarray as being in the obsState = READY
    #assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('SCANNING')
    #logging.info("SDP-subarray obsState: " + resource('mid_sdp/elt/subarray_1').get("obsState"))
    return fixture

@then("observation ends after 10 seconds as indicated by returning to READY state")
def check_running_state(fixture):
    fixture['future'].result(timeout=10)
    # check that the SDP report subarray as being in the obsState = READY
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('READY')
    # check that the CSP report subarray as being in the obsState = READY
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('READY')
    # check that the TMC report subarray as being in the obsState = READY
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('READY')
    logging.info("TMC-subarray obsState: " + resource('ska_mid/tm_subarray_node/1').get("obsState"))
    logging.info("EndScan Command is successful on Subarray.")

def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_mid/tm_subarray_node/1').get('State') == "ON"):
        if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "IDLE"):
            LOGGER.info("tearing down composed subarray (IDLE)")
            take_subarray(1).and_release_all_resources()  
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "READY"):
        LOGGER.info("tearing down configured subarray (READY)")
        take_subarray(1).and_end_sb_when_ready().and_release_all_resources()
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
        LOGGER.warn("Subarray is still in CONFIFURING! Please restart MVP manually to complete tear down")
        restart_subarray(1)
        #raise exception since we are unable to continue with tear down
        raise Exception("Unable to tear down test setup")
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "SCANNING"):
        LOGGER.warn("Subarray is still in SCANNING! Please restart MVP manually to complete tear down")
        restart_subarray(1)
        #raise exception since we are unable to continue with tear down
        raise Exception("Unable to tear down test setup")
    LOGGER.info("Put Telescope back to standby")
    set_telescope_to_standby()
    

