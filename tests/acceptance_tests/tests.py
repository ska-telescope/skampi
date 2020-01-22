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
from helpers import wait_for

THE_SUBARRAY_NODE = 'ska_mid/tm_subarray_node/1'

def pause():
    sleep(4)


def test_allocation():
    the_telescope = SKAMid()
    the_subarray = SubArray(1)
    the_resource_allocation = ResourceAllocation(dishes=[Dish(1), Dish(2)])

    print("Starting up telescope ...")
    the_telescope.start_up()


    print("Releasing any previously allocated resources... ")
    subarray_proxy = DeviceProxy(THE_SUBARRAY_NODE) 
    if (subarray_proxy.read_attribute("State").value == DevState.ON) :
        result = the_subarray.deallocate()
        wait_result = wait_for(THE_SUBARRAY_NODE).to_be({"attr" : "State", "value" : DevState.OFF}) 
        assert_that(wait_result).is_equal_to("OK")

    print("Allocating new resources... ")
    result = the_subarray.allocate(the_resource_allocation)
    assert_that(result).is_equal_to(the_resource_allocation)
   
    wait_result = wait_for('ska_mid/tm_subarray_node/1').to_be({"attr" : "State", "value" : DevState.ON}) 
    assert_that(wait_result).is_equal_to("OK")

    # Confirm that TM_subbarray node has cocrectly assigned resources
    subarray_proxy = DeviceProxy('ska_mid/tm_subarray_node/1')   
    receptor_list = subarray_proxy.receptorIDList
    assert_that(receptor_list).is_equal_to((1, 2))

    #need to check the state as well is in ObsState = IDLE and State = ON
    #TODO check the resource assignment of the CSP is correct (receptors and corresponding VCC state   - also check that it changed to correct state)
    #mid_csp/elt/master check the status of receptors and VCC reflect assignment
    #mid_csp/elt/subarray_01 check status and correct composition
    # check the resource assignment of the SDP is correct (no op - also check that the changed to correct state ObsState= IDLE and State = ON)
    # check that the dishes have responded
    assert_that(receptor_list).is_equal_to((1, 2))

    print("Now deallocating resources ... ")
    the_subarray.deallocate()
    pause() #rather poll for subarray_proxy.State changing ON OFFLINE (TMC team to confim)

    # Confirm result via direct inspection of TMC - expecting None 
    receptor_list = subarray_proxy.receptorIDList
    pause() # not needed
    
    assert_that(receptor_list).is_equal_to(None)

    print("Subarry has no allocated resources")

    # put telescope to standby
    the_telescope.standby()
    print("Script Complete: All resources dealoccated, Telescope is in standby")