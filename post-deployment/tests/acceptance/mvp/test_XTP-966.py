#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-966
----------------------------------
Scheduling Block Test for OET
"""
import os

import logging
from multiprocessing.pool import ThreadPool

import re
import enum
import time
from typing import List

import pytest

from assertpy import assert_that
from pytest_bdd import scenario, given, when, then, parsers


# SUT import
from oet.procedure.application.restclient import RestClientUI

# local imports

from resources.test_support.helpers import resource
from resources.test_support.logging_decorators import log_it
from resources.test_support.controls import set_telescope_to_standby, set_telescope_to_running
from resources.test_support.controls import restart_subarray, telescope_is_in_standby, take_subarray

DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True
# used as labels within the result fixture
# this should be refactored at some point to something more elegant
SUT_EXECUTED = 'SUT executed'
TEST_PASSED = 'Test Passed'
SUBARRAY_USED = "subarray"
STATE_CHECK = "State Transitions"
OET_TASK_ID = 'OET Task ID'

# test tuning parameters
# arbitrary number, this only needs to be this big to cover a science scan of several seconds
DEFAUT_LOOPS_DEFORE_TIMEOUT = 10000
# avoids swamping the rest server but short enough to avoid delaying the test
PAUSE_BETWEEN_OET_TASK_LIST_CHECKS_IN_SECS = 5
# OET task completion can occur before TMC has completed its activity - so allow time for the
# last transitions to take place
PAUSE_AT_END_OF_TASK_COMPLETION_IN_SECS = 10


class ObsState(enum.Enum):
    """
    Represent the ObsState Tango enumeration
    TODO: Refactor this as a useful shared class
    """
    EMPTY = 0
    RESOURCING = 1
    IDLE = 2
    CONFIGURING = 3
    READY = 4
    SCANNING = 5
    ABORTING = 6
    ABORTED = 7
    RESETTING = 8
    FAULT = 9
    RESTARTING = 10

    def __str__(self):
        """
        Convert enum to string
        """
        # str(ObsState.IDLE) gives 'IDLE'
        return str(self.name)


devices_to_log = [
    'ska_mid/tm_subarray_node/1',
    'mid_csp/elt/subarray_01',
    'mid_csp_cbf/sub_elt/subarray_01',
    'mid_sdp/elt/subarray_1',
    'mid_d0001/elt/master',
    'mid_d0002/elt/master',
    'mid_d0003/elt/master',
    'mid_d0004/elt/master']
non_default_states_to_check = {
    'mid_d0001/elt/master': 'pointingState',
    'mid_d0002/elt/master': 'pointingState',
    'mid_d0003/elt/master': 'pointingState',
    'mid_d0004/elt/master': 'pointingState'}


@pytest.fixture(name="result")
def fixture_result():
    """structure used to hold details of the intermediate result at each stage of the test
    we also use this to track the task id - not convinced this is the best way to do
    this, it may make more sense as part of the OET REST CLI fixture.
    """
    fixture = {SUT_EXECUTED: False, TEST_PASSED: True,
               SUBARRAY_USED: None, STATE_CHECK: None, OET_TASK_ID: None}
    yield fixture
    # teardown
    end()


@pytest.fixture(name="oet_rest_cli")
def fixture_rest_client():
    """OET rest client instance used for testing """
    rest_cli = RestClientUI("http://oet-rest:5000/api/v1.0/procedures")
    yield rest_cli


def get_obsstate(device: str):
    """Get the current state of the device

    Args:
        device (str): id of the subarray to be checked

    Returns:
        str : Current state of the device
    """
    return resource(device).get('obsState')


def become_expected_state(device: str, expected_state: ObsState, timeout=DEFAUT_LOOPS_DEFORE_TIMEOUT):
    """Wait for the subarray to transition to the expected state

    Args:
        device (str): device to check
        expected_state (ObsState): expected state
        timeout (int, optional): time to wait for transiution before failing 

    Returns:
        [type]: [description]
    """
    last_state = get_obsstate(device)
    if last_state == expected_state:
        msg = "STATE MONITORING: State has changed to " + " obsState :" + last_state
        LOGGER.info(msg)
        return True
    while timeout != 0:
        current_state = get_obsstate(device)
        if current_state != last_state:
            if current_state == 'READY' and expected_state != 'READY':
                LOGGER.info(
                    "STATE MONITORING: State has changed to %s - counting as transitory",
                    current_state)
                last_state = current_state
            else:
                LOGGER.info(
                    "STATE MONITORING: State has changed to %s", current_state)
                return current_state == expected_state
        timeout -= 1
    LOGGER.info(
        "STATE MONITORING: Timeout occured before expected sequence complete")
    return False


def track_obsstates(device: str, obstate_flow: List[ObsState], timeout=DEFAUT_LOOPS_DEFORE_TIMEOUT):
    """For a given list of obs states will track the state chnges on the
    device to confirm that the state chages to the next one on the list
    if a change that doesn't match the predicted order is detected then
    it returns False

    Args:
        device (str): device id for the subarray or other device being tracked
        obstate_flow (List[ObsState]): list of states in order
        timeout (int, optional): time to wait for transiution before failing . 

    Returns:
        result (boolean): True if all states were matched, 
                          False if the expecte order is not followed
    """
    for obs_state in obstate_flow:
        msg = "STATE MONITORING: Waiting for state obsState :" + obs_state
        LOGGER.info(msg)
        if not become_expected_state(device, obs_state, timeout):
            return False
    return True


def parse_rest_response(resp):
    """Split the response from the REST API lines
    into columns

    Args:
        resp (string): [description]

    Returns:
        [rest_response_object]: [description]
    """
    rest_responses = []
    lines = resp.splitlines()
    del lines[0:2]
    for line in lines:
        elements = line.split()
        rest_response_object = {
            'id': elements[0],
            'uri': elements[1],
            'script': elements[2],
            'state': elements[3]}
        rest_responses.append(rest_response_object)
    return rest_responses


def get_task_status(task, resp):
    """Extract a status for a task from the list
    If it isn't on the list return None so we can trap
    if we need to

    Args:
        task (str): Task ID being hunted for
        resp (str): The response message to be parsed

    Returns:
        [str]: The current OET status of the task
    """
    rest_responses = parse_rest_response(resp)
    result_for_task = [x['state'] for x in rest_responses if x['id'] == task]
    if len(result_for_task) == 0:
        return None
    task_status = result_for_task[0]
    LOGGER.debug("Task Status is : %s", task_status)
    return task_status


def task_has_status(task, expected_status, resp):
    """Confirm the task is in the expected status by
    querying the OET client

    Args:
        task (str): OET ID for the task
        expected_status (str): Expected status 
        resp ([type]): [description]

    Returns:
        [type]: [description]
    """
    return get_task_status(task, resp) == expected_status


def confirm_script_status_and_return_id(resp, expected_status='READY'):

    details = parse_rest_response(resp)
    assert_that(
        len(details), "Expected a valid reply when creating the script").is_equal_to(1)
    resp_state = details[0].get('state')
    assert_that(
        resp_state,
        "The script status did not match the expected state"
    ).is_equal_to(expected_status)
    script_id = details[0].get('id')
    return script_id


LOGGER = logging.getLogger(__name__)


def subarray_is(state):
    current_state = resource('ska_mid/tm_subarray_node/1').get("obsState")
    return (current_state == state)


@pytest.mark.select
# @pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
@scenario("../../../features/XTP-966.feature", "Scheduling Block Resource allocation")
def test_sb_resource_allocation():
    """Scheduling Block Resource allocation test."""


@given(parsers.parse('the subarray {subarray} and the expected states {ex_states}'))
def setup_telescope(result, subarray, ex_states):
    """Setup and check the subarray is in the right
    state to begin the test - this will be the first
    state in the list passed in.

    Args:
        result ([type]): fixture used to track progress
        expected_states ([type]): list of expected states
        subarray ([type]): the subarray to be used for the test
    """

    #expected_states = [map(str.strip, expected_states.split(','))]
    expected_states = re.split(' *, *', ex_states.strip())

    attempt_to_clean_subarray_to_idle()

    # if the subarray is not in the expected initial state
    # then we fail the test without doing anything else
    intial_subarray_state = get_obsstate(subarray)
    assert_that(
        intial_subarray_state,
        "Expected subarray to be in the right initial state"
    ).is_equal_to(expected_states[0])

    # start the track_obsstate function in a separate thread
    pool = ThreadPool(processes=1)
    result[SUBARRAY_USED] = subarray
    result[STATE_CHECK] = pool.apply_async(
        track_obsstates, (subarray, expected_states))


def attempt_to_clean_subarray_to_idle():
    """
    Ideally the telescope would always be in the same state
    when running the test - this method will cleanup the 
    subarray provided to the expected IDLE state where 
    this test starts 
    """
    if telescope_is_in_standby():
        LOGGER.info("PROCESS: Starting up telescope")
        set_telescope_to_running()
    if subarray_is('READY'):
        take_subarray(1).and_end_sb_when_ready().and_release_all_resources()

    LOGGER.info("PROCESS: Telescope is in %s ",
                resource('ska_mid/tm_subarray_node/1').get("obsState"))


@when(parsers.parse(
    'the OET allocates resources with the script {script} for the SB {scheduling_block}'
))
def allocate_resources(result, oet_rest_cli, script, scheduling_block):
    LOGGER.info("PROCESS: Allocating resources for the SB %s ",
                scheduling_block)
    resp = oet_rest_cli.create(script, subarray_id=1)
    # confirm that create worked and we have a valid id
    result[OET_TASK_ID] = confirm_script_status_and_return_id(resp, 'READY')
    # we  can now start the observing task passing in the scheduling block as a parameter
    resp = oet_rest_cli.start(scheduling_block)
    # confirm that it didn't fail on starting
    result[OET_TASK_ID] = confirm_script_status_and_return_id(resp, 'RUNNING')
    timeout = DEFAUT_LOOPS_DEFORE_TIMEOUT
    while timeout != 0:
        if not task_is_running(result[OET_TASK_ID], oet_rest_cli):
            LOGGER.info("PROCESS: Allocation of resources is complete")
            result[TEST_PASSED] = True
            return result[TEST_PASSED]
        time.sleep(PAUSE_BETWEEN_OET_TASK_LIST_CHECKS_IN_SECS)
        timeout -= 1
    LOGGER.info("PROCESS Timeout waiting for task to complete")
    result[TEST_PASSED] = False
    return result[TEST_PASSED]


@then(parsers.parse(
    'the OET observes the SB {scheduling_block} with the script {script}'
))
@log_it('XTP-966', devices_to_log, non_default_states_to_check)
def run_scheduling_block(scheduling_block, script, result, oet_rest_cli):
    """[summary]

    Args:
        result ([type]): [description]
        oet_rest_cli ([type]): [description]
    """
    LOGGER.info("PROCESS: Starting to observe the SB %s using script %s",
                scheduling_block, script)
    resp = oet_rest_cli.create(script, subarray_id=1)
    # confirm that create worked and we have a valid id
    result[OET_TASK_ID] = confirm_script_status_and_return_id(resp, 'READY')
    # we  can now start the observing task passing in the scheduling block as a parameter
    resp = oet_rest_cli.start(
        scheduling_block, 'scripts/data/example_configure.json')
    # confirm that it didn't fail on starting
    result[OET_TASK_ID] = confirm_script_status_and_return_id(resp, 'RUNNING')


def task_is_running(task, oet_rest_cli):
    """Use the OET REST API to confirm the task with the given id
    is running

    Args:
        task ([type]): [description]
        oet_rest_cli ([type]): [description]

    Returns:
        [type]: [description]
    """
    resp = oet_rest_cli.list()
    return task_has_status(task, 'RUNNING', resp)


@then('the task runs to completion')
def check_task_completed(result, oet_rest_cli):
    """Confirm the task completes
    The task can be counted as completing when
    it is no longer visible on the OET client

    At the moment this is done by polling and
    checking the list an arbitrary timeout

    Args:
        result ([type]): [description]
        oet_rest_cli ([type]): the OET REST API
    """
    timeout = DEFAUT_LOOPS_DEFORE_TIMEOUT  # arbitrary number
    while timeout != 0:
        if not task_is_running(result[OET_TASK_ID], oet_rest_cli):
            LOGGER.info(
                "PROCESS: Task has run to completion - no longer present on task list")
            result[TEST_PASSED] = True
            return
        time.sleep(PAUSE_BETWEEN_OET_TASK_LIST_CHECKS_IN_SECS)
        timeout -= 1
    # if we get here we timed out so need to fail the test
    result[TEST_PASSED] = False


@then('the SubArrayNode ObsState passed through the expected states')
def check_transitions(result):
    """Check that the device passed through the expected
    obsState transitions. This has been being monitored
    on a separate thread in the background.

    The method deliberately pauses at the start to allow TMC time 
    to complete any operation still in progress.

    Args:
        result ([type]): [description]
    """

    time.sleep(PAUSE_AT_END_OF_TASK_COMPLETION_IN_SECS)
    thread_result = result[STATE_CHECK].get()
    result[TEST_PASSED] = thread_result
    assert thread_result


def end():
    """ teardown any state that was previously setup with a setup_function
    call.
    """

    if (resource('ska_mid/tm_subarray_node/1').get('State') == "ON") and (subarray_is("IDLE")):
        LOGGER.info("CLEANUP: tearing down composed subarray (IDLE)")
        take_subarray(1).and_release_all_resources()
    if subarray_is("READY"):
        LOGGER.info("CLEANUP: tearing down configured subarray (READY)")
        take_subarray(1).and_end_sb_when_ready().and_release_all_resources()
    if subarray_is("CONFIGURING"):
        LOGGER.warning(
            "Subarray is still in CONFIFURING! Please restart MVP manualy to complete tear down")
        restart_subarray(1)
        # raise exception since we are unable to continue with tear down
        raise Exception("Unable to tear down test setup")
    if subarray_is("SCANNING"):
        LOGGER.warning(
            "Subarray is still in SCANNING! Please restart MVP manualy to complete tear down")
        restart_subarray(1)
        # raise exception since we are unable to continue with tear down
        raise Exception("Unable to tear down test setup")
    set_telescope_to_standby()
    LOGGER.info("CLEANUP: Telescope is in %s ",
                resource('ska_mid/tm_subarray_node/1').get("obsState"))
