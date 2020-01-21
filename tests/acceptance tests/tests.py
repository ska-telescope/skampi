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
from tango import DeviceProxy

def pause():
    sleep(4)


def test_allocation():
    the_telescope = SKAMid()
    the_subarray = SubArray(1)
    the_resource_allocation = ResourceAllocation(dishes=[Dish(1), Dish(2)])

    print("Starting up telescope ...")
    the_telescope.start_up()

   #commented this out as it gives an error when it was already deallocated 
   # print("Releasing any previously allocated resources... ")
   # result = the_subarray.deallocate()
   # pause()

    print("Allocating new resources... ")
    result = the_subarray.allocate(the_resource_allocation)
    pause() #rather poll for subarray_proxy.State changing OFF/OFLLINE to ON (TMC team to confirm whether this is really neccesary

    assert_that(result).is_equal_to(the_resource_allocation)

    # Confirm result via direct inspection of TMC
    subarray_proxy = DeviceProxy('ska_mid/tm_subarray_node/1')
    pause() # not neccesary
    receptor_list = subarray_proxy.receptorIDList
    pause() # not neccesary
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