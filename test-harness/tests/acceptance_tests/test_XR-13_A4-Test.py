#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XR-13_A4-Test
----------------------------------
Acceptance test to deallocate the resources from subarray for MVP.
"""
import sys

sys.path.append('/app')
import time
import pytest
import logging
from time import sleep
from assertpy import assert_that
from pytest_bdd import scenario, given, when, then
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from tango import DeviceProxy, DevState
from test_support.helpers import wait_for, obsState, resource, watch

@scenario("1_XR-13_XTP-494.feature", "A4-Test, Sub-array deallocation of resources")
@pytest.mark.skip(reason="WIP untill after refactoring")
def test_deallocate_resources():
    """Deallocate Resources."""

@given("SKA Mid telescope")
def i_can_haz_telescope():
    the_telescope = SKAMid()
    return the_telescope

@given("The telescope is ready")
def startup_telescope(i_can_haz_telescope):
    logging.info("Starting up the telescope")
    the_telescope = i_can_haz_telescope.start_up()
    return the_telescope

@given("A subarray definition")
def gimme_a_subarray():
    the_subarray = SubArray(1)
    return the_subarray

@given("A resource allocation definition")
def resource_alloc_def():
    the_resource_allocation = ResourceAllocation(dishes=[Dish(1), Dish(2)])
    return the_resource_allocation

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

@given("a means of observing the sdp master")
def show_sdp_master_state():
    sdp_master = resource('mid_sdp/elt/master')
    return sdp_master

@given("a monitor on the tmc subarray state")
def watch_tmc_subarray_state(show_tmc_subarray_state):
    watch_State_tmc = watch(show_tmc_subarray_state).for_a_change_on("State")
    return watch_State_tmc

@given("a monitor on csp subarray state")
def watch_csp_subarray_state(show_csp_subarray_state):
    watch_State_csp = watch(show_csp_subarray_state).for_a_change_on("State")
    return watch_State_csp

@given("a monitor on sdp subarray state")
def watch_sdp_subarray_state(show_sdp_subarray_state):
    watch_State_sdp = watch(show_sdp_subarray_state).for_a_change_on("State")
    return watch_State_sdp

@given("a way of monitoring receptor ID list")
def watch_receptorIDlist(show_tmc_subarray_state):
    watch_receptorIDList = watch(show_tmc_subarray_state).for_a_change_on("receptorIDList")
    return watch_receptorIDList

@given("I allocate resources to a subarray")
def allocate_resources(gimme_a_subarray, resource_alloc_def):
    result = gimme_a_subarray.allocate(resource_alloc_def)

@when("I deallocate the resources")
def deallocate_resources(gimme_a_subarray):
    logging.info("Now deallocating resources ... ")
    result = gimme_a_subarray.deallocate()

@then("subarray should go into OFF state")
def subarray_state_OFF(i_can_haz_telescope, gimme_a_subarray, show_tmc_subarray_state,
                       show_csp_subarray_state, show_sdp_subarray_state ):
    logging.info("Now deallocating resources ... ")
    logging.info("TMC subarray state: " + show_tmc_subarray_state.get("State"))
    time.sleep(5)
    logging.info("CSP subarray state: " + show_csp_subarray_state.get("State"))
    logging.info("SDP subarray state: " + show_sdp_subarray_state.get("State"))

    watch_receptorIDList = watch(show_tmc_subarray_state).for_a_change_on("receptorIDList")

    # gather info
    receptorIDList_val = watch_receptorIDList.get_value_when_changed()

    # Confirm
    assert_that(show_tmc_subarray_state.get("State") == "OFF")
    assert_that(show_csp_subarray_state.get("State") == "OFF")
    assert_that(show_sdp_subarray_state.get("State") == "OFF")

    assert_that(show_tmc_subarray_state.get("obsState")).is_equal_to("IDLE")
    assert_that(show_csp_subarray_state.get("obsState")).is_equal_to("IDLE")
    assert_that(show_sdp_subarray_state.get("obsState")).is_equal_to("IDLE")
    assert_that(receptorIDList_val == [])

    # Confirm
    logging.info("Subarry is now deallocated")

    # put telescope to standby
    i_can_haz_telescope.standby()


