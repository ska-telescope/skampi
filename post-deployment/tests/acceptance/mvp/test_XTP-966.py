#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-966
----------------------------------
Scheduling Block Test for OET
"""

import logging
from multiprocessing.pool import ThreadPool


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
#from resources.test_support.logging_decorators import log_it
#from resources.test_support.controls import set_telescope_to_standby, set_telescope_to_running
#from resources.test_support.controls import telescope_is_in_standby, take_subarray

# used as labels within the result fixture
# this should be refactored at some point to something more elegant
SUT_EXECUTED = 'SUT executed'
TEST_PASSED = 'Test Passed'
SUBARRAY_USED = "subarray"
STATE_CHECK = "State Transitions"
OET_TASK_ID = 'OET Task ID'


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
    end(fixture)


@pytest.fixture(name="oet_rest_cli")
def fixture_rest_client():
    """OET rest client instance used for testing """
    rest_cli = RestClientUI("http://rest-oet-test:5000/api/v1.0/procedures")
    yield rest_cli


def get_obsstate(device: str):
    """Get the current state of the device

    Args:
        device (str): id of the subarray to be checked

    Returns:
        str : Current state of the device
    """
    return resource(device).get('obsState')


def become_expected_state(device: str, expected_state: ObsState, timeout=60):
    """Wait for the subarray to transition to the expected state

    Args:
        device (str): device to check
        expected_state (ObsState): expected state
        timeout (int, optional): time to wait for transiution before failing . Defaults to 60.

    Returns:
        [type]: [description]
    """
    last_state = get_obsstate(device)
    if last_state == expected_state:
        return True
    while timeout != 0:
        current_state = get_obsstate(device)
        if current_state != last_state:
            return current_state == expected_state
        time.sleep(0.1)
        timeout -= 1
    return False


def track_obsstates(device: str, obstate_flow: List[ObsState], timeout=60):
    """For a given list of obs states will track the state chnges on the
    device to confirm that the state chages to the next one on the list
    if a change that doesn't match the predicted order is detected then
    it returns False

    Args:
        device (str): device id for the subarray or other device being tracked
        obstate_flow (List[ObsState]): kist of states in order
        timeout (int, optional): time to wait for transiution before failing . Defaults to 60.

    Returns:
        [type]: [description]
    """
    for obs_state in obstate_flow:
        if not become_expected_state(device, obs_state, timeout):
            return False
    return True


def parse_rest_response(resp):
    """Split the response from the REST API lines
    into columns

    Args:
        resp ([type]): [description]

    Returns:
        [type]: [description]
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
        task ([type]): Task ID being hunted for
        resp ([type]): The response message to be parsed

    Returns:
        [type]: The current OET status of the task
    """
    rest_responses = parse_rest_response(resp)
    result_for_task = [x['state'] for x in rest_responses if x['id'] == task]
    if len(result_for_task) == 0:
        return None
    else:
        return result_for_task[0]


def task_has_status(task, expected_status, resp):
    """Confirm the task is in the expected status by
    querying the OET client

    Args:
        task ([type]): [description]
        expected_status ([type]): [description]
        resp ([type]): [description]

    Returns:
        [type]: [description]
    """
    return get_task_status(task, resp) == expected_status


LOGGER = logging.getLogger(__name__)


@pytest.mark.select
@scenario("../../../features/XTP-966.feature", "Scheduling Block Resource allocation")
def test_sb_resource_allocation():
    """Scheduling Block Resource allocation test."""


@given(parsers.parse('the subarray {subarray} and the expected states {expected_states}'))
def setup_telescope_and_scan(result, subarray, expected_states):
    """Setup and check the subarray is in the right
    state to begin the test - this will be the first
    state in the list passed in.

    Args:
        result ([type]): fixture used to track progress
        expected_states ([type]): list of expected states
        subarray ([type]): the subarray to be used for the test
    """

    expected_states = [map(str.strip, expected_states.split(','))]

    # check subarray state is in first state
    # if the subarray is not in the expected initial state
    # then we fail the test without doing anything else
    if not get_obsstate(subarray) == expected_states[0]:
        # fail the test
        return

    # start the track_obsstate function in a separate thread
    pool = ThreadPool(processes=1)
    result[SUBARRAY_USED] = subarray
    result[STATE_CHECK] = pool.apply_async(
        track_obsstates, (subarray, expected_states))


@when(parsers.parse('the OET runs the script {script} passing the SB {scheduling_block} as an argument'))
def run_scheduling_block(script, scheduling_block, result, oet_rest_cli):
    """[summary]

    Args:
        result ([type]): [description]
        oet_rest_cli ([type]): [description]
    """
    resp = oet_rest_cli.create(script)
    # confirm that create worked should be able to use
    # the same method to parse the columns returned as
    # for the list?
    details = parse_rest_response(resp)
    # add aserts to fail if didn't

    resp = oet_rest_cli.start(scheduling_block, 10, 1, 1)
    # confirm that it didn't fail on starting should be able to use
    # the same method to parse the columns returned as
    # for the list?
    details = parse_rest_response(resp)
    # add aserts to fail if didn't start


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
    timeout = 1000  # arbitrary number
    while timeout != 0:
        if not task_is_running(result[OET_TASK_ID], oet_rest_cli):
            result[TEST_PASSED] = True
            return
        time.sleep(0.1)
        timeout -= 1
    # if we get here we timed out so need to fail the test
    result[TEST_PASSED] = False


@then('and the SubArrayNode ObsState passed through the expected <states>')
def check_transitions(result):
    """Check that the device passed through the expected
    obsState transitions. This has been being monitored
    on a separate thread in the background.

    Args:
        result ([type]): [description]
    """
    thread_result = result[STATE_CHECK].get()
    result[TEST_PASSED] = thread_result
    # add assert to confirm the lists match


def end(result):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    LOGGER.info("End of test: Resetting Telescope")
    # whatever we need to do to return the telescope to the
    # starting state
