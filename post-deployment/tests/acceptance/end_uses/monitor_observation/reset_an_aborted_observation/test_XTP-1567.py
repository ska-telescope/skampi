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
from tango import DeviceProxy, DevState # type: ignore
## local imports
from resources.test_support.helpers_low import resource, wait_before_test
from resources.test_support.sync_decorators_low import sync_obsreset, sync_scan, sync_abort
from resources.test_support.persistance_helping import load_config_from_file
from resources.test_support.controls_low import set_telescope_to_standby, set_telescope_to_running, telescope_is_in_standby, restart_subarray_low, to_be_composed_out_of, configure_by_file, take_subarray
import resources.test_support.tmc_helpers_low as tmc
from ska.scripting.domain import Telescope, SubArray
from concurrent import futures

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

subarray=SubArray(1)

@pytest.fixture
def result():
    return {}

@pytest.mark.skalow
@pytest.mark.quarantine
@pytest.mark.obsreset
@scenario("XTP-1567.feature", "BDD test case for ObsReset command in MVP Low")
def test_subarray_obsreset():
    """reset subarray"""

def assign():
    LOGGER.info("Given A running telescope for executing observations on a subarray")
    #Added timeout of 10 sec to wait tmc_low subarray to become OFF
    wait_before_test(timeout=10)
    assert(telescope_is_in_standby())
    LOGGER.info("Starting up telescope")
    set_telescope_to_running()
    wait_before_test(timeout=10)
    to_be_composed_out_of()
    LOGGER.info("AssignResources is invoked on Subarray")
    wait_before_test(timeout=10)

def config():
    def test_SUT():
        configure_by_file()
    test_SUT()
    LOGGER.info("Configure command on Subarray 1 is successful")

# def scanning(fixture):
#     @sync_scan(200)
#     def scan():
#         def send_scan():
#            subarray.scan()
#         LOGGER.info("Scan is invoked on Subarray 1")
#         executor = futures.ThreadPoolExecutor(max_workers=1)
#         return executor.submit(send_scan)
#     fixture['future'] = scan()
#     return fixture
    # tmc.configure_sub()
    # LOGGER.info("Configure is invoked on Subarray")
    # wait_before_test(timeout=10)

    # scan_file = 'resources/test_data/TMC_integration/mccs_scan.json'
    # scan_string = load_config_from_file(scan_file)
    # SubarrayNodeLow = DeviceProxy('ska_low/tm_subarray_node/1')
    # SubarrayNodeLow.Scan(scan_string)
    # LOGGER.info("Scan is invoked on Subarray")

    # SubarrayNodeLow.Abort()
    # LOGGER.info("Abort is invoked on Subarray")
    # wait_before_test(timeout=10)
@given("operator has a running telescope with a subarray in state <subarray_obsstate> and Subarray has transitioned into obsState ABORTED")
def set_up_telescope(subarray_obsstate : str):
    if subarray_obsstate == 'IDLE':
        assign()
        LOGGER.info("Abort command can be invoked on Subarray with Subarray obsState as 'IDLE'")
    elif subarray_obsstate == 'READY':
        assign()
        config()
        LOGGER.info("Abort command can be invoked on Subarray with Subarray obsState as 'READY'")
    # elif subarray_obsstate == 'SCANNING':
    #     assign()
    #     LOGGER.info("Resources are assigned successfully and configuring the subarray now")
    #     config()
    #     LOGGER.info("Subarray is configured and executing a scan on subarray")
        #scanning(fixture)
    #     def scanning(fixture):
    #     @sync_scan(200)
    #         def scan():
    #             def send_scan():
    #                 subarray.scan()
    #         LOGGER.info("Scan is invoked on Subarray 1")
    #         executor = futures.ThreadPoolExecutor(max_workers=1)
    #         return executor.submit(send_scan)
    #     fixture['future'] = scan()
    # return fixture
        # LOGGER.info("Abort command can be invoked on Subarray with Subarray obsState as 'SCANNING'")
    else:
        msg = 'obsState {} is not settable with command methods'
        raise ValueError(msg.format(subarray_obsstate))
        
    def abort_subarray():
        @sync_abort(200)
        def abort():
            LOGGER.info("Invoking ABORT command.")
            subarray.abort()
            #take_subarray(1).reset_when_aborted()
            LOGGER.info("Abort command is invoked on subarray")
        abort()
        LOGGER.info("Abort is completed on Subarray")
    abort_subarray()


@when("the operator invokes ObsReset command")
def reset_subarray():
   
    @sync_obsreset(200)
    def obsreset_subarray():
        subarray.reset()
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
            subarray.deallocate()
            LOGGER.info('Invoked ReleaseResources on Subarray')
            wait_before_test(timeout=10)
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "READY"):
            LOGGER.info("tearing down configured subarray (READY)")
            subarray.end()
            resource('ska_low/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
            LOGGER.info('Invoked End on Subarray')
            wait_before_test(timeout=10)
            subarray.deallocate()
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
        LOGGER.info("Telescope is in standBy")
