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
import os
import json
#local dependencies
from resources.test_support.helpers_low import obsState, resource, watch, waiter, wait_before_test
#from resources.test_support.log_helping import DeviceLogging
#from resources.test_support.state_checking import StateChecker
from resources.test_support.persistance_helping import update_scan_config_file
from resources.test_support.logging_decorators import log_it
from resources.test_support.sync_decorators import sync_configure_oet,time_it
from resources.test_support.controls_low import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,take_subarray,restart_subarray
import pytest
from tmc_helpers_low import compose_sub, configure_sub, release_resources, end
#SUT dependencies
#from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish

DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True


LOGGER = logging.getLogger(__name__)

devices_to_log = [
    'ska_low/tm_subarray_node/1',
    'ska_low/tm_leaf_node/mccs_subarray01',
    'low-mccs/subarray/01']

non_default_states_to_check = {}

@pytest.fixture
def result():
    return {}

# @pytest.mark.select
@pytest.mark.skalow
#@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
# TODO: Need to change when feature file will be created.
@scenario("1_XR-13_XTP-494.feature", "A2-Test, Sub-array transitions from IDLE to READY state")
def test_configure_subarray():
    """Configure Subarray."""

@given("I am accessing the console interface for the OET")
def start_up():
    LOGGER.info("Given I am accessing the console interface for the OET")
    LOGGER.info("Check whether telescope is in StandBy")
    assert(telescope_is_in_standby())
    LOGGER.info("Starting up telescope")
    set_telescope_to_running()
    wait_before_test(timeout=20)
    LOGGER.info("Telescope is in ON state")

# TODO: Need to update given clause
@given("sub-array is in IDLE state")
def assign(result):
    LOGGER.info("Allocating resources to Low Subarray 1")
    compose_sub()
    LOGGER.info("Subarray 1 is ready and composed out of 2 dishes")

# TODO: Need to update when clause
@when("I call the configure scan execution instruction")
def config(result):
    @log_it('AX-13_A2',devices_to_log,non_default_states_to_check)
    @sync_configure_oet
    @time_it(120)
    def test_SUT():
        configure_sub()
    test_SUT()
    LOGGER.info("Configure command on Subarray 1 is successful")

# TODO: Need to update then clause
@then("sub-array is in READY state for which subsequent scan commands can be directed to deliver a basic imaging outcome")
def check_state():
    LOGGER.info("Checking the results")
    # check that the TMC report subarray as being in the obsState = READY
    assert_that(resource('ska_low/tm_subarray_node/1').get('obsState')).is_equal_to('READY')
    # check that the MCCS report subarray as being in the obsState = READY
    assert_that(resource('low-mccs/subarray/01').get('obsState')).is_equal_to('READY')
    LOGGER.info("Results OK")


def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_low/tm_subarray_node/1').get('State') == "ON"):
        #this means there must have been an error
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "IDLE"):
            LOGGER.info("tearing down composed subarray (IDLE)")
            release_resources()
    if (resource('ska_low/tm_subarray_node/1').get('obsState') == "READY"):
        #this means test must have passed
        LOGGER.info("tearing down configured subarray (READY)")
        end()
        release_resources()
        LOGGER.info("EndSb and ReleaseResources is involked on Subarray 1")
    if (resource('ska_low/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
        LOGGER.warn("Subarray is still in configuring! Please restart MVP manualy to complete tear down")
        restart_subarray(1)
        #raise exception since we are unable to continue with tear down
        raise Exception("Unable to tear down test setup")
    LOGGER.info("Put Telescope back to standby")
    set_telescope_to_standby()
    LOGGER.info("Telescope is in standby")

