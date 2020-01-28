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

    #given is from 29  to 44

    the_telescope = SKAMid()
    the_subarray = SubArray(1)
    the_resource_allocation = ResourceAllocation(dishes=[Dish(1), Dish(2)])


    #"under the hood resources for observing the internal state"
    tmc_subarray_node_01 = resource('ska_mid/tm_subarray_node/1')
    csp_subarray_01 = resource('mid_csp/elt/subarray_01')
    csp_master = resource('mid_csp/elt/master')
    sdp_subarray_01 = resource('mid_sdp/elt/subarray_1')

    print("Starting up telescope ...")
    #these are our assumptions for the initial state:
    #1. Telescope is in the "OFF" state (this means all sub arrays are in the DISABLED state)
    #we assume this is the state that the system will be after deployment
    the_telescope.start_up()

    #maybe get rid of this
    #print("Releasing any previously allocated resources... ")
   # if (tmc_subarray_node_01.get("State") == 'ON') :
   #     watch_State = watch(tmc_subarray_node_01).for_a_change_on("State")
    #    result = the_subarray.deallocate()
     #   State_val = watch_State.get_value_when_changed()
     #   assert_that(State_val).is_equal_to("OFF")


    print("Allocating new resources... ")
    #when I alocate dishes 1 - 2 : lines 56 to 67
    #prepare
    watch_State = watch(tmc_subarray_node_01).for_a_change_on("State")
    watch_receptorIDList = watch(tmc_subarray_node_01).for_a_change_on("receptorIDList")

    #execute
    result = the_subarray.allocate(the_resource_allocation)

    #gather info
    State_val = watch_State.get_value_when_changed()
    receptorIDList_val = watch_receptorIDList.get_value_when_changed(20)

    # then subarray cocrectly assigned resources
    # Confirm that TM_subbarray node has cocrectly assigned resources
    assert_that(result).is_equal_to(the_resource_allocation) 
    assert_that(State_val).is_equal_to("ON")
    assert_that(tmc_subarray_node_01.get('obsState')).is_equal_to('IDLE')
    assert_that(receptorIDList_val).is_equal_to((1, 2))
  
    # the following changes must have occurred before the previous
    #then CSP subarray must be in state ON and in obsState IDLE
    assert_that(csp_subarray_01.get('State')).is_equal_to('ON')
    assert_that(csp_subarray_01.get('obsState')).is_equal_to('IDLE')
    assert_that(csp_subarray_01.get('receptors')).is_equal_to((1,2))
    assert_that(csp_master.get('receptorMembership')).is_equal_to((1,1,0,0))
    assert_that(csp_master.get('availableReceptorIDs')).is_equal_to((3,4))
    assert_that(csp_subarray_01.get('receptors')).is_equal_to((1,2))

    #then SDP subarray must be in state ON and in Obstate IDLE
    assert_that(sdp_subarray_01.get('State')).is_equal_to('ON')
    assert_that(sdp_subarray_01.get('obsState')).is_equal_to('IDLE') 

    #this should become part of the post session and the testing part should be another test
    #############################################################################
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