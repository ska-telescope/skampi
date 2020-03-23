#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""
import sys

sys.path.append('/app')
import time
import signal
import pytest
import logging
from time import sleep
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then

from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from tango import DeviceProxy, DevState
from test_support.helpers import wait_for, obsState, resource, watch, take_subarray, restart_subarray, waiter, map_dish_nr_to_device_name
import logging

LOGGER = logging.getLogger(__name__)

import json

def set_workflow_id(file, workflow_id):
    with open(file,'r') as f: 
        data = json.load(f)
    data['sdp']['configure'][0]['workflow']['id'] = 'vis_receive'
    with open(file,'w') as f:
        json.dump(data, f)

   
def handlde_timeout():
    print("operation timeout")
    raise Exception("operation timeout")

#@pytest.mark.xfail
@scenario("1_XR-13_XTP-494.feature", "A2-Test, Sub-array transitions from IDLE to READY state")
@pytest.mark.skip(reason="WIP untill after refactoring")
def test_configure_subarray():
    """Configure Subarray."""

@given("I am accessing the console interface for the OET")
def start_up():
    the_waiter = waiter()
    the_waiter.set_wait_for_starting_up()
    SKAMid().start_up() 
    the_waiter.wait()
    LOGGER.info(the_waiter.logs)



@given("sub-array is in IDLE state")
def assign():
    take_subarray(1).to_be_composed_out_of(4)



@when("I call the configure scan execution instruction")
def config():
    timeout = 60
    #update the ID of the config data so that there is no duplicate configs send during tests
    file = 'tests/acceptance_tests/test_data/polaris_b1_no_cam.json'
    set_workflow_id(file, 'vis_receive')
    #set a timout mechanism in case a component gets stuck in executing
    signal.signal(signal.SIGALRM, handlde_timeout)
    signal.alarm(timeout)#wait for 30 seconds and timeout if still stick
    try:
        SubArray(1).configure_from_file(file)
    except:
        LOGGER.info("configure from file timed out after %s",timeout)


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
    the_waiter = waiter()
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "IDLE"):
        the_waiter.set_wait_for_tearing_down_subarray()
        LOGGER.info("tearing down composed subarray (IDLE)")
        SubArray(1).deallocate()
        the_waiter.wait()
        LOGGER.info(the_waiter.logs)
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "READY"):
        LOGGER.info("tearing down configured subarray (READY)")
        the_waiter.set_wait_for_ending_SB()
        SubArray(1).end_sb()
        the_waiter.wait()
        LOGGER.info(the_waiter.logs)
        the_waiter.set_wait_for_tearing_down_subarray()
        SubArray(1).deallocate()
        the_waiter.wait()
        LOGGER.info(the_waiter.logs)
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
        LOGGER.info("tearing down configuring subarray")
        restart_subarray(1)
    the_waiter.set_wait_for_going_to_standby()
    SKAMid().standby()
    the_waiter.wait()
    LOGGER.info(the_waiter.logs)

        
    
