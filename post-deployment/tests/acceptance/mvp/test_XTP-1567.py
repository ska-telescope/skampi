#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""
import os
import pytest
import logging
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then

#SUT infrastructure
from tango import DeviceProxy, DevState
## local imports
from resources.test_support.helpers_low import resource, wait_before_test
from resources.test_support.sync_decorators_low import sync_obsreset
from resources.test_support.persistance_helping import load_config_from_file
from resources.test_support.controls_low import set_telescope_to_standby, set_telescope_to_running, telescope_is_in_standby, restart_subarray_low
import resources.test_support.tmc_helpers_low as tmc

DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True

LOGGER = logging.getLogger(__name__)

devices_to_log = [
    'ska_low/tm_subarray_node/1',
    'low-mccs/control/control',
    'low-mccs/subarray/01']
non_default_states_to_check = {}


@pytest.fixture
def result():
    return {}

@pytest.mark.skalow
@scenario("XTP-1567.feature", "BDD test case for ObsReset command in MVP Low")
def test_subarray_obsreset():
    """reset subarray"""

@given("Subarray has transitioned into obsState ABORTED during an observation")
def set_to_abort():
    LOGGER.info("Given A running telescope for executing observations on a subarray")
    #Added timeout of 10 sec to wait tmc_low subarray to become OFF
    wait_before_test(timeout=10)
    assert(telescope_is_in_standby())
    LOGGER.info("Starting up telescope")
    set_telescope_to_running()
    wait_before_test(timeout=10)
    tmc.compose_sub()
    LOGGER.info("AssignResources is invoked on Subarray")
    wait_before_test(timeout=10)

    tmc.configure_sub()
    LOGGER.info("Configure is invoked on Subarray")
    wait_before_test(timeout=10)

    scan_file = 'resources/test_data/TMC_integration/mccs_scan.json'
    scan_string = load_config_from_file(scan_file)
    SubarrayNodeLow = DeviceProxy('ska_low/tm_subarray_node/1')
    SubarrayNodeLow.Scan(scan_string)
    LOGGER.info("Scan is invoked on Subarray")

    SubarrayNodeLow.Abort()
    LOGGER.info("Abort is invoked on Subarray")
    wait_before_test(timeout=10)

@when("the operator invokes ObsReset command")
def reset_subarray():
   
    @sync_obsreset(200)
    def obsreset_subarray():
        tmc.obsreset()
        LOGGER.info("obsreset command is invoked on subarray")
    obsreset_subarray()

@then("the subarray should transition to obsState IDLE")
def check_idle_state():
    assert_that(resource('ska_low/tm_subarray_node/1').get('obsState')).is_equal_to('IDLE')
    assert_that(resource('low-mccs/subarray/01').get('obsState')).is_equal_to('IDLE')
    LOGGER.info("Obsreset is completed")

def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_low/tm_subarray_node/1').get('State') == "ON"):
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "IDLE"):
            LOGGER.info("tearing down composed subarray (IDLE)")
            tmc.release_resources()
            LOGGER.info('Invoked ReleaseResources on Subarray')
            wait_before_test(timeout=10)
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "READY"):
            LOGGER.info("tearing down configured subarray (READY)")
            tmc.end()
            resource('ska_low/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
            LOGGER.info('Invoked End on Subarray')
            wait_before_test(timeout=10)
            tmc.release_resources()
            LOGGER.info('Invoked ReleaseResources on Subarray')
            wait_before_test(timeout=10)
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
            LOGGER.warn("Subarray is still in CONFIFURING! Please restart MVP manualy to complete tear down")
            restart_subarray_low(1)
            #raise exception since we are unable to continue with tear down
            raise Exception("Unable to tear down test setup")
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "SCANNING"):
            LOGGER.warn("Subarray is still in SCANNING! Please restart MVP manualy to complete tear down")
            restart_subarray_low(1)
            #raise exception since we are unable to continue with tear down
            raise Exception("Unable to tear down test setup")
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "ABORTING"):
            LOGGER.warn("Subarray is still in ABORTING! Please restart MVP Low manualy to complete tear down")
            restart_subarray_low(1)
            #raise exception since we are unable to continue with tear down
            raise Exception("Unable to tear down test setup") 
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "RESETTING"):
            LOGGER.warn("Subarray is still in RESTARTING! Please restart MVP manualy to complete tear down")
            restart_subarray_low(1)
            #raise exception since we are unable to continue with tear down
            raise Exception("Unable to tear down test setup") 
        set_telescope_to_standby()
        LOGGER.info("Telescope is in standby")
