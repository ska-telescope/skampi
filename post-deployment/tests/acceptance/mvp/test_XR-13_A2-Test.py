#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""
import random
import signal
from datetime import date,datetime
from random import choice
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from resources.test_support.helpers import wait_for, obsState, resource, watch, take_subarray, restart_subarray, waiter, \
    map_dish_nr_to_device_name, update_file, DeviceLogging
import logging

LOGGER = logging.getLogger(__name__)

import json

def handlde_timeout(arg1,agr2):
    print("operation timeout")
    raise Exception("operation timeout")

def print_logs_to_file(d,status='ok'):
    if status=='ok':
        filename = 'test_AX-13_A2_{}.csv'.format(datetime.now().strftime('%d_%m_%Y-%H_%M'))
    elif status=='error':
        filename = 'error_test_AX-13_A2_{}.csv'.format(datetime.now().strftime('%d_%m_%Y-%H_%M'))
    LOGGER.info("Printing log files to build/{}".format(filename))
    d.implementation.print_log_to_file(filename,style='csv')


@scenario("../../../features/1_XR-13_XTP-494.feature", "A2-Test, Sub-array transitions from IDLE to READY state")
def test_configure_subarray():
    """Configure Subarray."""

@given("I am accessing the console interface for the OET")
def start_up():
    the_waiter = waiter()
    the_waiter.set_wait_for_starting_up()
    SKAMid().start_up()
    the_waiter.wait()
    LOGGER.info("Telescope Started up")
    LOGGER.debug("the_waiter.logs")

@given("sub-array is in IDLE state")
def assign():
    take_subarray(1).to_be_composed_out_of(4)
    LOGGER.info("Subarray 1 is ready and composed out of 4 dishes")

@when("I call the configure scan execution instruction")
def config():
    timeout = 60
    # update the ID of the config data so that there is no duplicate configs send during tests
    file = 'resources/test_data/polaris_b1_no_cam.json'
    update_file(file)
    signal.signal(signal.SIGALRM, handlde_timeout)
    signal.alarm(timeout)  # wait for 20 seconds and timeout if still stick
    #set up logging of components
    LOGGER.info("Starting Configuration Test")
    d = DeviceLogging('DeviceLoggingImplWithDBDirect')
    d.update_traces(['ska_mid/tm_subarray_node/1',
                    'mid_csp/elt/subarray_01',
                    'mid_csp_cbf/sub_elt/subarray_01',
                    'mid_sdp/elt/subarray_1'])
    d.start_tracing()
    try:
        SubArray(1).configure_from_file(file, with_processing = False)
    except:
        LOGGER.info("Configure Command timed out after {} seconds".format(timeout))
        LOGGER.info("Gathering logs")
        d.stop_tracing()
        print_logs_to_file(d,status='error')
        LOGGER.info("The following messages was logged from devices:\n{}".format(d.get_printable_messages()))
        raise
    LOGGER.info("Configure executed successfully")
    LOGGER.info("Gathering logs")
    d.stop_tracing()
    print_logs_to_file(d,status='ok')

@then("sub-array is in READY state for which subsequent scan commands can be directed to deliver a basic imaging outcome")
def check_state():
    LOGGER.info("Checking the results")
    # check that the TMC report subarray as being in the obsState = READY
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('READY')
    # check that the CSP report subarray as being in the obsState = READY
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('READY')
    # check that the SDP report subarray as being in the obsState = READY
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('READY')
    LOGGER.info("Results OK")


def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    the_waiter = waiter()
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "IDLE"):
        #this means there must have been an error
        the_waiter.set_wait_for_tearing_down_subarray()
        LOGGER.info("tearing down composed subarray (IDLE)")
        SubArray(1).deallocate()
        the_waiter.wait()
        LOGGER.info(the_waiter.logs)
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "READY"):
        #this means test must have passed
        LOGGER.info("tearing down configured subarray (READY)")
        the_waiter.set_wait_for_ending_SB()
        SubArray(1).end_sb()
        the_waiter.wait()
        LOGGER.debug(the_waiter.logs)
        the_waiter.set_wait_for_tearing_down_subarray()
        SubArray(1).deallocate()
        the_waiter.wait()
        LOGGER.debug(the_waiter.logs)
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
        LOGGER.warn("Subarray is still in configuring! Please restart MVP manualy to complete tear down")
        restart_subarray(1)
        #raise exception since we are unable to continue with tear down
        raise Exception("Unable to tear down test setup")
    LOGGER.info("Putting Telescope in standby")
    the_waiter.set_wait_for_going_to_standby()
    SKAMid().standby()
    the_waiter.wait()
    LOGGER.debug(the_waiter.logs)

