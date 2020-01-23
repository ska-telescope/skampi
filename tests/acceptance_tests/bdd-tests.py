#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""
import sys
sys.path.append('/app')

import pytest
import logging
from time import sleep
from assertpy import assert_that
from pytest-bdd import scenario, given, when, then

from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from tango import DeviceProxy,DevState
from helpers import wait_for, obsState, resource, watch

@scenario("./path-to-feature-file", "Allocate Resources")

@given("The telescope is ready")
def i_can_haz_telescope():
    the_telescope = SKAMid()
    logging.info("Starting up telescope ...")
    the_telescope.start_up()
    return the_telescope

@given("A subarray definition")
def gimme_a_subarray():
    the_subarray = SubArray(1)
    return the_subarray

@given("A resource allocation definition")
def resource_alloc_def():
    the_resource_allocation = ResourceAllocation(dishes=[Dish(1), Dish(2)])
    return the_resource_allocation

    #"under the hood resources for observing the internal state"
@given("a means of observing the tmc subarray")
def show_tmc_subarray_state():
    tmc_subarray_node_01 = resource('ska_mid/tm_subarray_node/1')
    return tmc_subarray_node_01

@given("a means of observing the csp subarray")
def show_csp_subarray_state():
    csp_subarray_01 = resource('mid_csp/elt/subarray_01')
    return csp_subarray_01

@given("a means of observing the csp master")
def show_csp_master_state():
    csp_master = resource('mid_csp/elt/master')
    return csp_master

@given("a means of observing the sdp subarray")
def show_sdp_subarray_state():
    sdp_subarray_01 = resource('mid_sdp/elt/subarray_1')
    return sdp_subarray_01

@given("there are not previously allocated resources")
# Note: this step may not be appropriate when testing allocation of multiple subbarrays, or may require further work
def deallocate_resources(show_tmc_subarray_state, gimme_a_subarray):
    logging.info("Releasing any previously allocated resources... ")
    if (tmc_subarray_node_01.get("State") == 'ON') :
        watch_State = watch(tmc_subarray_node_01).for_a_change_on("State")
        result = the_subarray.deallocate()
        State_val = watch_State.get_value_when_changed()
        assert_that(State_val).is_equal_to("OFF")
    return result

@given("a monitor on tmc subarray state")
def watch_tmc_subarray_state(show_tmc_subarray_state):
    watch_State = watch(tmc_subarray_node_01).for_a_change_on("State")
    return watch_State

@given("a way of monitoring receptor ID list")
def watch_receptorIDlist(show_tmc_subarray_state):
    watch_receptorIDList = watch(tmc_subarray_node_01).for_a_change_on("receptorIDList")
    return watch_receptorIDList

@given("a way to report on the subarray status")
def show_alloc_results(gimme_a_subarray):
#TODO add code here to return an empty result/watcher thing
    return result

@when("I allocate resources to a subarray")
def allocate_resources(gimme_a_subarray, resource_alloc_def):
    #execute
    result = the_subarray.allocate(the_resource_allocation)

@then("the subarray is correctly allocated")
def check_resources_allocated(watch_tmc_subarray_state, watch_receptorIDList, resource_alloc_def, show_tmc_subarray_state, show_csp_subarray_state, show_csp_master_state, show_sdp_subarray_state):
    #gather info
    State_val = watch_State.get_value_when_changed()
    receptorIDList_val = watch_receptorIDList.get_value_when_changed(20)

    # Confirm that TM_subbarray node has cocrectly assigned resources
    assert_that(result).is_equal_to(the_resource_allocation) 
    assert_that(State_val).is_equal_to("ON")
    assert_that(tmc_subarray_node_01.get('obsState')).is_equal_to('IDLE')
    assert_that(receptorIDList_val).is_equal_to((1, 2))
  
    # the following changes must have occurred before the previous
    #CSP subarray must be in state ON and in obsState IDLE
    assert_that(csp_subarray_01.get('State')).is_equal_to('ON')
    assert_that(csp_subarray_01.get('obsState')).is_equal_to('IDLE')
    assert_that(csp_subarray_01.get('receptors')).is_equal_to((1,2))
    assert_that(csp_master.get('receptorMembership')).is_equal_to((1,1,0,0))
    assert_that(csp_master.get('availableReceptorIDs')).is_equal_to((3,4))
    assert_that(csp_subarray_01.get('receptors')).is_equal_to((1,2))

    #SDP subarray must be in state ON and in Obstate IDLE
    assert_that(sdp_subarray_01.get('State')).is_equal_to('ON')
    assert_that(sdp_subarray_01.get('obsState')).is_equal_to('IDLE')

    #need to check the state as well is in ObsState = IDLE and State = ON
    #TODO check the resource assignment of the CSP is correct (receptors and corresponding VCC state   - also check that it changed to correct state)
    #mid_csp/elt/master check the status of receptors and VCC reflect assignment
    #mid_csp/elt/subarray_01 check status and correct composition
    # check the resource assignment of the SDP is correct (no op - also check that the changed to correct state ObsState= IDLE and State = ON)
    # check that the dishes have responded
    
#TODO do similar when, then, statements for deallocating resources
    logging.info("Now deallocating resources ... ")
    #prepare
    watch_State = watch(tmc_subarray_node_01).for_a_change_on("State")
    watch_receptorIDList = watch(tmc_subarray_node_01).for_a_change_on("receptorIDList")

    # execute
    the_subarray.deallocate()

    # gather info
    State_val = watch_State.get_value_when_changed()
    receptorIDList_val = watch_receptorIDList.get_value_when_changed()

    # Confirm 

    assert_that(State_val).is_equal_to("OFF")
    assert_that(tmc_subarray_node_01.get('obsState')).is_equal_to('IDLE')
    assert_that(receptorIDList_val).is_equal_to(None)


    logging.info("Subarry has no allocated resources")

    # put telescope to standby
    the_telescope.standby()
    logging.info("Script Complete: All resources dealoccated, Telescope is in standby")
