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
from multiprocessing import Process, Manager, Queue

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

LOGGER = logging.getLogger(__name__)


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
    fixture = {SUT_EXECUTED: False, TEST_PASSED: False, SCHEDULING_BLOCK: None,
               STATE_CHECK: None, OET_TASK_ID: None, SUBARRAY: None}
    yield fixture
    # teardown
    end(fixture[SUBARRAY])


@pytest.fixture(name="oet_rest_cli")
def fixture_rest_client():
    """OET rest client instance used for testing """
    helm_release = environ.get("HELM_RELEASE", "test")
    rest_cli_uri = f"http://oet-rest-{helm_release}:5000/api/v1.0/procedures"
    rest_cli = RestClientUI(rest_cli_uri)
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
    exit_q = None
    results = []

    def __init__(self, device):
        self.device = device

    def start_polling(self):
        manager = Manager()
        self.exit_q = Queue()
        self.results = manager.list()
        self.proc = Process(target=self.track_obsstates,
                            args=(self.device, self.results, self.exit_q))
        self.proc.start()

    def stop_polling(self):
        if self.proc is not None:
            self.exit_q.put(True)
            self.proc.join()

    def get_results(self):
        return self.results

    def track_obsstates(self, device, recorded_states, exit_q):
        LOGGER.info("STATE MONITORING: Started Tracking")
        while exit_q.empty():
            current_state = device.get_obsstate()
            if len(recorded_states) == 0 or current_state != recorded_states[-1]:
                LOGGER.info(
                    "STATE MONITORING: State has changed to %s", current_state)
                recorded_states.append(current_state)


def parse_rest_response_line(line):
    """Split a line from the REST API lines
    into columns

    Args:
        line (string): A line from OET REST CLI response

    Returns:
        rest_response_object: A dicts containing
        information on a script.
    """
    elements = line.split()
    rest_response_object = {
        'id': elements[0],
        'script': elements[1],
        'creation_time': str(elements[2] + ' ' + elements[3]),
        'state': elements[4]}
    return rest_response_object


def parse_rest_response(resp):
    """Split the response from the REST API lines
    into columns

    Args:
        resp (string): Response from OET REST CLI

    Returns:
        [rest_response_object]: List of dicts containing
        information on each script.
    """
    rest_responses = []
    lines = resp.splitlines()
    del lines[0:2]
    for line in lines:
        rest_response_object = parse_rest_response_line(line)
        rest_responses.append(rest_response_object)
    return rest_responses


def parse_rest_start_response(resp):
    """ Split the response from the REST API start
    command into columns.

    This needs to be done separately from other OET REST
    Client responses because starting a script returns a
    Python Generator object instead of a static string.

    Args:
        resp (Generator): Response from OET REST CLI start

    Returns:
        [rest_response_object]: List of dicts containing
        information on each script.
    """
    for line in resp:
        # Only get line with script details (ignore header lines)
        if 'RUNNING' in line:
            return [parse_rest_response_line(line)]
    return []


def get_task_status(task, resp):
    """Extract a status for a task from the list
    If it isn't on the list return None so we can trap
    if we need to

    Args:
        task (str): Task ID being hunted for
        resp (str): The response message to be parsed

    Returns:
        str: The current OET status of the task or
        None if task is not present in resp
    """
    rest_responses = parse_rest_response(resp)
    result_for_task = [x['state'] for x in rest_responses if x['id'] == task]
    if len(result_for_task) == 0:
        return None
    task_status = result_for_task[0]
    LOGGER.debug("Task Status is : %s", task_status)
    return task_status


def task_has_status(task, expected_status, resp):
    """Confirm the task has the expected status by
    querying the OET client

    Args:
        task (str): OET ID for the task (script)
        expected_status (str): Expected script state
        resp (str): Response from OET REST CLI list

    Returns:
        bool: True if task is in expected_status
    """
    return get_task_status(task, resp) == expected_status


def confirm_script_status_and_return_id(resp, expected_status='CREATED'):
    """
    Confirm that the script is in a given state and return the ID

    Args:
        resp (str): Response from OET REST CLI list
        expected_status (str): Expected script state

    Returns:
        str: Task ID
    """
    if expected_status is 'RUNNING':
        details = parse_rest_start_response(resp)
    else:
        details = parse_rest_response(resp)
    assert_that(
        len(details), "Expected details for 1 script, instead got "
                      "details for {} scripts".format(len(details))).is_equal_to(1)
    resp_state = details[0].get('state')
    assert_that(
        resp_state,
        "The script status did not match the expected state"
    ).is_equal_to(expected_status)
    script_id = details[0].get('id')
    return script_id


def attempt_to_clean_subarray_to_empty(subarray: Subarray):
    """
    Ideally the telescope would always be in the same state
    when running the test - this method will cleanup the
    subarray provided to the expected EMPTY state where
    this test starts
    """
    # TODO: this does not cover the case where sub-array is in IDLE and resources need
    #  released. Should there be a general helper function for BDD tests which, if
    #  telescope is not in standby, attempts to set it to standby before every test?
    #  This would make more sense than implementing a new function for each test which
    #  attempts to set the telescope to standby
    if telescope_is_in_standby():
        LOGGER.info("PROCESS: Starting up telescope")
        set_telescope_to_running()
    if subarray.obsstate_is('READY'):
        take_subarray(1).and_end_sb_when_ready().and_release_all_resources()

    LOGGER.info("PROCESS: Sub-array state is %s ", subarray.get_obsstate())


