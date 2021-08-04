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
from concurrent import futures
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
# SUT
#SUT infrastructure
from tango import DeviceProxy # type: ignore
from ska.scripting.domain import SubArray

## local imports
from resources.test_support.helpers_low import resource, wait_before_test
from resources.test_support.controls_low import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,restart_subarray_low, to_be_composed_out_of, configure_by_file, take_subarray
from resources.test_support.sync_decorators_low import sync_abort, sync_scan, sync_scanning_oet
import resources.test_support.tmc_helpers_low as tmc
from resources.test_support.persistance_helping import load_config_from_file
from ska.scripting.domain import Telescope, SubArray


DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def fixture():
    return {}

devices_to_log = [
    'ska_low/tm_subarray_node/1',
    'low-mccs/control/control',
    'low-mccs/subarray/01']
non_default_states_to_check = {}

subarray=SubArray(1)

@pytest.mark.skalow
@pytest.mark.quarantine
@scenario("XTP-1566.feature", "when the telescope subarrays can be aborted then Abort brings them in ABORTED observation state in MVP Low")
def test_subarray_abort_obsreset():
    """Abort Operation"""

def assign():
    LOGGER.info(
        "Before starting the telescope checking if the telescope is in StandBy."
    )
    assert telescope_is_in_standby()
    LOGGER.info("Telescope is in StandBy.")
    LOGGER.info("Invoking Startup Telescope command on the telescope.")
    set_telescope_to_running()
    wait_before_test(timeout=10)
    LOGGER.info("Telescope is started successfully.")
    LOGGER.info("Allocating resources to Low Subarray 1")
    to_be_composed_out_of()
    wait_before_test(timeout=10)
    LOGGER.info("Subarray 1 is ready")


def config():
    def test_SUT():
        configure_by_file()     
    test_SUT()
    LOGGER.info("Configure command on Subarray 1 is successful")
    wait_before_test(timeout=10)

@given("operator has a running low telescope with a subarray in obsState <subarray_obsstate>")
def set_up_telescope(subarray_obsstate : str):
    if subarray_obsstate == "IDLE":
        assign()
        LOGGER.info("Abort command can be invoked on Subarray with Subarray obsState as 'IDLE'")
    elif subarray_obsstate == 'READY':
        assign()
        config()
        LOGGER.info("Abort command can be invoked on Subarray with Subarray obsState as 'READY'")
    elif subarray_obsstate == "SCANNING":
        assign()
        config()
        @sync_scanning_oet
        def scan():
            scan_file = 'resources/test_data/TMC_integration/mccs_scan.json'
            scan_string = load_config_from_file(scan_file)
            SubarrayNodeLow = DeviceProxy('ska_low/tm_subarray_node/1')
            SubarrayNodeLow.Scan(scan_string)
            # subarray.scan()
            LOGGER.info("scan command is called")
        scan()
        LOGGER.info("Subarray OBSSTATE '%s'", resource('ska_low/tm_subarray_node/1').get('obsState'))
        LOGGER.info("Abort command can be invoked on Subarray with Subarray obsState as 'SCANNING'")
    else:
        msg = "obsState {} is not settable with command methods"
        raise ValueError(msg.format(subarray_obsstate))

@when("operator issues the ABORT command")
def abort_subarray():
    @sync_abort(500)
    def abort_subarray():
        subarray.abort()
        LOGGER.info("Abort command is invoked on subarray")
    abort_subarray()

@then("the subarray eventually transitions into obsState ABORTED")
def check_state():
    LOGGER.info("Checking the results")
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
            # subarray.deallocate() #TODO: Once the OET latest charts are available this can be reverted
            tmc.release_resources()
            LOGGER.info('Invoked ReleaseResources on Subarray')
            wait_before_test(timeout=10)
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "READY"):
            LOGGER.info("tearing down configured subarray (READY)")
            # subarray.end()
            take_subarray(1).and_end_sb_when_ready()
            resource('ska_low/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
            LOGGER.info('Invoked End on Subarray')
            wait_before_test(timeout=10)
            # subarray.deallocate() #TODO: Once the OET latest charts are available this can be reverted
            tmc.release_resources()
            LOGGER.info('Invoked ReleaseResources on Subarray')
            wait_before_test(timeout=10)
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
            LOGGER.warn("Subarray is still in CONFIFURING! Please restart MVP manualy to complete tear down")
            restart_subarray_low(1)
            # raise exception since we are unable to continue with tear down
            raise Exception("Unable to tear down test setup")
        if (resource('ska_low/tm_subarray_node/1').get('obsState') == "SCANNING"):
            LOGGER.warn("Subarray is still in SCANNING! Please restart MVP manualy to complete tear down")
            restart_subarray_low(1)
            # raise exception since we are unable to continue with tear down
            raise Exception("Unable to tear down test setup")
        if(resource('ska_low/tm_subarray_node/1').get('obsState') == "ABORTING"):
            LOGGER.warn("Subarray is still in ABORTING! Please restart MVP manualy to complete tear down")
            restart_subarray_low(1)
        if(resource('ska_low/tm_subarray_node/1').get('obsState') == "ABORTED"):
            LOGGER.info("tearing down configured subarray (ABORTED)")
            take_subarray(1).reset_when_aborted()
            LOGGER.info('Invoked ObsReset on Subarray')
            wait_before_test(timeout=10)
            # subarray.deallocate() #TODO: Once the OET latest charts are available this can be reverted
            tmc.release_resources()
            LOGGER.info('Invoked ReleaseResources on Subarray')
            wait_before_test(timeout=10)
        set_telescope_to_standby()
        LOGGER.info("Telescope is in standby")
    else:
        LOGGER.warn("Subarray is in inconsistent state! Please restart MVP manualy to complete tear down")
        restart_subarray_low(1)
