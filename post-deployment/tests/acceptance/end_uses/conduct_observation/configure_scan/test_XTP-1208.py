#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""
import random
import signal
import tango
import time
from datetime import date,datetime
from random import choice
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
from  time  import sleep
import logging
import os
import json
#local dependencies
from resources.test_support.helpers_low import resource, watch, waiter, wait_before_test
from resources.test_support.persistance_helping import update_scan_config_file, load_config_from_file
from resources.test_support.sync_decorators_low import sync_configure
from resources.test_support.controls_low import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,restart_subarray, to_be_composed_out_of, configure_by_file, take_subarray, restart_subarray_low
import pytest
from resources.test_support.tmc_helpers_low import compose_sub, configure_sub, release_resources, end
from ska.scripting.domain import Telescope, SubArray
import resources.test_support.tmc_helpers_low as tmc


DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True

LOGGER = logging.getLogger(__name__)
TIMEOUT = 10000


devices_to_log = [
    'ska_low/tm_subarray_node/1',
    'ska_low/tm_leaf_node/mccs_subarray01',
    'low-mccs/subarray/01']

non_default_states_to_check = {}

@pytest.fixture
def result():
    return {}

@pytest.mark.skalow
@pytest.mark.quarantine
# @pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="deployment is not ready for SKALow")
@scenario("XTP-1208.feature", "TMC and MCCS subarray transitions from IDLE to READY state")
def test_configure_subarray():
    """Configure Subarray."""

@given("A running telescope for executing observations on a subarray")
def start_up():
    LOGGER.info("Given A running telescope for executing observations on a subarray")
    LOGGER.info("Check whether telescope is in StandBy")
    # if not telescope_is_in_standby():
    set_telescope_to_standby()
    assert(telescope_is_in_standby())
    LOGGER.info("Starting up telescope")
    CentralNodeLow = tango.DeviceProxy("ska_low/tm_central/central_node")
    LOGGER.info(
        "Before Sending StartupTelescope command on CentralNodeLow state :"
        + str(CentralNodeLow.State())
    )
    CentralNodeLow.set_timeout_millis(10000)

    start_time = time.time()
    sleep_time = 5
    while True:
        try:
            if CentralNodeLow.State() == tango.DevState.ON:
                break
        except Exception as ex: 
            LOGGER.error("CentralNodeLow State problem")

        try:
            LOGGER.info("CentralNodeLow State:" + str(CentralNodeLow.State()))
        except Exception as ex: 
            LOGGER.error("CentralNodeLow State problem")
        
        try:
            if CentralNodeLow.State() == tango.DevState.FAULT:
                CentralNodeLow.Reset()
                time.sleep(sleep_time)
                continue
        except Exception as ex: 
            LOGGER.error("CentralNodeLow Reset problem")
            time.sleep(sleep_time)
            continue

        try:
            CentralNodeLow.StartUpTelescope()
            time.sleep(sleep_time)
        except Exception as ex: 
             LOGGER.error("CentralNodeLow StartUpTelescope problem")

        if((time.time() - start_time) > TIMEOUT):
            break

    wait_before_test(timeout=5)
    LOGGER.info("CentralNodeLow State:" + str(CentralNodeLow.State()))

@given("Subarray is in IDLE state")
def assign(result):
    LOGGER.info("Allocating resources to Low Subarray 1")
    # to_be_composed_out_of()
    resource("ska_low/tm_subarray_node/1").assert_attribute("State").equals("ON")
    resource("ska_low/tm_subarray_node/1").assert_attribute("obsState").equals("EMPTY")
    assign_resources_file = (
        "resources/test_data/TMC_integration/mccs_assign_resources.json"
    )
    config = load_config_from_file(assign_resources_file)
    CentralNodeLow = tango.DeviceProxy("ska_low/tm_central/central_node")
    CentralNodeLow.set_timeout_millis(10000)
    CentralNodeLow.AssignResources(config)
    wait_before_test(timeout=15)
    LOGGER.info("Invoked AssignResources on CentralNodeLow")
    LOGGER.info("CentralNodeLow State:" + str(CentralNodeLow.State()))
    LOGGER.info("Subarray 1 is ready")

@when("I call the configure scan execution instruction")
def config(result):
    def test_SUT():
        # configure_by_file()
        configure1_file = "resources/test_data/TMC_integration/mccs_configure.json"
        config = load_config_from_file(configure1_file)
        LOGGER.info("Configuring a scan for subarray 1")
        SubarrayNode = tango.DeviceProxy("ska_low/tm_subarray_node/1")
        SubarrayNode.set_timeout_millis(10000)
        for _ in range(10):
            try:
                SubarrayNode.Configure(config)
                LOGGER.info("Configure command on Subarray 1 is successful")
                break
            except:
                LOGGER.error("SubarrayNode.Configure problem")
            wait_before_test(timeout=15)
    test_SUT()
    

@then("Subarray is in READY state for which subsequent scan commands can be directed to deliver a basic imaging outcome")
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
    subarray=SubArray(1)
    if (resource('ska_low/tm_subarray_node/1').get('State') == "ON"):
        #this means there must have been an error
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "IDLE"):
            LOGGER.info("tearing down composed subarray (IDLE)")
            # subarray.deallocate() #TODO: Once the OET latest charts are available this can be reverted
            tmc.release_resources()
    if (resource('ska_low/tm_subarray_node/1').get('obsState') == "READY"):
        #this means test must have passed
        LOGGER.info("tearing down configured subarray (READY)")
        # take_subarray(1).and_end_sb_when_ready()
        SubarrayNodeLow = tango.DeviceProxy("ska_low/tm_subarray_node/1")
        SubarrayNodeLow.set_timeout_millis(10000)
        SubarrayNodeLow.End()
        LOGGER.info("End is invoked on Subarray 1")
        # subarray.deallocate() #TODO: Once the OET latest charts are available this can be reverted
        tmc.release_resources()
        LOGGER.info("ReleaseResources is invoked on Subarray 1")
    if (resource('ska_low/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
        LOGGER.warn("Subarray is still in configuring! Please restart MVP manualy to complete tear down")
        restart_subarray_low(1)
        #raise exception since we are unable to continue with tear down
        raise Exception("Unable to tear down test setup")
    LOGGER.info("Put Telescope back to standby")
    set_telescope_to_standby()
    LOGGER.info("Telescope is in standby")

