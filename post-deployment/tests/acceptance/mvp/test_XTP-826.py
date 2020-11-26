#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-826
----------------------------------
Acceptance tests for MVP.
"""
import os
import logging
import pytest
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
# SUT import
from ska.scripting.domain import SubArray

# local imports
from resources.test_support.helpers import resource
from resources.test_support.logging_decorators import log_it
from resources.test_support.controls import set_telescope_to_standby, set_telescope_to_running
from resources.test_support.controls import telescope_is_in_standby, take_subarray

DEVICES_TO_LOG = [
    'ska_mid/tm_subarray_node/1',
    'mid_csp/elt/subarray_01',
    'mid_csp_cbf/sub_elt/subarray_01',
    'mid_sdp/elt/subarray_1',
    'mid_d0001/elt/master',
    'mid_d0002/elt/master',
    'mid_d0003/elt/master',
    'mid_d0004/elt/master']
NON_DEFAULT_DEVICES_TO_CHECK = {
    'mid_d0001/elt/master': 'pointingState',
    'mid_d0002/elt/master': 'pointingState',
    'mid_d0003/elt/master': 'pointingState',
    'mid_d0004/elt/master': 'pointingState'}


DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True
# by default these tests are disabled


# used as labels within the result fixture
# this should be refactored at some point to something more elegant
SUT_EXECUTED = 'SUT executed'
TEST_PASSED = 'Test Passed'
SUBARRAY_USED = "subarray"


@pytest.fixture(name="result")
def fixture_result():
    """structure used to hold details of the intermediate result at each stage of the test"""
    fixture = {SUT_EXECUTED: False, TEST_PASSED: True, SUBARRAY_USED: None}
    yield fixture
    # teardown
    end(fixture)


def get_subarray_state():
    """return the current state of the subarray"""
    return resource('ska_mid/tm_subarray_node/1').assert_attribute('State')


def subarray_is_in_state(expected_state):
    """confirtm the subarray is in a given state"""
    get_subarray_state().equals(expected_state)


def check_resource_ready(resource_name):
    "check that for the passed in resource name the reported obsState is READY"
    obstate = resource(resource_name).get('obsState')
    assert_that(obstate == 'READY')
    msg = resource_name + " obsState :" + obstate
    logging.info(msg)


LOGGER = logging.getLogger(__name__)

@pytest.mark.select
@pytest.mark.skamid
#@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabled by local env")
@scenario("XTP-826.feature", "Run more than one scan on a sub array")
def test_multi_scan():
    """Multiscan Test."""


@given('a running telescope upon which a previously scan has successfully run')
def setup_telescope_and_scan(result):
    """
    confirm the telescope is ready, and then to be sure we are testing a multiscan scenario
    perform one scan
    """
    assert telescope_is_in_standby(
    ), f"Test failed as telescope state is {get_subarray_state().value}"
    set_telescope_to_running()

    LOGGER.info("Ensuring resources are assigned")
    result[SUBARRAY_USED],result['sdp_block'] = take_subarray(1).to_be_composed_out_of(2)
    LOGGER.info("Result of Subarray command is :" + str(result[SUBARRAY_USED]) + str(result['sdp_block']))

    LOGGER.info("configuring for first scan")
    result[SUBARRAY_USED].and_configure_scan_by_file(result['sdp_block'], file='resources/test_data/OET_integration/configure1.json',)

    LOGGER.info("executing first scan")
    result[SUBARRAY_USED].and_run_a_scan()
    return result


@given('I have configured it again')
def configure_again(result):
    """
    reconfigure the telescope for a new scan
    assuming this scenario includes a reconfiguration of the source from
    what was done for the previous scan
    """
    LOGGER.info("Configuring  second scan")
    result[SUBARRAY_USED].and_configure_scan_by_file(
        result['sdp_block'],file='resources/test_data/OET_integration/configure2.json')
    LOGGER.info("________SDP_block for second configure command______" + str(result['sdp_block']))


@when('I run the scan again')
def execute_second_scan(result):
    """
    execute the configured scan - this is the key part of this test
    """
    LOGGER.info("Executing second scan")
    #####################SUT is execucted#################
    # @log_it('XTP-826', DEVICES_TO_LOG, NON_DEFAULT_DEVICES_TO_CHECK)
    def scan():
        SubArray(1).scan()
    scan()
    #############################################
    result[SUT_EXECUTED] = True


@then('the scan should complete without any errors or exceptions')
def check_completion_state(result):
    """
    interpreted as the TMC subarry, csp and sdp report subarray as being in the obsState = READY
    if we got to this point it means we didnt have any exceptions
    """
    LOGGER.info("checking completion status")

    check_resource_ready('ska_mid/tm_subarray_node/1')
    check_resource_ready('mid_csp/elt/subarray_01')
    check_resource_ready('mid_sdp/elt/subarray_1')

    result[TEST_PASSED] = True


def end(result):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    LOGGER.info("End of test: Resetting Telescope")
    if result[SUBARRAY_USED] is not None:
        LOGGER.info("Resetting subarray")
        result[SUBARRAY_USED].reset()
    if resource('ska_mid/tm_subarray_node/1').get("obsState") == "IDLE":
        LOGGER.info("Release all resources assigned to subarray")
        take_subarray(1).and_release_all_resources()
    if telescope_is_in_standby():
        LOGGER.info("Telescope is in STANDBY")
    else:
        LOGGER.info("Resetting telescope to STANDBY")
        set_telescope_to_standby()
