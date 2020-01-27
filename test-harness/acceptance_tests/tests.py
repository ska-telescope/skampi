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
from time import sleep
from assertpy import assert_that

from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from tango import DeviceProxy,DevState
from helpers import wait_for, obsState, resource, watch


def pause():
    sleep(4)


def test_allocation():
    the_telescope = SKAMid()
    the_subarray = SubArray(1)
    the_resource_allocation = ResourceAllocation(dishes=[Dish(1), Dish(2)])

    #"under the hood resources for observing the internal state"
    tmc_subarray_node_01 = resource('ska_mid/tm_subarray_node/1')
    csp_subarray_01 = resource('mid_csp/elt/subarray_01')
    csp_master = resource('mid_csp/elt/master')
    sdp_subarray_01 = resource('mid_sdp/elt/subarray_1')



    print("Starting up telescope ...")
    the_telescope.start_up()


    print("Releasing any previously allocated resources... ")
    if (tmc_subarray_node_01.get("State") == 'ON') :
        watch_State = watch(tmc_subarray_node_01).for_a_change_on("State")
        result = the_subarray.deallocate()
        State_val = watch_State.get_value_when_changed()
        assert_that(State_val).is_equal_to("OFF")

    print("Allocating new resources... ")
    #prepare
    watch_State = watch(tmc_subarray_node_01).for_a_change_on("State")
    watch_receptorIDList = watch(tmc_subarray_node_01).for_a_change_on("receptorIDList")

    #execute
    result = the_subarray.allocate(the_resource_allocation)

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
    

    print("Now deallocating resources ... ")
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


    print("Subarry has no allocated resources")

    # put telescope to standby
    the_telescope.standby()
    print("Script Complete: All resources dealoccated, Telescope is in standby")