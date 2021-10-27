#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-2328
----------------------------------
Tests for allocating resources from JSON (XTP-2325)
and configure subarray and observe scan (XTP-2330)
"""
import logging

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from resources.test_support.controls import (restart_subarray,
                                             set_telescope_to_running,
                                             set_telescope_to_standby,
                                             take_subarray,
                                             telescope_is_in_standby,
                                             tmc_is_on)
from resources.test_support.helpers import resource
from resources.test_support.oet_helpers import ScriptExecutor, ObsStateRecorder

# used as labels within the oet_result fixture
# this should be refactored at some point to something more elegant
SUBARRAY_USED = 'subarray_node'
SCHEDULING_BLOCK = 'Scheduling Block'
STATE_CHECK = 'State Transitions'

EXECUTOR = ScriptExecutor()

LOGGER = logging.getLogger(__name__)


@pytest.fixture(name="result")
def fixture_result():
    """structure used to hold details of the intermediate result at each stage of the test"""
    fixture = {SUBARRAY_USED: 'ska_mid/tm_subarray_node/1',
               SCHEDULING_BLOCK: None,
               STATE_CHECK: None}
    yield fixture
    # teardown
    end(fixture)


def end(result):
    """ teardown any state that was previously setup for the tests.

    Args:
        result (dict): fixture to track test state
    """
    subarray = resource(result[SUBARRAY_USED])
    obsstate = subarray.get('obsState')
    LOGGER.info("CLEANUP: Sub-array in obsState %s ", obsstate)
    if obsstate == "IDLE":
        LOGGER.info("CLEANUP: tearing down composed subarray (IDLE)")
        take_subarray(1).and_release_all_resources()
    if obsstate == "READY":
        LOGGER.info("CLEANUP: tearing down configured subarray (READY)")
        take_subarray(1).and_end_sb_when_ready(
        ).and_release_all_resources()
    if subarray.get('obsState') != "EMPTY":
        LOGGER.warning(
            "Subarray is still in %s Please restart MVP manually to complete tear down",
            obsstate)
        restart_subarray(1)
        # raise exception since we are unable to continue with tear down
        raise Exception("Unable to tear down test setup")
    if not telescope_is_in_standby():
        set_telescope_to_standby()
    LOGGER.info("CLEANUP: Sub-array is in %s ",
                subarray.get('obsState'))


@pytest.mark.skip
@pytest.mark.oetmid
@pytest.mark.skamid
@pytest.mark.quarantine
@scenario("XTP-2328.feature", "Allocating resources without an SBI")
def test_resource_allocation_without_sbi():
    """
    Given sub-array is in ObsState EMPTY
    When I tell the OET to allocate resources using script file:///app/scripts/allocate_from_file.py
     and scripts/data/example_allocate.json
    Then the sub-array goes to ObsState IDLE
    """


@pytest.mark.skip
@pytest.mark.oetmid
@pytest.mark.skamid
@pytest.mark.quarantine
@scenario("XTP-2328.feature", "Configuring a subarray and performing scan without an SBI")
def test_observing_without_sbi():
    """
    Given A running telescope with 2 dishes are allocated to sub-array for executing observations
    When I tell the OET to configure a sub-array and perform scan using script
    file:///app/scripts/observe.py and scripts/data/example_configure.json
    Then the sub-array passes through ObsStates IDLE, CONFIGURING, SCANNING, IDLE
    """


@given('sub-array is in ObsState EMPTY')
def start_up_telescope(result):
    LOGGER.info("Before starting the telescope checking if the TMC is in ON state")
    assert(tmc_is_on())
    if telescope_is_in_standby():
        LOGGER.info("PROCESS: Starting up telescope")
        set_telescope_to_running()

    subarray_state = resource(result[SUBARRAY_USED]).get('obsState')
    assert subarray_state == 'EMPTY', \
        f"Expected sub-array to be in EMPTY but instead was in {subarray_state}"
    LOGGER.info("Sub-array is in ObsState EMPTY")


@given('A running telescope with 2 dishes are allocated to sub-array for executing observations')
def allocate_resources():
    """
    setting up running telescope with 2 dishes are allocated
    """
    LOGGER.info("Before starting the telescope checking if the TMC is in ON state")
    assert(tmc_is_on())
    LOGGER.info("Before starting the telescope checking if the telescope is in StandBy")
    if telescope_is_in_standby():
        LOGGER.info("Starting up telescope")
        set_telescope_to_running()
        LOGGER.info("Telescope started")
    LOGGER.info("Assigning 2 dishes to subarray 1")
    take_subarray(1).to_be_composed_out_of(2)
    LOGGER.info("Resources are successfully assigned to subarray 1.")


@when(parsers.parse('I tell the OET to allocate resources using script {script} and {allocate_json}'))
def when_allocate_resources_from_file(script, allocate_json):
    """
    Use the OET Rest API to run script that allocates resources from given JSON.

    Args:
        script (str): file path to an observing script
        allocate_json (str): file path to a allocate json
    """

    script_completion_state = EXECUTOR.execute_script(
        script,
        allocate_json,
        timeout=300
    )
    assert script_completion_state == 'COMPLETED', \
        f"Expected resource allocation script to be COMPLETED, instead was {script_completion_state}"


@when(
    parsers.parse('I tell the OET to configure a sub-array and perform scan for duration {duration} sec using script '
                  '{script} and {configure_json}'))
def observe_without_sbi(duration, script, configure_json, result):
    """
    Use the OET Rest API to observe using observing script and Configure JSON

    Args:
        duration (float): scan duration time
        script (str): file path to an observing script
        configure_json (str): file path to a configuree json
        result (dict): fixture used to track progress
    """
    subarray_url = result[SUBARRAY_USED]
    recorder = ObsStateRecorder(subarray_url)
    recorder.start_recording()
    result[STATE_CHECK] = recorder

    script_completion_state = EXECUTOR.execute_script(
        script,
        configure_json,
        float(duration),
        timeout=300
    )
    assert script_completion_state == 'COMPLETED', \
        f"Expected observation script to be COMPLETED, instead was {script_completion_state}"


@then(parsers.parse('the sub-array goes to ObsState {obsstate}'))
def check_final_subarray_state(obsstate, result):
    """
    Check that the final state of the sub-array is as expected.

    Args:
        obsstate (str): Sub-array Tango device ObsState
        result (dict): fixture used to track progress
    """
    subarray_state = resource(result[SUBARRAY_USED]).get('obsState')
    assert subarray_state == obsstate, \
        f"Expected sub-array to be in {obsstate} but instead was in {subarray_state}"
    LOGGER.info("Sub-array is in ObsState %s", obsstate)


@then(parsers.parse('the sub-array passes through ObsStates {expected_states}'))
def check_transitions(expected_states, result):
    """
    Check that the device passed through the expected obsState transitions.

    Args:
        expected_states (str): String containing states sub-array is expected to have
        passed through, separated by a comma
        result (dict): fixture used to track progress
    """
    expected_states = [x.strip() for x in expected_states.split(',')]
    recorder: ObsStateRecorder = result[STATE_CHECK]
    recorder.stop_recording()
    recorder.state_transitions_match(expected_states)
