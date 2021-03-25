#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-966
----------------------------------
Scheduling Block Test for OET
"""
import logging
import time
import pytest

from pytest_bdd import given, parsers, scenario, then, when
from resources.test_support.controls import (restart_subarray,
                                             set_telescope_to_running,
                                             set_telescope_to_standby,
                                             take_subarray,
                                             telescope_is_in_standby)

from resources.test_support.oet_helpers import Subarray, Poller, ScriptExecutor

# used as labels within the oet_result fixture
# this should be refactored at some point to something more elegant
SUT_EXECUTED = 'SUT executed'
TEST_PASSED = 'Test Passed'
STATE_CHECK = "State Transitions"
OET_TASK_ID = 'OET Task ID'
SCHEDULING_BLOCK = 'Scheduling Block'
SUBARRAY = 'Subarray Used'

EXECUTOR = ScriptExecutor()

LOGGER = logging.getLogger(__name__)


@pytest.fixture()
def oet_result():
    """structure used to hold details of the intermediate result at each stage of the test
    we also use this to track the task id and the scheduling block - not convinced this
    is the best way to do this, it may make more sense as part of the OET REST CLI fixture.
    """
    fixture = {SUT_EXECUTED: False, TEST_PASSED: False, SCHEDULING_BLOCK: None,
               STATE_CHECK: None, OET_TASK_ID: None, SUBARRAY: None}
    yield fixture
    # teardown
    end(fixture[SUBARRAY])


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


@pytest.mark.skamid
@scenario("XTP-966.feature",
          "SKA Mid Scheduling Block - Resource allocation and observation")
def test_sb_resource_allocation():
    """Scheduling Block Resource allocation test."""


@given(parsers.parse('the subarray {subarray_name} and the SB {scheduling_block}'))
def setup_telescope(oet_result, subarray_name, scheduling_block):
    """Setup and check the subarray is in the right
    state to begin the test - this will be the first
    state in the list passed in.

    Args:
        oet_result (dict): fixture used to track progress
        subarray_name (str): Sub-array ID
        scheduling_block (str): file path to SB JSON file
    """
    subarray = Subarray(subarray_name)
    attempt_to_clean_subarray_to_empty(subarray)

    # start the track_obsstate function in a separate thread
    poller = Poller(subarray)
    poller.start_polling()

    oet_result[STATE_CHECK] = poller
    oet_result[SCHEDULING_BLOCK] = scheduling_block
    oet_result[SUBARRAY] = subarray


@when(parsers.parse('the OET allocates resources for the SB with the script {script}'))
def allocate_resources(oet_result, script):
    """
    Use the OET Rest API to allocate resources for the Scheduling Block

    Args:
        oet_result (dict): fixture used to track progress
        script (str): file path to an observing script
    """
    LOGGER.info("PROCESS: Creating SBI from SB %s ",
                oet_result[SCHEDULING_BLOCK])

    # create Scheduling Block Instance so that the same SB ID is maintained through
    # resource allocation and observation execution
    oet_result[TEST_PASSED] = EXECUTOR.execute_script(
        script='file://scripts/create_sbi.py',
        scheduling_block=oet_result[SCHEDULING_BLOCK]
    )
    assert oet_result[TEST_PASSED],  "PROCESS: SBI creation failed"

    LOGGER.info("PROCESS: Allocating resources for the SB %s ",
                oet_result[SCHEDULING_BLOCK])
    oet_result[TEST_PASSED] = EXECUTOR.execute_script(
        script=script,
        scheduling_block=oet_result[SCHEDULING_BLOCK]
    )
    assert oet_result[TEST_PASSED],  "PROCESS: Resource Allocation failed"


@then(parsers.parse('the OET observes the SB with the script {script}'))
def run_scheduling_block(oet_result, script):
    """
    Use the OET Rest API to observe the SBI

    Args:
        oet_result (dict): fixture used to track progress
        script (str): path to the script file to be run
    """
    LOGGER.info("PROCESS: Starting to observe the SB %s using script %s",
                oet_result[SCHEDULING_BLOCK], script)

    oet_result[TEST_PASSED] = EXECUTOR.execute_script(
        script=script,
        scheduling_block=oet_result[SCHEDULING_BLOCK]
    )
    assert oet_result[TEST_PASSED],  "PROCESS: Observation failed"


@then(parsers.parse(
    'the SubArrayNode obsState passes in order through the following states {expected_states}'
))
def check_transitions(oet_result, expected_states):
    """Check that the device passed through the expected
    obsState transitions.

    Args:
        oet_result (dict): fixture used to track progress
        expected_states (str): String containing states sub-array is expected to have
        passed through, separated by a comma
    """
    expected_states = [x.strip() for x in expected_states.split(',')]
    assert oet_result[STATE_CHECK].state_transitions_match(expected_states)
    oet_result[TEST_PASSED] = True


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
        LOGGER.info("CLEANUP: Sub-array is in %s ",
                    subarray.get_obsstate())
