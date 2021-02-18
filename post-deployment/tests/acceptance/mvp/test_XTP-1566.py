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
from resources.test_support.sync_decorators_low import sync_scan_oet,sync_configure_oet, sync_scan, sync_abort, time_it
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

@pytest.mark.skip(reason="no way of currently testing this")
# @pytest.mark.skalow
# @pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="deployment is not ready for SKALow")
@scenario("XTP-1566.feature", "BDD test case for Abort functionality in MVP Low")
def test_subarray_abort():
    """Abort Operation"""

@given("Subarray is in ON state")
def start_up():
    LOGGER.info("Check whether telescope is in StandBy")
    assert(telescope_is_in_standby())
    LOGGER.info("Starting up telescope")
    set_telescope_to_running()
    wait_before_test(timeout=20)

@given("operator has a running low telescope with a subarray in obsState <subarray_obsstate>")
def set_up_telescope(subarray_obsstate : str):
    start_up()

    tmc.compose_sub()
    LOGGER.info("AssignResources is invoked on Subarray")
    wait_before_test(timeout=10)

    tmc.configure_sub()
    LOGGER.info("Configure is invoke on Subarray")
    wait_before_test(timeout=10)
    
    if subarray_obsstate == 'SCANNING':
        tmc.scan_sub()
        LOGGER.info("Scan is invoked on Subarray")
        wait_before_test(timeout=10)

    else:
        msg = 'obsState {} is not settable with command methods'
        raise ValueError(msg.format(subarray_obsstate))

@when("Operator issues the ABORT command")
def abort_subarray():
    @sync_abort(200)
    def abort():
        SubarrayNodeLow = DeviceProxy('ska_low/tm_subarray_node/1')
        SubarrayNodeLow.Abort()
        LOGGER.info("Abort command is invoked on subarray")
    abort()

@then("The subarray eventually transitions into obsState ABORTED")
def check_state():
    LOGGER.info("Checking the results")
    # check that the TMC and MCCS report subarray as being in the obsState = ABORTING
    # assert_that(resource('ska_low/tm_subarray_node/1').get('obsState')).is_equal_to('ABORTING')
    # assert_that(resource('low-mccs/subarray/01').get('obsState')).is_equal_to('ABORTING')
     # check that the TMC and MCCS report subarray as being in the obsState = ABORTED
    assert_that(resource('ska_low/tm_subarray_node/1').get('obsState')).is_equal_to('ABORTED')
    assert_that(resource('low-mccs/subarray/01').get('obsState')).is_equal_to('ABORTED')
    LOGGER.info("Results OK")

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
            restart_subarray(1)
            #raise exception since we are unable to continue with tear down
            raise Exception("Unable to tear down test setup")
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "SCANNING"):
            LOGGER.warn("Subarray is still in SCANNING! Please restart MVP manualy to complete tear down")
            restart_subarray(1)
            #raise exception since we are unable to continue with tear down
            raise Exception("Unable to tear down test setup")
        if(resource('ska_low/tm_subarray_node/1').get('obsState') == "ABORTING"):
            LOGGER.warn("Subarray is still in ABORTING! Please restart MVP manualy to complete tear down")
            restart_subarray(1)
        if(resource('ska_low/tm_subarray_node/1').get('obsState') == "ABORTED"):
            LOGGER.info("tearing down configured subarray (ABORTED)")
            tmc.obsreset_sub()
            LOGGER.info('Invoked ObsReset on Subarray')
            tmc.release_resources()
            LOGGER.info('Invoked ReleaseResources on Subarray')
            wait_before_test(timeout=10)