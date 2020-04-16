#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""

import random
import signal
from concurrent import futures
from time import sleep
import threading
from datetime import date
from random import choice
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
import oet
import pytest
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from tango import DeviceProxy, DevState
from resources.test_support.helpers import wait_for, obsState, resource, watch, take_subarray, restart_subarray, waiter, \
    map_dish_nr_to_device_name
import logging

LOGGER = logging.getLogger(__name__)

import json


def update_file(file):
    with open(file, 'r') as f:
        data = json.load(f)
    random_no = random.randint(100, 999)
    data['scanID'] = random_no
    data['sdp']['configure'][0]['id'] = "realtime-" + date.today().strftime("%Y%m%d") + "-" + str(choice
                                                                                                  (range(1, 10000)))
    fieldid = 1
    intervalms = 1400

    scan_details = {}
    scan_details["fieldId"] = fieldid
    scan_details["intervalMs"] = intervalms
    scanParameters = {}
    scanParameters[random_no] = scan_details

    data['sdp']['configure'][0]['scanParameters'] = scanParameters

    with open(file, 'w') as f:
        json.dump(data, f)


def handlde_timeout():
    print("operation timeout")
    raise Exception("operation timeout")


@pytest.fixture
def fixture():
    return {}

def send_scan(duration):
    SubArray(1).scan(duration)


@scenario("../../../features/1_XR-13_XTP-494.feature", "A3-Test, Sub-array performs an observational imaging scan")
def test_subarray_scan():
    """Imaging Scan Operation."""

@given("I am accessing the console interface for the OET")
def start_up():
    the_waiter = waiter()
    the_waiter.set_wait_for_starting_up()
    SKAMid().start_up()
    the_waiter.wait()
    LOGGER.info(the_waiter.logs)

    take_subarray(1).to_be_composed_out_of(4)
    assert_that(resource('ska_mid/tm_subarray_node/1').get("obsState")).is_equal_to("IDLE")
    assert_that(resource('mid_csp/elt/subarray_01').get("obsState")).is_equal_to("IDLE")
    assert_that(resource('mid_sdp/elt/subarray_1').get("obsState")).is_equal_to("IDLE")

    watch_receptorIDList = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("receptorIDList")
    assert_that(resource('ska_mid/tm_subarray_node/1').get("receptorIDList")).is_equal_to((1, 2, 3, 4))
    receptorIDList_val = watch_receptorIDList.get_value_when_changed()
    assert_that(receptorIDList_val == [(1,2,3,4)])

@given("Sub-array is in READY state")
def config():
    timeout = 80
    file = 'resources/test_data/polaris_b1_no_cam.json'
    # update the ID of the config data so that there is no duplicate configs send during tests
    update_file(file)
    signal.signal(signal.SIGALRM, handlde_timeout)
    signal.alarm(timeout)  # wait for 30 seconds and timeout if still stick
    try:
        logging.info("Configuring the subarray")
        SubArray(1).configure_from_file(file, with_processing=False)
    except Exception as ex_obj:
        LOGGER.info("Exception in configure command:", ex_obj)

def check_state():
    # check that the TMC report subarray as being in the ON state and obsState = READY
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('READY')
    logging.info("subarray obsState: " + resource('ska_mid/tm_subarray_node/1').get("obsState"))
    # check that the CSP report subarray as being in the ON state and obsState = READY
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('READY')
    logging.info("CSPsubarray obsState: " + resource('mid_csp/elt/subarray_01').get("obsState"))
    # check that the SDP report subarray as being in the ON state and obsState = READY
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('READY')
    logging.info("SDPsubarray obsState: " + resource('mid_sdp/elt/subarray_1').get("obsState"))

@given("duration of scan is 10 seconds")
def scan_duration(fixture):
    fixture['duration'] = 10.0
    return fixture

@when("I call the execution of the scan instruction")
def invoke_scan_command(fixture):
    executor = futures.ThreadPoolExecutor(max_workers=1)
    fixture['watch_subarray_state'] = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")
    future = executor.submit(send_scan, fixture['duration'])
    fixture['future'] = future
    return fixture

@then("Sub-array changes to a SCANNING state")
def check_ready_state(fixture):
    fixture['watch_subarray_state'].wait_until_value_changed()
    # check that the TMC report subarray as being in the obsState = READY
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('SCANNING')
    logging.info("TMC-subarray obsState: " + resource('ska_mid/tm_subarray_node/1').get("obsState"))
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('SCANNING')
    logging.info("CSP-subarray obsState: " + resource('mid_csp/elt/subarray_01').get("obsState"))
    # check that the SDP report subarray as being in the obsState = READY
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('SCANNING')
    logging.info("SDP-subarray obsState: " + resource('mid_sdp/elt/subarray_1').get("obsState"))
    return fixture

@then("observation ends after 10 seconds as indicated by returning to READY state")
def check_running_state(fixture):
    fixture['future'].result(timeout=10)
    # check that the TMC report subarray as being in the obsState = READY
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('READY')
    logging.info("TMC-subarray obsState: " + resource('ska_mid/tm_subarray_node/1').get("obsState"))
    # check that the CSP report subarray as being in the obsState = READY
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('READY')
    logging.info("CSP-subarray obsState: " + resource('mid_csp/elt/subarray_01').get("obsState"))
    # check that the SDP report subarray as being in the obsState = READY
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('READY')
    logging.info("SDP-subarray obsState: " + resource('mid_sdp/elt/subarray_1').get("obsState"))

def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    the_waiter = waiter()
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "IDLE"):
        print("inside IDLE")
        the_waiter.set_wait_for_tearing_down_subarray()
        LOGGER.info("tearing down composed subarray (IDLE)")
        SubArray(1).deallocate()
        the_waiter.wait()
        LOGGER.info(the_waiter.logs)
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "READY"):
        print("inside READY")
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
        print("inside CONFIGURING")
        LOGGER.info("tearing down configuring subarray")
        restart_subarray(1)
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "SCANNING"):
        LOGGER.info("tearing down scanning subarray")
        restart_subarray(1)
    the_waiter.set_wait_for_going_to_standby()
    SKAMid().standby()
    LOGGER.info("standby command is executed on telescope")
    the_waiter.wait()
    LOGGER.info(the_waiter.logs)

