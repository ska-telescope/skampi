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
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then


#SUT
from ska.scripting.domain import Telescope, SubArray, ResourceAllocation, Dish
from ska_tmc_cdm.messages.central_node.assign_resources import AssignResourcesRequest
from ska_tmc_cdm.schemas import CODEC as cdm_CODEC
#SUT infrastructure
from tango import DeviceProxy, DevState # type: ignore
## local imports
from resources.test_support.helpers import resource
from resources.test_support.sync_decorators import sync_assign_resources
from resources.test_support.persistance_helping import update_resource_config_file
from resources.test_support.controls import set_telescope_to_standby,set_telescope_to_running,telescope_is_in_standby,take_subarray, tmc_is_on
from resources.test_support.helpers_low import wait_before_test
from resources.test_support.oet_helpers import oet_compose_sub

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
#@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
@scenario("1_XR-13_XTP-494.feature", "A1-Test, Sub-array resource allocation")
def test_allocate_resources():
    """Assign Resources."""

@given("A running telescope for executing observations on a subarray")
def set_to_running():
    LOGGER.info("Before starting the telescope checking if the TMC is in ON state")
    assert(tmc_is_on())
    LOGGER.info("Before starting the telescope checking if the telescope is in StandBy.")
    assert telescope_is_in_standby()
    LOGGER.info("Telescope is in StandBy.")
    LOGGER.info("Invoking Startup Telescope command on the telescope.")
    set_telescope_to_running()
    LOGGER.info("Telescope is started successfully.")

@when("I allocate 4 dishes to subarray 1")
def allocate_four_dishes(result):
    LOGGER.info("Allocating 4 dishes to subarray 1")
    ##############################
    @sync_assign_resources(4, 600)
    def test_SUT():
        res = oet_compose_sub()
        return res     
    result['response'] = test_SUT()
    LOGGER.info("Result of test_SUT : " + str(result))
    LOGGER.info("Result response of test_SUT : " + str(result['response']))
    ##############################
    LOGGER.info("AssignResource command is executed successfully.")
    return result

@then("I have a subarray composed of 4 dishes")
def check_subarray_composition(result):
    #check that there was no error in response
    # TODO: To uncomment once latest tmc-mid chart is published
    assert_that(result['response']).is_equal_to(ResourceAllocation(dishes=[Dish(1), Dish(2), Dish(3), Dish(4)]))
    #check that this is reflected correctly on TMC side
    assert_that(resource('ska_mid/tm_subarray_node/1').get("receptorIDList")).is_equal_to((1, 2, 3, 4))
    #check that this is reflected correctly on CSP side
    assert_that(resource('mid_csp/elt/subarray_01').get('assignedReceptors')).is_equal_to((1, 2, 3, 4))
    #assert_that(resource('mid_csp/elt/master').get('receptorMembership')).is_equal_to((1, 1,))
    #TODO need to find a better way of testing sets with sets
    #assert_that(set(resource('mid_csp/elt/master').get('availableReceptorIDs'))).is_subset_of(set((4,3)))
    #check that this is reflected correctly on SDP side - no code at the current implementation
    LOGGER.info("Then I have a subarray composed of 4 dishes: PASSED")


@then("the subarray is in the condition that allows scan configurations to take place")
def check_subarry_state():
    # check that the obsState of SDP-Subarray is IDEL
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('IDLE')
    # check that the obsState of CSP-Subarray is IDEL
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('IDLE')
    # check that the obsState of TMC-Subarray is IDEL
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('IDLE')
    LOGGER.info("Then the subarray is in the condition that allows scan configurations to take place: PASSED")


def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_mid/tm_subarray_node/1').get("obsState") == "IDLE"):
        LOGGER.info("Release all resources assigned to subarray")
        take_subarray(1).and_release_all_resources()
        LOGGER.info("ResourceIdList is empty for Subarray 1 ")
    LOGGER.info("Put Telescope back to standby")
    set_telescope_to_standby()
    LOGGER.info("Telescope is in standby")

 
    
