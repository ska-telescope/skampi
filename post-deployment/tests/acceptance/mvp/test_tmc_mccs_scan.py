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
from tango import DeviceProxy, DevState
from resources.test_support.helpers_low import resource, watch, waiter, wait_before_test
from resources.test_support.logging_decorators import log_it
import logging
from resources.test_support.controls_low import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,restart_subarray
from resources.test_support.sync_decorators_low import  sync_scan_oet,sync_configure_oet, sync_scan, time_it
import resources.test_support.tmc_helpers_low as tmc

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
    'ska_low/tm_subarray_node/1',
    'low-mccs/control/control',
    'low-mccs/subarray/01']
non_default_states_to_check = {}

@pytest.mark.skalow
#@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
@scenario("XTP-1188.feature", "TMC and MCCS subarray performs an observational scan")
def test_subarray_scan():
    """Scan Operation."""

@given("Subarray is in ON state")
def start_up():
    LOGGER.info("Check whether telescope is in StandBy")
    assert(telescope_is_in_standby())
    LOGGER.info("Starting up telescope")
    set_telescope_to_running()
    wait_before_test(timeout=20)

@given("Subarray is configured successfully")
def set_to_ready():
    tmc.compose_sub()
    LOGGER.info("AssignResources is invoked on Subarray")
    wait_before_test(timeout=10)
    tmc.configure_sub()
    LOGGER.info("Configure is invoke on Subarray")
    wait_before_test(timeout=10)

@when("I call the execution of the scan command for duration of 10 seconds")
def invoke_scan_command(fixture):
    @sync_scan(200)
    def scan():
        def send_scan(duration):
            SubarrayNodeLow = DeviceProxy('ska_low/tm_subarray_node/1')
            SubarrayNodeLow.Scan('{"id":1}')
        LOGGER.info("Scan is invoked on Subarray 1")
        executor = futures.ThreadPoolExecutor(max_workers=1)
        return executor.submit(send_scan,'{"id":1}')
    fixture['future'] = scan()
    return fixture

@then("Subarray changes to a SCANNING state")
def check_scanning_state(fixture):
    # check that the TMC report subarray as being in the obsState = SCANNING
    logging.info("TMC subarray low obsState: " + resource('ska_low/tm_subarray_node/1').get("obsState"))
    assert_that(resource('ska_low/tm_subarray_node/1').get('obsState')).is_equal_to('SCANNING')
    # check that the MCCS report subarray as being in the obsState = SCANNING
    logging.info("MCCS subarray low obsState: " + resource('low-mccs/subarray/01').get("obsState"))
    assert_that(resource('low-mccs/subarray/01').get('obsState')).is_equal_to('SCANNING')
    return fixture

@then("Observation ends after 10 seconds as indicated by returning to READY state")
def check_ready_state(fixture):
    fixture['future'].result(timeout=10)
    wait_before_test(timeout=10)
    # check that the TMC report subarray as being in the obsState = READY
    logging.info("TMC subarray low obsState: " + resource('ska_low/tm_subarray_node/1').get("obsState"))
    assert_that(resource('ska_low/tm_subarray_node/1').get('obsState')).is_equal_to('READY')
    # check that the MCCS report subarray as being in the obsState = READY
    logging.info("MCCS subarray low obsState: " + resource('low-mccs/subarray/01').get("obsState"))
    assert_that(resource('low-mccs/subarray/01').get('obsState')).is_equal_to('READY')
    
def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_low/tm_subarray_node/1').get('State') == "ON"):
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "IDLE"):
            LOGGER.info("tearing down composed subarray (IDLE)")
            # take_subarray(1).and_release_all_resources() 
            tmc.release_resources()
            LOGGER.info('Invoked ReleaseResources on Subarray')
            wait_before_test(timeout=10)
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "READY"):
            LOGGER.info("tearing down configured subarray (READY)")
            # take_subarray(1).and_end_sb_when_ready().and_release_all_resources()
            tmc.end()
            resource('ska_low/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
            LOGGER.info('Invoked End on Subarray')
            wait_before_test(timeout=10)
            tmc.release_resources()
            LOGGER.info('Invoked ReleaseResources on Subarray')
            wait_before_test(timeout=10)
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
            LOGGER.warn("Subarray is still in CONFIFURING! Please restart MVP manualy to complete tear down")
            restart_subarray(1)
            #raise exception since we are unable to continue with tear down
            raise Exception("Unable to tear down test setup")
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "SCANNING"):
            LOGGER.warn("Subarray is still in SCANNING! Please restart MVP manualy to complete tear down")
            restart_subarray(1)
            #raise exception since we are unable to continue with tear down
            raise Exception("Unable to tear down test setup")
        LOGGER.info("Put Telescope back to standby")
        set_telescope_to_standby()
    else:
        LOGGER.warn("Subarray is in inconsistent state! Please restart MVP manualy to complete tear down")
        restart_subarray(1)
