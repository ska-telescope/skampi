#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""
import sys, os
import pytest
import logging
from time import sleep
from assertpy import assert_that
from concurrent import futures
from pytest_bdd import scenario, given, when, then


#SUT
from ska.scripting.domain import Telescope, SubArray
#SUT infrastructure
from tango import DeviceProxy, DevState # type: ignore
## local imports
from resources.test_support.helpers import resource
from resources.test_support.sync_decorators import sync_assign_resources, sync_obsreset,sync_abort, sync_scan_oet
from resources.test_support.persistance_helping import update_resource_config_file
from resources.test_support.controls import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,take_subarray,restart_subarray,tmc_is_on


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
@pytest.mark.skamid
@pytest.mark.quarantine
# @pytest.mark.skip(reason="feature not working consistently")
@scenario("XTP-1096.feature", "BDD test case for ObsReset command")
def test_subarray_obsreset():
    """reset subarray"""

def assign():
    LOGGER.info("Before starting the telescope checking if the TMC is in ON state")
    assert(tmc_is_on())
    LOGGER.info("Before starting the telescope checking if the telescope is in StandBy.")
    assert(telescope_is_in_standby())
    LOGGER.info("Telescope is in StandBy.")
    LOGGER.info("Invoking Startup Telescope command on the telescope.")
    set_telescope_to_running()
    LOGGER.info("Telescope is started successfully.")
    pilot, sdp_block = take_subarray(1).to_be_composed_out_of(2)
    LOGGER.info("Resources are assigned successfully on Subarray.")
    return sdp_block


def configure_ready(sdp_block):
    LOGGER.info("Invoking configure command on the Subarray.")
    take_subarray(1).and_configure_scan_by_file(sdp_block)
    LOGGER.info("Configure command is invoked on Subarray.")
    LOGGER.info("Subarray is moved to READY, Configure command is successful on Subarray.")


def scanning(fixture):
    fixture['scans'] = '{"id":1}'
    @sync_scan_oet
    def scan():
        LOGGER.info("Invoking scan command on Subarray.")
        def send_scan(duration):
            SubArray(1).scan()
        LOGGER.info("Scan is invoked on Subarray 1")
        executor = futures.ThreadPoolExecutor(max_workers=1)
        LOGGER.info("Getting into executor block")
        return executor.submit(send_scan,fixture['scans'])
    fixture['future'] = scan()
    LOGGER.info("obsState = Scanning of TMC-Subarray")
    return fixture


@given("operator has a running telescope with a subarray in state <subarray_obsstate> and Subarray has transitioned into obsState ABORTED")
def set_up_telescope(subarray_obsstate : str):
    if subarray_obsstate == 'IDLE':
        assign()
        LOGGER.info("Abort command can be invoked on Subarray with Subarray obsState as 'IDLE'")
    elif subarray_obsstate == 'READY':
        sdp_block = assign()
        LOGGER.info("Resources are assigned successfully and configuring the subarray now")
        configure_ready(sdp_block)
        LOGGER.info("Abort command can be invoked on Subarray with Subarray obsState as 'READY'")
    elif subarray_obsstate == 'SCANNING':
        sdp_block = assign()
        LOGGER.info("Resources are assigned successfully and configuring the subarray now")
        configure_ready(sdp_block)
        LOGGER.info("Subarray is configured and executing a scan on subarray")
        scanning(sdp_block)
        LOGGER.info("Abort command can be invoked on Subarray with Subarray obsState as 'SCANNING'")
    else:
        msg = 'obsState {} is not settable with command methods'
        raise ValueError(msg.format(subarray_obsstate))
        
    def abort_subarray():
        @sync_abort(200)
        def abort():
            LOGGER.info("Invoking ABORT command.")
            SubArray(1).abort()
            LOGGER.info("Abort command is invoked on subarray")
        abort()
        LOGGER.info("Abort is completed on Subarray")
    abort_subarray()

@when("the operator invokes ObsReset command")
def reset_subarray():
    @sync_obsreset(200)
    def obsreset_subarray():
        LOGGER.info("Invoking ObsReset command on the Subarray.")
        SubArray(1).reset()
        LOGGER.info("ObsReset command is invoked on subarray")
    obsreset_subarray()
    LOGGER.info("ObsReset is completed on Subarray.")


@then("the subarray should transition to obsState IDLE")
def check_idle_state():
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('IDLE')
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('IDLE')
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('IDLE')

def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_mid/tm_subarray_node/1').get('State') == "ON"):
        if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "IDLE"):
            LOGGER.info("tearing down composed subarray (IDLE)")
            take_subarray(1).and_release_all_resources()
            LOGGER.info("Resources are deallocated successfully from Subarray.")
        if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
            LOGGER.warn("Subarray is still in CONFIFURING! Please restart MVP manually to complete tear down")
            restart_subarray(1)
            raise Exception("Unable to tear down test setup")  
        if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "READY"):
            LOGGER.info("tearing down configured subarray (READY)")
            take_subarray(1).and_end_sb_when_ready().and_release_all_resources()
        if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "SCANNING"):
            LOGGER.warn("Subarray is still in SCANNING! Please restart MVP manually to complete tear down")
            restart_subarray(1)
            raise Exception("Unable to tear down test setup")
        if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "ABORTING"):
            LOGGER.warn("Subarray is still in ABORTING! Please restart MVP manually to complete tear down")
            restart_subarray(1)
            raise Exception("Unable to tear down test setup")
        if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "ABORTED"):
            take_subarray(1).reset_when_aborted()
            take_subarray(1).and_release_all_resources()
        if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "RESETTING"):
            LOGGER.warn("Subarray is still in RESETTING! Please restart MVP manually to complete tear down")
            restart_subarray(1)
            raise Exception("Unable to tear down test setup")
    LOGGER.info("Put Telescope back to StandBy")
    set_telescope_to_standby()
    LOGGER.info("Telescope StandBy command invoked.")
