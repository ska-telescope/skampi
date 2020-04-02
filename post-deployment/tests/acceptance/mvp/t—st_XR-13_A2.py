#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""
import sys

import time
import signal
import pytest
import logging
from time import sleep
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then

from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from tango import DeviceProxy, DevState
from helpers import wait_for, obsState, resource, watch, take_subarray, restart_subarray

def update_file(file):
    import json
    import random
    from datetime import date 
    with open(file,'r') as f: 
        data = json.load(f)
    data['sdp']['configure'][0]['id'] = "realtime-"+date.today().strftime("%Y%m%d")+"-"+str(random.choice(range(1, 10000))) 
    with open(file,'w') as f:
        json.dump(data, f)

   
def handlde_timout():
    print("operation timeout")
    raise Exception("operation timeout")

#@pytest.mark.xfail
@scenario("../../../features/1_XR-13_XTP-494.feature", "A2-Test, Sub-array transitions from IDLE to READY state")
def test_deallocate_resources():
    """Configure Subarray."""

@given("I am accessing the console interface for the OET")
def start_up():
    SKAMid().start_up()  

@given("sub-array is in IDLE state")
def assign():
    watch_receptorIDList = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("receptorIDList")
    take_subarray(1).to_be_composed_out_of(4)
    watch_receptorIDList.wait_until_value_changed()

@when("I call the configure scan execution instruction")
def config():
    #update the ID of the config data so that there is no duplicate configs send during tests
    file = 'tests/acceptance_tests/test_data/polaris_b1_no_cam.json'
    update_file(file)
    #set a timout mechanism in case a component gets stuck in executing
    signal.signal(signal.SIGALRM, handlde_timout)
    signal.alarm(60)#wait for 30 seconds and timeout if still stick
    try:
        SubArray(1).configure_from_file(file)
    except:
        print("timeout")


@then("sub-array is in READY state for which subsequent scan commands can be directed to deliver a basic imaging outcome")
def check_state():
    #check that the TMC report subarray as being in the ON state and obsState = IDLE
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('READY')
    #check that the CSP report subarray as being in the ON state and obsState = IDLE
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('READY')
    #check that the SDP report subarray as being in the ON state and obsState = IDLE
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('READY')

def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "IDLE"):
        SubArray(1).deallocate()
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "READY"):
        SubArray(1).end_sb()
        SubArray(1).deallocate()
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
        restart_subarray(1)
    SKAMid().standby()
        
    
