#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-966
----------------------------------
Scheduling Block Test for OET
"""
import enum
import logging
from os import environ
import time
from multiprocessing import Process, Manager

import pytest
from assertpy import assert_that
# SUT import
from oet.procedure.application.restclient import RestClientUI
from pytest_bdd import given, parsers, scenario, then, when

from resources.test_support.controls import (restart_subarray,
                                             set_telescope_to_running,
                                             set_telescope_to_standby,
                                             take_subarray,
                                             telescope_is_in_standby)
from resources.test_support.helpers import resource

# local imports


DEV_TEST_TOGGLE = environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True
# used as labels within the result fixture
# this should be refactored at some point to something more elegant
SUT_EXECUTED = 'SUT executed'
TEST_PASSED = 'Test Passed'
STATE_CHECK = "State Transitions"
OET_TASK_ID = 'OET Task ID'
SCHEDULING_BLOCK = 'Scheduling Block'
SUBARRAY = 'Subarray Used'

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


@pytest.fixture(name="result")
def fixture_result():
    """structure used to hold details of the intermediate result at each stage of the test
    we also use this to track the task id and the scheduling block - not convinced this
    is the best way to do this, it may make more sense as part of the OET REST CLI fixture.
    """
    fixture = {SUT_EXECUTED: False, TEST_PASSED: True, SCHEDULING_BLOCK: None,
               STATE_CHECK: None, OET_TASK_ID: None}
    yield fixture
    # teardown
    end(fixture[SUBARRAY])


@pytest.fixture(name="oet_rest_cli")
def fixture_rest_client():
    """OET rest client instance used for testing """
    rest_cli = RestClientUI("http://oet-rest:5000/api/v1.0/procedures")
    yield rest_cli


class Subarray:

    resource = None

    def __init__(self, device):
        self.resource = resource(device)

    def get_obsstate(self):
        return self.resource.get('obsState')

    def get_state(self):
        return self.resource.get('State')

    def state_is(self, state):
        current_state = self.get_state()
        return current_state == state

    def obsstate_is(self, state):
        current_state = self.get_obsstate()
        return current_state == state


class Poller:
    proc = None
    device = None
    results = []

    def __init__(self, device):
        self.device = device

    def start_polling(self):
        manager = Manager()
        self.results = manager.list()
        self.proc = Process(target=self.track_obsstates,
                            args=(self.device, self.results,))
        self.proc.start()
        print("Starting")

    def stop_polling(self):
        if self.proc is not None:
            self.proc.terminate()

    def get_results(self):
        return self.results

    def track_obsstates(self, device, recorded_states):
        LOGGER.info("STATE MONITORING: Started Tracking")
        while True:
            current_state = device.get_obsstate()
            if len(recorded_states) == 0 or current_state != recorded_states[-1]:
                LOGGER.info(
                    "STATE MONITORING: State has changed to %s", current_state)
                recorded_states.append(current_state)


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
    """
    Confirm that the script is in a given state and return the ID
    """
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


def attempt_to_clean_subarray_to_idle(subarray: Subarray):
    """
    Ideally the telescope would always be in the same state
    when running the test - this method will cleanup the
    subarray provided to the expected IDLE state where
    this test starts
    """

    if telescope_is_in_standby():
        LOGGER.info("PROCESS: Starting up telescope")
        set_telescope_to_running()
    if subarray.obsstate_is('READY'):
        take_subarray(1).and_end_sb_when_ready().and_release_all_resources()

    LOGGER.info("PROCESS: Telescope is in %s ", subarray.get_obsstate())


def run_task_using_oet_rest_client(oet_rest_cli, script, scheduling_block, additional_json=None):

    oet_task_id = None
    resp = oet_rest_cli.create(script, subarray_id=1)
    # confirm that creating the task worked and we have a valid ID
    oet_task_id = confirm_script_status_and_return_id(resp, 'READY')
    # we  can now start the observing task passing in the scheduling block as a parameter
    if additional_json is not None:
        resp = oet_rest_cli.start(scheduling_block, additional_json)
    else:
        resp = oet_rest_cli.start(scheduling_block)
    # confirm that it didn't fail on starting
    oet_task_id = confirm_script_status_and_return_id(resp, 'RUNNING')

    timeout = DEFAUT_LOOPS_DEFORE_TIMEOUT  # arbitrary number
    while timeout != 0:
        resp = oet_rest_cli.list()
        if not task_has_status(oet_task_id, 'RUNNING', resp):
            LOGGER.info(
                "PROCESS: Task has run to completion - no longer present on task list")
            return True
        time.sleep(PAUSE_BETWEEN_OET_TASK_LIST_CHECKS_IN_SECS)
        timeout -= 1
    # if we get here we timed out so need to fail the test
    return False


# @pytest.mark.select
@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
@scenario("../../../features/XTP-966.feature",
          "Scheduling Block Resource Allocation and Observation")
def test_sb_resource_allocation():
    """Scheduling Block Resource allocation test."""


@given(parsers.parse('the subarray {subarray_name} and the SB {scheduling_block}'))
def setup_telescope(result, subarray_name, scheduling_block):
    """Setup and check the subarray is in the right
    state to begin the test - this will be the first
    state in the list passed in.

    Args:
        result ([type]): fixture used to track progress
        expected_states ([type]): list of expected states
        subarray ([type]): the subarray to be used for the test
    """

    subarray = Subarray(subarray_name)
    attempt_to_clean_subarray_to_idle(subarray)

    # start the track_obsstate function in a separate thread

    poller = Poller(subarray)
    poller.start_polling()

    result[SCHEDULING_BLOCK] = scheduling_block
    result[SUBARRAY] = subarray
    result[STATE_CHECK] = poller


@when(parsers.parse('the OET allocates resources for the SB with the script {script}'))
def allocate_resources(result, oet_rest_cli, script):
    """
    Use the OET Rest API to allocate resources for the Scheduling Block
    """
    LOGGER.info("PROCESS: Allocating resources for the SB %s ",
                result[SCHEDULING_BLOCK])
    result[TEST_PASSED] = run_task_using_oet_rest_client(
        oet_rest_cli,
        script=script,
        scheduling_block=result[SCHEDULING_BLOCK]
    )
    assert result[TEST_PASSED],  "PROCESS: Resource Allocation failed"


@then(parsers.parse('the OET observes the SB with the script {script}'))
def run_scheduling_block(result, oet_rest_cli, script):
    """[summary]

    Args:
        result ([type]): [description]
        oet_rest_cli ([type]): [description]
    """
    LOGGER.info("PROCESS: Starting to observe the SB %s using script %s",
                result[SCHEDULING_BLOCK], script)

    # TODO additional_json seems to be manadatory for configure at the moment but should be optional
    result[TEST_PASSED] = run_task_using_oet_rest_client(
        oet_rest_cli,
        script=script,
        scheduling_block=result[SCHEDULING_BLOCK],
        additional_json='scripts/data/example_configure.json'
    )
    assert result[TEST_PASSED],  "PROCESS: Observation failed"


@then(parsers.parse(
    'the SubArrayNode obsState passes in order through the following states {expected_states}'
))
def check_transitions(expected_states, result):
    """Check that the device passed through the expected
    obsState transitions. This has been being monitored
    on a separate thread in the background.

    The method deliberately pauses at the start to allow TMC time
    to complete any operation still in progress.

    Args:
        result ([type]): [description]
    """

    time.sleep(PAUSE_AT_END_OF_TASK_COMPLETION_IN_SECS)
    expected_states = [x.strip() for x in expected_states.split(',')]

    result[STATE_CHECK].stop_polling()
    recorded_states = result[STATE_CHECK].get_results()

    # ignore 'READY' as it can be a transitory state so we don't rely
    # on it being present in the list to be matched
    recorded_states = list(filter(('READY').__ne__, recorded_states))
    result[TEST_PASSED] = False
    LOGGER.info("Comparing the list of states observed with the expected states")
    for expected_state, recorded_state in zip(expected_states, recorded_states):
        LOGGER.info("Expected %s was %s ", expected_state, recorded_state)
        assert expected_state == recorded_state, "State observeed was not as expected"
    LOGGER.info("All states match")
    result[TEST_PASSED] = True


def end(subarray: Subarray):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if subarray is not None:
        if (subarray.state_is("ON")) and (subarray.obsstate_is("IDLE")):
            LOGGER.info("CLEANUP: tearing down composed subarray (IDLE)")
            take_subarray(1).and_release_all_resources()
        if subarray.obsstate_is("READY"):
            LOGGER.info("CLEANUP: tearing down configured subarray (READY)")
            take_subarray(1).and_end_sb_when_ready(
            ).and_release_all_resources()
        if subarray.obsstate_is("CONFIGURING"):
            LOGGER.warning(
                "Subarray is still in CONFIFURING! Please restart MVP manualy to complete tear down")
            restart_subarray(1)
            # raise exception since we are unable to continue with tear down
            raise Exception("Unable to tear down test setup")
        if subarray.obsstate_is("SCANNING"):
            LOGGER.warning(
                "Subarray is still in SCANNING! Please restart MVP manualy to complete tear down")
            restart_subarray(1)
            # raise exception since we are unable to continue with tear down
            raise Exception("Unable to tear down test setup")
        set_telescope_to_standby()
        LOGGER.info("CLEANUP: Telescope is in %s ",
                    subarray.get_obsstate())
