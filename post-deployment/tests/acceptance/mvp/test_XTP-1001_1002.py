#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-1001
----------------------------------
Telescope startup and standby using OET scripts
"""
import logging
import time
import pytest
from assertpy import assert_that
from oet.procedure.application.restclient import RestClientUI
from pytest_bdd import given, parsers, scenario, then, when
from resources.test_support.controls import (restart_subarray,
                                             set_telescope_to_running,
                                             set_telescope_to_standby,
                                             take_subarray,
                                             telescope_is_in_standby)

from resources.test_support.oet_helpers import Subarray, Poller, ScriptExecutor, resource

# used as labels within the oet_result fixture
# this should be refactored at some point to something more elegant
SUT_EXECUTED = 'SUT executed'
TEST_PASSED = 'Test Passed'
STATE_CHECK = "State Transitions"
OET_TASK_ID = 'OET Task ID'
SCHEDULING_BLOCK = 'Scheduling Block'
SUBARRAY = 'Subarray Used'

# OET task completion can occur before TMC has completed its activity - so allow time for the
# last transitions to take place
PAUSE_AT_END_OF_TASK_COMPLETION_IN_SECS = 10

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


@pytest.mark.fast
@pytest.mark.skamid
@scenario("XTP-1001.feature", "Telescope startup and standby")
def test_telescope_startup_and_standby():
    """Telescope startup and standby test."""


@given('telescope is in OFF State')
def set_telescope_in_standby_state():
    """Setup and check the subarray is in the right
    state to begin the test - this will be the first
    state in the list passed in.
    """
    LOGGER.info("PROCESS: Standby Telescope")
    assert (telescope_is_in_standby())
    LOGGER.info("Telescope is in OFF state")


@given('telescope is in ON State')
def set_telescope_in_startup_state():
    """Setup and check the subarray is in the right
    state to begin the test - this will be the first
    state in the list passed in.
    """
    if telescope_is_in_standby():
        LOGGER.info("PROCESS: Start up telescope")
        set_telescope_to_running()
    LOGGER.info("Telescope is in ON state")


@when('I tell the OET to run <script>')
def setup_telescope(oet_result, rest_client, script):
    """
    Use the OET Rest API to setup telescope

    Args:
        oet_result (dict): fixture used to track progress
        rest_client (RestClientUI):
        script (str): file path to an observing script
    """
    LOGGER.info("PROCESS: setting up telescope using oet script %s ",
                script)

    # Telescope startup and standby
    oet_result[TEST_PASSED] = EXECUTOR.run_task_using_oet_rest_client(
        rest_client,
        script=script
    )
    assert oet_result[TEST_PASSED], "PROCESS: Telescope setting up operation failed"


@then('the central node goes to state <state>')
def check_transitions(oet_result, expected_states):
    """Check that the central node device passed through the expected
    obsState transitions.
    The method deliberately pauses at the start to allow TMC time
    to complete any operation still in progress.

    Args:
        oet_result (dict): fixture used to track progress
        expected_states (str): String containing states central node is expected to have
        passed through
    """
    time.sleep(PAUSE_AT_END_OF_TASK_COMPLETION_IN_SECS)
    assert_that(resource('ska_mid/tm_central/central_node').get('obsState')).is_equal_to(expected_states)
    LOGGER.info("All states match")



