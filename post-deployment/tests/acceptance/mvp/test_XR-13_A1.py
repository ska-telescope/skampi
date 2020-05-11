#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""
import sys
import pytest
import logging
from time import sleep
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
from datetime import date,datetime
#SUT
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
#SUT infrastructure
from tango import DeviceProxy, DevState
## local imports
from resources.test_support.helpers import wait_for, obsState, resource, watch, waiter, map_dish_nr_to_device_name,\
set_telescope_to_standby,set_telescope_to_running,take_subarray,telescope_is_in_standby
from resources.test_support.log_helping import DeviceLogging
from resources.test_support.state_checking import StateChecker

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

def print_logs_to_file(s,d,status='ok'):
    if status=='ok':
        filename_d = 'logs_test_AX-13_A1_{}.csv'.format(datetime.now().strftime('%d_%m_%Y-%H_%M'))
        filename_s = 'states_test_AX-13_A1_{}.csv'.format(datetime.now().strftime('%d_%m_%Y-%H_%M'))
    elif status=='error':
        filename_d = 'error_logs_test_AX-13_A1_{}.csv'.format(datetime.now().strftime('%d_%m_%Y-%H_%M'))
        filename_s = 'error_states_test_AX-13_A1_{}.csv'.format(datetime.now().strftime('%d_%m_%Y-%H_%M'))
    LOGGER.info("Printing log files to build/{} and build/{}".format(filename_d,filename_s))
    d.implementation.print_log_to_file(filename_d,style='csv')
    s.print_records_to_file(filename_s,style='csv',filtered=False)



@pytest.fixture
def result():
    return {}

@scenario("../../../features/1_XR-13_XTP-494.feature", "A1-Test, Sub-array resource allocation")
@pytest.mark.skip(reason="WIP untill after refactoring")
def test_allocate_resources():
    """Assign Resources."""

@given("A running telescope for executing observations on a subarray")
def set_to_running():
    LOGGER.info("Given A running telescope for executing observations on a subarray")
    assert(telescope_is_in_standby())
    LOGGER.info("Starting up telescope")
    set_telescope_to_running()

@when("I allocate 4 dishes to subarray 1")
def allocate_four_dishes(result):
    LOGGER.info("When I allocate 4 dishes to subarray 1")
    ###setting up waits
    the_waiter = waiter()
    the_waiter.set_wait_for_assign_resources()
    ####loging
    s = StateChecker(devices_to_log,specific_states=non_default_states_to_check)
    s.run(threaded=True,resolution=0.1)
    d = DeviceLogging('DeviceLoggingImplWithDBDirect')
    d.update_traces(devices_to_log)
    d.start_tracing()
    ##system under test is being excuted
    result['response'] = SubArray(1).allocate(ResourceAllocation(dishes=[Dish(1), Dish(2), Dish(3), Dish(4)]))
    ####################################
    #wait for certain values to be changed (wait_for_assign_resources)
    the_waiter.wait()
    if the_waiter.timed_out:
        pytest.fail('timed out whilst assigning resources:\n {}'.format(the_waiter.logs))

    LOGGER.info("Assign resources executed successfully")
    LOGGER.info("Gathering logs")
    s.stop()
    d.stop_tracing()
    print_logs_to_file(s,d,status='ok')
    return result

@then("I have a subarray composed of 4 dishes")
def check_subarray_composition(result):

    #check that there was no error in response
    assert_that(result['response']).is_equal_to(ResourceAllocation(dishes=[Dish(1), Dish(2), Dish(3), Dish(4)]))
    #check that this is reflected correctly on TMC side
    assert_that(resource('ska_mid/tm_subarray_node/1').get("receptorIDList")).is_equal_to((1, 2, 3, 4))
    #check that this is reflected correctly on CSP side
    assert_that(resource('mid_csp/elt/subarray_01').get('assignedReceptors')).is_equal_to((1, 2, 3, 4))
    assert_that(resource('mid_csp/elt/master').get('receptorMembership')).is_equal_to((1, 1, 1, 1))
    #TODO need to find a better way of testing sets with sets
    #assert_that(set(resource('mid_csp/elt/master').get('availableReceptorIDs'))).is_subset_of(set((4,3)))
    #check that this is reflected correctly on SDP side - no code at the current implementation
    LOGGER.info("Then I have a subarray composed of 4 dishes: PASSED")


@then("the subarray is in the condition that allows scan configurations to take place")
def check_subarry_state():
    
    #check that the TMC report subarray as being in the ON state and obsState = IDLE
    assert_that(resource('ska_mid/tm_subarray_node/1').get("State")).is_equal_to("ON")
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('IDLE')
    #check that the CSP report subarray as being in the ON state and obsState = IDLE
    assert_that(resource('mid_csp/elt/subarray_01').get('State')).is_equal_to('ON')
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('IDLE')
    #check that the SDP report subarray as being in the ON state and obsState = IDLE
    assert_that(resource('mid_sdp/elt/subarray_1').get('State')).is_equal_to('ON')
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('IDLE')
    LOGGER.info("Then the subarray is in the condition that allows scan configurations to take place: PASSED")

def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_mid/tm_subarray_node/1').get("State") == "ON"):
        LOGGER.info("Release all resources assigned to subarray")
        take_subarray(1).and_release_all_resources()
    LOGGER.info("Put Telescope back to standby")
    set_telescope_to_standby()
 
    
