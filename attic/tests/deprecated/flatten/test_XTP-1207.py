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
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
import pytest
from tango import DeviceProxy, DevState
from resources.test_support.helpers_low import resource, watch, waiter, wait_before_test
import logging
from ska.scripting.domain import SubArray
import resources.test_support.tmc_helpers_low as tmc
from resources.test_support.persistance_helping import load_config_from_file
from resources.test_support.controls_low import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,restart_subarray
from resources.test_support.sync_decorators_low import sync_assign_resources

LOGGER = logging.getLogger(__name__)

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


@pytest.fixture
def result():
    return {}

@pytest.mark.quarantine
@pytest.mark.skalow
@pytest.mark.assignr
# @pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="deployment is not ready for SKALow")
@scenario("XTP-1207.feature", "TMC and MCCS subarray resource allocation")
def test_allocate_resources():
    """Assign Resources."""

@given("A running telescope for executing observations on a subarray")
def set_to_running():
    LOGGER.info("Given A running telescope for executing observations on a subarray")
    assert(telescope_is_in_standby())
    LOGGER.info("Starting up telescope")
    set_telescope_to_running()
    wait_before_test(timeout=10)

@when("I allocate resources to TMC and MCCS Subarray")
def allocate_resources_to_subarray():
    @sync_assign_resources(150)
    def compose_sub():
        resource('ska_low/tm_subarray_node/1').assert_attribute('State').equals('ON')
        resource('ska_low/tm_subarray_node/1').assert_attribute('obsState').equals('EMPTY')
        assign_resources_file = 'resources/test_data/OET_integration/mccs_assign_resources.json'
        subarray = SubArray(1)
        LOGGER.info('Subarray has been created.')
        subarray.allocate_from_file(cdm_file=assign_resources_file, with_processing=False)
        LOGGER.info('Invoked AssignResources on CentralNode')

    compose_sub()
    LOGGER.info("AssignResource command is executed successfully")

@then("The TMC and MCCS subarray is in the condition that allows scan configurations to take place")
def check_subarry_state():
    #check that the TMC report SubarrayLow as being in the ON state and obsState = IDLE
    assert_that(resource('ska_low/tm_subarray_node/1').get("State")).is_equal_to("ON")
    assert_that(resource('ska_low/tm_subarray_node/1').get('obsState')).is_equal_to('IDLE')
    #check that the MCCS report subarray as being in the ON state and obsState = IDLE
    assert_that(resource('low-mccs/subarray/01').get('State')).is_equal_to('ON')
    assert_that(resource('low-mccs/subarray/01').get('obsState')).is_equal_to('IDLE')
    LOGGER.info("Then the subarray is in the condition that allows scan configurations to take place: PASSED")

def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_low/tm_subarray_node/1').get("obsState") == "IDLE"):
        LOGGER.info("Release all resources assigned to subarray")
        # subarray = SubArray(1)
        # subarray.deallocate() #TODO: Once the OET latest charts are available this can be reverted
        tmc.release_resources()
        LOGGER.info("ResourceIdList is empty for Subarray 1 ")
    LOGGER.info("Put Telescope back to standby")
    set_telescope_to_standby()
    LOGGER.info("Telescope is in standby")

