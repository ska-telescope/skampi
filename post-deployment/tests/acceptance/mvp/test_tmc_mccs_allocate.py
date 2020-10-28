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
from pytest_bdd import scenario, given, when, then


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
# import oet
import pytest
# from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from tango import DeviceProxy, DevState
# from resources.test_support.helpers import  obsState, resource, watch, waiter, map_dish_nr_to_device_name
from resources.test_support.helpers_low import resource, watch, waiter, wait_before_test
from resources.test_support.logging_decorators import log_it
import logging
from resources.test_support.persistance_helping import load_config_from_file
# from resources.test_support.controls import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,take_subarray,restart_subarray
from resources.test_support.controls_low import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,restart_subarray,sync_assign_resources
from resources.test_support.sync_decorators import  sync_scan_oet,sync_configure_oet,time_it
from resources.test_support.tmc_helpers_low import compose_sub
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


@pytest.fixture
def result():
    return {}

@pytest.mark.select
#@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
@scenario("1_XR-13_XTP-494.feature", "A1-Test, Sub-array resource allocation")
def test_allocate_resources():
    """Assign Resources."""

@given("A running telescope for executing observations on a subarray")
def set_to_running():
    LOGGER.info("Given A running telescope for executing observations on a subarray")
    assert(telescope_is_in_standby())
    LOGGER.info("Starting up telescope")
    set_telescope_to_running()

@when("I allocate 4 dishes to subarray 1")
def allocate_four_dishes():

    # LOGGER.info("When I allocate 2 dishes to subarray 1")
    ##############################
    # @log_it('AX-13_A1',devices_to_log,non_default_states_to_check)
    # @sync_assign_resources(2,150)
    # def test_SUT():
        # cdm_file_path = 'resources/test_data/OET_integration/example_allocate.json'
        # LOGGER.info("cdm_file_path :" + str(cdm_file_path))
        # update_resource_config_file(cdm_file_path)
        # dish_allocation = ResourceAllocation(dishes=[Dish(1), Dish(2)])
        # LOGGER.info("dish_allocation :" + str(dish_allocation))
        # subarray = SubArray(1)
        # LOGGER.info("Allocate Subarray is :" + str(subarray))
    # return compose_sub()
    # LOGGER.info("AssignResource command is invoked")
    # result['response'] = test_SUT()
    # LOGGER.info("Result of test_SUT : " + str(result))
    # LOGGER.info("Result response of test_SUT : " + str(result['response']))
    # ##############################
    @sync_assign_resources(150)
    def compose_sub():
        resource('ska_low/tm_subarray_node/1').assert_attribute('State').equals('ON')
        resource('ska_low/tm_subarray_node/1').assert_attribute('obsState').equals('EMPTY')
        assign_resources_file = 'resources/test_data/TMC_integration/mccs_assign_resources.json'
        config = load_config_from_file(assign_resources_file)
        CentralNode = DeviceProxy('ska_low/tm_central/central_node')
        CentralNode.AssignResources(config)
        LOGGER.info('Invoked AssignResources on CentralNode')

    compose_sub()
    LOGGER.info("AssignResource command is executed successfully")
    return result

# @then("I have a subarray composed of 4 dishes")
# def check_subarray_composition(result):
#
#     #check that there was no error in response
#     assert_that(result['response']).is_equal_to(ResourceAllocation(dishes=[Dish(1), Dish(2)]))
#     #check that this is reflected correctly on TMC side
#     assert_that(resource('ska_mid/tm_subarray_node/1').get("receptorIDList")).is_equal_to((1, 2))
#     #check that this is reflected correctly on CSP side
#     assert_that(resource('mid_csp/elt/subarray_01').get('assignedReceptors')).is_equal_to((1, 2))
#     #assert_that(resource('mid_csp/elt/master').get('receptorMembership')).is_equal_to((1, 1,))
#     #TODO need to find a better way of testing sets with sets
#     #assert_that(set(resource('mid_csp/elt/master').get('availableReceptorIDs'))).is_subset_of(set((4,3)))
#     #check that this is reflected correctly on SDP side - no code at the current implementation
#     LOGGER.info("Then I have a subarray composed of 2 dishes: PASSED")


@then("the subarray is in the condition that allows scan configurations to take place")
def check_subarry_state():
    #check that the TMC report subarray as being in the ON state and obsState = IDLE
    assert_that(resource('ska_low/tm_subarray_node/1').get("State")).is_equal_to("ON")
    #assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('RESOURCING')
    assert_that(resource('ska_low/tm_subarray_node/1').get('obsState')).is_equal_to('IDLE')
    #check that the CSP report subarray as being in the ON state and obsState = IDLE
    assert_that(resource('low-mccs/subarray/01').get('State')).is_equal_to('ON')
    assert_that(resource('low-mccs/subarray/01').get('obsState')).is_equal_to('IDLE')
    # #check that the SDP report subarray as being in the ON state and obsState = IDLE
    # assert_that(resource('mid_sdp/elt/subarray_1').get('State')).is_equal_to('ON')
    # assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('IDLE')
    LOGGER.info("Then the subarray is in the condition that allows scan configurations to take place: PASSED")

def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_low/tm_subarray_node/1').get("obsState") == "IDLE"):
        LOGGER.info("Release all resources assigned to subarray")
        # take_subarray(1).and_release_all_resources()
        tmc.release_resources()
        LOGGER.info("ResourceIdList is empty for Subarray 1 ")
    LOGGER.info("Put Telescope back to standby")
    set_telescope_to_standby()
    LOGGER.info("Telescope is in standby")