def run_task_using_oet_rest_client(oet_rest_cli, script, scheduling_block):
    resp = oet_rest_cli.create(script, subarray_id=1)
    # confirm that creating the task worked and we have a valid ID
    oet_create_task_id = confirm_script_status_and_return_id(resp, 'CREATED')
    # we  can now start the observing task passing in the scheduling block as a parameter
    resp = oet_rest_cli.start(scheduling_block, listen=False)
    # confirm that it didn't fail on starting
    oet_start_task_id = confirm_script_status_and_return_id(resp, 'RUNNING')

    # If task IDs do not match, wrong script was started
    if oet_create_task_id != oet_start_task_id:
        LOGGER.info("Script IDs did not match, created script with ID %s but started script with ID %s",
                    oet_create_task_id, oet_start_task_id)
        return False

    timeout = DEFAUT_LOOPS_DEFORE_TIMEOUT  # arbitrary number
    while timeout != 0:
        resp = oet_rest_cli.list()
        if not task_has_status(oet_start_task_id, 'RUNNING', resp):
            LOGGER.info(
                "PROCESS: Task has run to completion - no longer present on task list")
            return True
        time.sleep(PAUSE_BETWEEN_OET_TASK_LIST_CHECKS_IN_SECS)
        timeout -= 1
    # if we get here we timed out so need to fail the test
    return False


@pytest.mark.skamid
@scenario("XTP-966.feature",
          "Scheduling Block Resource Allocation and Observation")
def test_sb_resource_allocation():
    """Scheduling Block Resource allocation test."""


@given(parsers.parse('the subarray {subarray_name} and the SB {scheduling_block}'))
def setup_telescope(result, subarray_name, scheduling_block):
    """Setup and check the subarray is in the right
    state to begin the test - this will be the first
    state in the list passed in.

    Args:
        result (dict): fixture used to track progress
        subarray_name (str): Sub-array ID
        scheduling_block (str): file path to SB JSON file
    """

    subarray = Subarray(subarray_name)
    attempt_to_clean_subarray_to_empty(subarray)

    # start the track_obsstate function in a separate thread
    poller = Poller(subarray)
    poller.start_polling()

    result[STATE_CHECK] = poller
    result[SCHEDULING_BLOCK] = scheduling_block
    result[SUBARRAY] = subarray


@when(parsers.parse('the OET allocates resources for the SB with the script {script}'))
def allocate_resources(result, oet_rest_cli, script):
    """
    Use the OET Rest API to allocate resources for the Scheduling Block

    Args:
        result (dict): fixture used to track progress
        oet_rest_cli (RestClientUI):
        script (str): file path to an observing script
    """
    LOGGER.info("PROCESS: Creating SBI from SB %s ",
                result[SCHEDULING_BLOCK])

    # create Scheduling Block Instance so that the same SB ID is maintained through
    # resource allocation and observation execution
    result[TEST_PASSED] = run_task_using_oet_rest_client(
        oet_rest_cli,
        script='file://scripts/create_sbi.py',
        scheduling_block=result[SCHEDULING_BLOCK]
    )
    assert result[TEST_PASSED],  "PROCESS: SBI creation failed"

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
        result (dict): fixture used to track progress
        oet_rest_cli ([type]): [description]
    """
    LOGGER.info("PROCESS: Starting to observe the SB %s using script %s",
                result[SCHEDULING_BLOCK], script)

    result[TEST_PASSED] = run_task_using_oet_rest_client(
        oet_rest_cli,
        script=script,
        scheduling_block=result[SCHEDULING_BLOCK]
    )
    assert result[TEST_PASSED],  "PROCESS: Observation failed"


@then(parsers.parse(
    'the SubArrayNode obsState passes in order through the following states {expected_states}'
))
def check_transitions(result, expected_states):
    """Check that the device passed through the expected
    obsState transitions. This has been being monitored
    on a separate thread in the background.

    The method deliberately pauses at the start to allow TMC time
    to complete any operation still in progress.

    Args:
        result (dict): fixture used to track progress
        expected_states (str): String containing states sub-array is expected to have
        passed through, separated by a comma
    """
    time.sleep(PAUSE_AT_END_OF_TASK_COMPLETION_IN_SECS)

    result[STATE_CHECK].stop_polling()
    expected_states = [x.strip() for x in expected_states.split(',')]
    recorded_states = list(result[STATE_CHECK].get_results())

    # ignore 'READY' as it can be a transitory state so we don't rely
    # on it being present in the list to be matched
    recorded_states = [i for i in recorded_states if i != 'READY']

    result[TEST_PASSED] = False
    LOGGER.info("Comparing the list of states observed with the expected states")
    for expected_state, recorded_state in zip(expected_states, recorded_states):
        LOGGER.info("Expected %s was %s ", expected_state, recorded_state)
        assert expected_state == recorded_state, "State observed was not as expected"
    LOGGER.info("All states match")
    result[TEST_PASSED] = True


def end(subarray: Subarray):
    """ teardown any state that was previously setup with a setup_function
    call.

    Args:
        subarray (Subarray): Subarray object referencing
        sub-array to reset
    """
    if subarray is not None:
        obsstate = subarray.get_obsstate()
        if subarray.state_is("ON") and obsstate == "IDLE":
            LOGGER.info("CLEANUP: tearing down composed subarray (IDLE)")
            take_subarray(1).and_release_all_resources()
        if obsstate == "READY":
            LOGGER.info("CLEANUP: tearing down configured subarray (READY)")
            take_subarray(1).and_end_sb_when_ready(
            ).and_release_all_resources()
        if obsstate in ["CONFIGURING", "SCANNING"]:
            LOGGER.warning(
                "Subarray is still in %s Please restart MVP manually to complete tear down",
                obsstate)
            restart_subarray(1)
            # raise exception since we are unable to continue with tear down
            raise Exception("Unable to tear down test setup")
        set_telescope_to_standby()
        LOGGER.info("CLEANUP: Telescope is in %s ",
                    subarray.get_obsstate())
