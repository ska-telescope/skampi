#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-826
----------------------------------
Acceptance tests for MVP.
"""
import logging
import pytest
from functools import partial
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then, parsers
from tango import DeviceProxy
#SUT import
from oet.domain import SubArray

## local imports
from resources.test_support.helpers import resource, watch
from resources.test_support.persistance_helping import update_resource_config_file
from resources.test_support.logging_decorators import log_it
from resources.test_support.sync_decorators import sync_scan_oet
from resources.test_support.controls import set_telescope_to_standby, set_telescope_to_running, telescope_is_in_standby, take_subarray

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


@pytest.fixture()
def result():
    fixture = {'SUT executed':False,"Test Passed":True,"subarray":None}
    yield fixture
    ##teard down
    end(fixture)

def get_subarray_state():
    return resource('ska_mid/tm_subarray_node/1').assert_attribute('State')

def subarray_is_in_state(expected_state):
    get_subarray_state().equals(expected_state)



LOGGER = logging.getLogger(__name__)
@scenario("../../../features/XTP-826.feature", "Run more than one scan on a sub array")
def test_multi_scan():
    """Multiscan Test."""
    pass

@given('a running telescope upon which a previously scan has successfully run')
def setup_telescope_and_scan(result):

    assert  telescope_is_in_standby(), f"Test failed as telescope state is {get_subarray_state().value}"
    set_telescope_to_running()

    LOGGER.info("Ensuring resources are assigned")
    result['subarray'] = take_subarray(1).to_be_composed_out_of(2)

    LOGGER.info("configuring for first scan")
    result['subarray'].and_configure_scan_by_file(file = 'resources/test_data/TMC_integration/configure1.json')

    LOGGER.info("executing first scan")
    result['subarray'].and_run_a_scan()
    return result

@given('I have configured it again')
def configure_again(result):
    LOGGER.info("Configuring  second scan")
    result['subarray'].and_configure_scan_by_file(file = 'resources/test_data/TMC_integration/configure2.json')

@when('I run the scan again')
def configure_second_scan(result):

    LOGGER.info("Executing second scan")
    #####################SUT is execucted#################
    @log_it('XTP-826',devices_to_log,non_default_states_to_check)
    def scan():
        SubArray(1).scan()
    scan()
    #############################################
    result['SUT executed'] = True

# we may not even have to put in this checks since implicitly if we got to this point it means we didnt had any exceptions
@then('the scan should complete without any errors or exceptions')
def check_completion_state(result):
    LOGGER.info("checking completion status")
    # check that the TMC report subarray as being in the obsState = READY
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('READY')
    logging.info("TMC-subarray obsState: " + resource('ska_mid/tm_subarray_node/1').get("obsState"))
    # check that the CSP report subarray as being in the obsState = READY
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('READY')
    logging.info("CSP-subarray obsState: " + resource('mid_csp/elt/subarray_01').get("obsState"))
    # check that the SDP report subarray as being in the obsState = READY
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('READY')
    logging.info("SDP-subarray obsState: " + resource('mid_sdp/elt/subarray_1').get("obsState"))
    result['test passed'] = True

def end(result):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    LOGGER.info("End of test: Resetting Telescope")
    if result['subarray'] is not None:
        LOGGER.info("Resetting subarray")
        result['subarray'].reset()
    if (resource('ska_mid/tm_subarray_node/1').get("State") == "ON"):
        LOGGER.info("Release all resources assigned to subarray")
        take_subarray(1).and_release_all_resources()
    if telescope_is_in_standby():
        LOGGER.info("Telescope is in STANDBY")
    else:
        LOGGER.info("Resetting telescope to STANDBY")
        set_telescope_to_standby()