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
from pytest_bdd import scenario, parsers, given, when, then


#SUT
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
import oet.observingtasks as observingtasks
#SUT infrastructure
from tango import DeviceProxy, DevState
## local imports
from resources.test_support.helpers import resource
from resources.test_support.logging_decorators import log_it
from resources.test_support.sync_decorators import sync_assign_resources
from resources.test_support.persistance_helping import update_resource_config_file,and_configuring_by_file
from resources.test_support.controls import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,take_subarray


DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True

SUBARRAY_STATE = 'Subarray State'

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
def fixture():
    return {}

def assign():
    assert(telescope_is_in_standby())
    set_telescope_to_running()
    pilot, sdp_block = take_subarray(1).to_be_composed_out_of(2)
    return sdp_block

def configuring(sdp_block):
    take_subarray(1).and_configuring_by_file(sdp_block)
    LOGGER.info("Configure is invoke on Subarray")

def configure_ready(sdp_block):
    take_subarray(1).and_configure_scan_by_file(sdp_block)
    LOGGER.info("Configure is invoke on Subarray")
    LOGGER.info("Subarray is moved to READY")

def scanning(fixture):
    #TODO add method to clear thread in case of failure
    fixture['scans'] = '{"id":1}'
    @log_it('AX-13_A3',devices_to_log,non_default_states_to_check)
    @sync_scan_oet
    def scan():
        def send_scan(duration):
            SubArray(1).scan()
        LOGGER.info("Scan is invoked on Subarray 1")
        executor = futures.ThreadPoolExecutor(max_workers=1)
        return executor.submit(send_scan,fixture['scans'])
    fixture['future'] = scan()
    return fixture

  
@pytest.mark.select
# @pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
@scenario("feature file tobe added", "to be added, when the telescope subarrays can be aborted then abort brings them in ABORTED")
def abort_subarray():
   """Abort subarray"""

@given(parsers.parse('operator John has a running telescope with a subarray in state {subarray_state:S}'))
@given('operator John has a running telescope with a subarray in state <subarray_state>)
def set_up_telescope(subarray_state : str):
    if subarray_state == 'IDLE':
        assign()
    elif subarray_state == 'CONFIGURING':
        sdp_block = assign()
        configuring(sdp_block)
    elif subarray_state == 'READY':
        sdp_block = assign()
        configure_ready(sdp_block)
    elif subarray_state == 'SCANNING':
        sdp_block = assign()
        scanning(sdp_block)
    else:
        msg = 'obsState {} is not settable with command methods'
        raise ValueError(msg.format(subarray_state))

@when("when operator issues the ABORT command")
def abort_subarray():
    @log_it('AX-13_A1',devices_to_log,non_default_states_to_check)
    @sync_abort(200)
    def abort():
        SubArray(1).abort()
        LOGGER.info("Abort is invoked on Subarray")

@then("the subarray eventually goes into ABORTING")
def check_state_aborting():
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('ABORTING')
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('ABORTING')
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('ABORTING')

@then("the subarray eventually goes into ABORTED")
def check_state_aborted():
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('ABORTED')
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('ABORTED')
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('ABORTED')

def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_mid/tm_subarray_node/1').get('State') == "ON"):
        if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "IDLE"):
            LOGGER.info("tearing down composed subarray (IDLE)")
            take_subarray(1).and_release_all_resources()
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
        LOGGER.warn("Subarray is still in CONFIFURING! Please restart MVP manualy to complete tear down")
        restart_subarray(1)
        #raise exception since we are unable to continue with tear down
        raise Exception("Unable to tear down test setup")  
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "READY"):
        LOGGER.info("tearing down configured subarray (READY)")
        take_subarray(1).and_end_sb_when_ready().and_release_all_resources()
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "SCANNING"):
        LOGGER.warn("Subarray is still in SCANNING! Please restart MVP manualy to complete tear down")
        restart_subarray(1)
        #raise exception since we are unable to continue with tear down
        raise Exception("Unable to tear down test setup")
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "ABORTING"):
        LOGGER.warn("Subarray is still in ABORTING! Please restart MVP manualy to complete tear down")
        restart_subarray(1)
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "ABORTED"):
        invoke_restart_on_subarray(1)
    LOGGER.info("Put Telescope back to standby")
    set_telescope_to_standby()



                    



