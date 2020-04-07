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
import random
from datetime import date
from random import choice
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
import oet
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
    print("random_no", random_no)
    data['scanID'] = random_no
    data['sdp']['configure'][0]['id'] = "realtime-" + date.today().strftime("%Y%m%d") + "-" + str(
        choice(range(1, 10000)))

    fieldid = 1
    intervalms = 1400

    scan_details = {}
    scan_details["fieldId"] = fieldid
    scan_details["intervalMs"] = intervalms

    scanparams = {}
    scanParameters = {}

    scanParameters[random_no] = scan_details
    scanparams = scanParameters

    data['sdp']['configure'][0]['scanParameters'] = scanParameters

    with open(file, 'w') as f:
        json.dump(data, f)


def handlde_timeout():
    print("operation timeout")
    raise Exception("operation timeout")


@scenario("../../../features/1_XR-13_XTP-494.feature", "A3-Test, Sub-array performs an observational imaging scan")
def test_subarray_scan():
    """Subarray Scan Operation."""


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
    assert_that(receptorIDList_val == [(1, 2, 3, 4)])


@given("Sub-array is in READY state")
def config():
    timeout = 60
    # update the ID of the config data so that there is no duplicate configs send during tests
    file = 'resources/test_data/polaris_b1_no_cam.json'
    update_file(file)
    # set a timout mechanism in case a component gets stuck in executing
    signal.signal(signal.SIGALRM, handlde_timeout)
    signal.alarm(timeout)  # wait for 30 seconds and timeout if still stick
    try:
        SubArray(1).configure_from_file(file, False)
    except:
        LOGGER.info("configure from file timed out after %s", timeout)


def check_state():
    watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")
    # check that the TMC report subarray as being in the ON state and obsState = READY
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('READY')
    logging.info("subarray obsState: " + resource('ska_mid/tm_subarray_node/1').get("obsState"))
    # check that the CSP report subarray as being in the ON state and obsState = READY
    watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("obsState")
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('READY')
    logging.info("CSPsubarray obsState: " + resource('mid_csp/elt/subarray_01').get("obsState"))
    # check that the SDP report subarray as being in the ON state and obsState = READY
    watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("obsState")
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('READY')
    logging.info("SDPsubarray obsState: " + resource('mid_sdp/elt/subarray_1').get("obsState"))


@when("I call the execution of the scan instruction")
def scan():
    timeout = 20
    # set a timout mechanism in case a component gets stuck in executing
    signal.signal(signal.SIGALRM, handlde_timeout)
    signal.alarm(timeout)  # wait for 30 seconds and timeout if still stick
    try:
        SubArray(1).scan(20.0)
    except:
        LOGGER.info("Scan from file timed out after %s", timeout)


@then("Sub-array is in SCANNING state")
def check_sub_state():
    # check that the TMC report subarray as being in the ON state and obsState = SCANNING
    # watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('SCANNING')
    # logging.info("subarray obsState: " + resource('ska_mid/tm_subarray_node/1').get("obsState"))
    # check that the CSP report subarray as being in the ON state and obsState = SCANNING
    # watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("obsState")
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('SCANNING')
    # logging.info("subarray obsState: " + resource('mid_csp/elt/subarray_01').get("obsState"))
    # check that the SDP report subarray as being in the ON state and obsState = SCANNING
    # watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("obsState")
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('SCANNING')
    # logging.info("subarray obsState: " + resource('mid_sdp/elt/subarray_1').get("obsState"))


@then("After SCANNING Sub-array is moved to READY state")
def check_ready_state():
    # check that the TMC report subarray as being in the ON state and obsState = SCANNING
    watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState")
    assert_that(resource('ska_mid/tm_subarray_node/1').get('obsState')).is_equal_to('READY')
    logging.info("TMC-subarray obsState: " + resource('ska_mid/tm_subarray_node/1').get("obsState"))
    # check that the CSP report subarray as being in the ON state and obsState = SCANNING
    watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("obsState")
    assert_that(resource('mid_csp/elt/subarray_01').get('obsState')).is_equal_to('READY')
    logging.info("CSP-subarray obsState: " + resource('mid_csp/elt/subarray_01').get("obsState"))
    # check that the SDP report subarray as being in the ON state and obsState = SCANNING
    watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("obsState")
    assert_that(resource('mid_sdp/elt/subarray_1').get('obsState')).is_equal_to('READY')
    logging.info("SDP-subarray obsState: " + resource('mid_sdp/elt/subarray_1').get("obsState"))


def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    the_waiter = waiter()
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
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "SCANNING"):
        LOGGER.info("tearing down scanning subarray")
        restart_subarray(1)
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
        LOGGER.info("tearing down configuring subarray")
        restart_subarray(1)
    if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "IDLE"):
        the_waiter.set_wait_for_tearing_down_subarray()
        LOGGER.info("tearing down composed subarray (IDLE)")
        SubArray(1).deallocate()
        the_waiter.wait()
        LOGGER.info(the_waiter.logs)
    the_waiter.set_wait_for_going_to_standby()
    SKAMid().standby()
    LOGGER.info("standby command is executed on telescope")
    the_waiter.wait()
    LOGGER.info(the_waiter.logs)

