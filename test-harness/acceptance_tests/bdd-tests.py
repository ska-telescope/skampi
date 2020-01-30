#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""
import sys

import bdd as bdd

sys.path.append('/app')

import pytest
import logging
from time import sleep
from assertpy import assert_that
from pytest-bdd import scenario, given, when, then

from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from tango import DeviceProxy, DevState
from helpers import wait_for, obsState, resource, watch


@scenario("./path-to-feature-file", "Deallocate Resources")

@given("The telescope is ready")
def i_can_haz_telescope():
    the_telescope = SKAMid()
    logging.info("Starting up telescope ...")
    the_telescope.start_up()
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
def show_csp_master_state():
    sdp_master = resource('mid_sdp/elt/master')
    return sdp_master


@given("a monitor on tmc subarray state")
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
    logging.debug("allocation result :",result)

# @given("check wheather the subarray is correctly allocated")
# def check_resources_allocated(watch_tmc_subarray_state, watch_receptorIDList, resource_alloc_def,
#                               show_tmc_subarray_state, show_csp_subarray_state, show_csp_master_state,
#                               show_sdp_subarray_state):
#     # gather info
#     State_val = watch_State.get_value_when_changed()
#     receptorIDList_val = watch_receptorIDList.get_value_when_changed(20)
#
#     # Confirm that TM_subbarray node has correctly assigned resources
#     assert_that(result).is_equal_to(the_resource_allocation)
#     assert_that(State_val).is_equal_to("ON")
#     assert_that(tmc_subarray_node_01.get('obsState')).is_equal_to('IDLE')
#     assert_that(receptorIDList_val).is_equal_to((1, 2))
#
#     # the following changes must have occurred before the previous
#     # CSP subarray must be in state ON and in obsState IDLE
#     assert_that(csp_subarray_01.get('State')).is_equal_to('ON')
#     assert_that(csp_subarray_01.get('obsState')).is_equal_to('IDLE')
#     assert_that(csp_subarray_01.get('receptors')).is_equal_to((1, 2))
#     assert_that(csp_master.get('receptorMembership')).is_equal_to((1, 1, 0, 0))
#     assert_that(csp_master.get('availableReceptorIDs')).is_equal_to((3, 4))
#     assert_that(csp_subarray_01.get('receptors')).is_equal_to((1, 2))
#
#     # SDP subarray must be in state ON and in Obstate IDLE
#     assert_that(sdp_subarray_01.get('State')).is_equal_to('ON')
#     assert_that(sdp_subarray_01.get('obsState')).is_equal_to('IDLE')


@when("I deallocate the resources")
def deallocate_resources(gimme_a_subarray):
    deallocation = gimme_a_subarray.deallocate()


@then("subarrays should go into OFF state")
def subarray_state_OFF(gimme_a_subarray):
    logging.info("Now deallocating resources ... ")

    # prepare
    watch_State_tmc = watch(show_tmc_subarray_state).for_a_change_on("State")
    watch_State_csp = watch(show_csp_subarray_state).for_a_change_on("State")
    watch_State_sdp = watch(show_sdp_subarray_state).for_a_change_on("State")

    watch_receptorIDList = watch(show_tmc_subarray_state).for_a_change_on("receptorIDList")

    # execute
    gimme_a_subarray.deallocate()

    # gather info
    State_val_tmc = watch_State_tmc.get_value_when_changed()
    State_val_csp = watch_State_csp.get_value_when_changed()
    State_val_sdp = watch_State_sdp.get_value_when_changed()
    receptorIDList_val = watch_receptorIDList.get_value_when_changed()

    # Confirm
    assert_that(State_val_tmc).is_equal_to("OFF")
    assert_that(State_val_csp).is_equal_to("OFF")
    assert_that(State_val_sdp).is_equal_to("OFF")

    assert_that(show_tmc_subarray_state.get("obsState")).is_equal_to("IDLE")
    assert_that(show_csp_subarray_state.get("obsState")).is_equal_to("IDLE")
    assert_that(show_sdp_subarray_state.get("obsState")).is_equal_to("IDLE")

    assert_that(receptorIDList_val).is_equal_to(None)

    # Confirm
    logging.info("Subarry has no allocated resources")

    # put telescope to standby
    i_can_haz_telescope.standby()

