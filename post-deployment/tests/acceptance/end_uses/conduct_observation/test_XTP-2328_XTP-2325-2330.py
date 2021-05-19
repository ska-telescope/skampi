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
                                             telescope_is_in_standby)

from resources.test_support.helpers import resource
from resources.test_support.oet_helpers import ScriptExecutor, Poller, Subarray

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
    if obsstate == "IDLE":
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
    if not telescope_is_in_standby():
        set_telescope_to_standby()
    LOGGER.info("CLEANUP: Sub-array is in %s ",
                subarray.get('obsState'))


@pytest.mark.oetmid
@pytest.mark.skamid
@pytest.mark.quarantine
@scenario("XTP-2328.feature", "Allocating resources without an SBI")
def test_resource_allocation():
    """
    Given sub-array is in ObsState EMPTY
    When I tell the OET to allocate resources using script file:///app/scripts/allocate_from_file.py
     and scripts/data/example_allocate.json
    Then the sub-array goes to ObsState IDLE
    """


@pytest.mark.oetmid
@pytest.mark.skamid
@pytest.mark.quarantine
@scenario("XTP-2328.feature", "Configuring a subarray and performing scan without an SBI")
def test_observing_sbi():
    """
    Given OET has allocated resources with file:///app/scripts/allocate_from_file.py
    and scripts/data/example_allocate.json
    When I tell the OET to configure a subarray and perform scan using script
    file:///app/scripts/observe.py and scripts/data/example_configure.json
    Then the sub-array passes through ObsStates IDLE, CONFIGURING, SCANNING, IDLE
    """


@given('sub-array is in ObsState EMPTY')
def start_up_telescope(result):
    if telescope_is_in_standby():
        LOGGER.info("PROCESS: Starting up telescope")
        set_telescope_to_running()

    subarray_state = resource(result[SUBARRAY_USED]).get('obsState')
    assert subarray_state == 'EMPTY', \
        f"Expected sub-array to be in EMPTY but instead was in {subarray_state}"
    LOGGER.info("Sub-array is in ObsState EMPTY")


@given(parsers.parse('OET has allocated resources with {script} and {allocate_json}'))
def allocate_resources_from_sbi(script, allocate_json):
    """
    Use the OET Rest API to run resource allocation script with allocate JSON

    Args:
        script (str): file path to an observing script
        allocate_json (str): file path to a allocate_json
    """
    if telescope_is_in_standby():
        set_telescope_to_running()

    script_completion_state = EXECUTOR.execute_script(
        script,
        allocate_json,
        timeout=60
    )
    assert script_completion_state == 'COMPLETED', \
        f"Expected resource allocation script to be COMPLETED, instead was {script_completion_state}"


@when(parsers.parse('I tell the OET to allocate resources using script {script} and {allocate_json}'))
def when_allocate_resources_from_sbi(script, allocate_json):
    """
    Use the OET Rest API to run script that allocates resources from given JSON.

    Args:
        script (str): file path to an observing script
        allocate_json (str): file path to a allocate json
    """
    script_completion_state = EXECUTOR.execute_script(
        script,
        allocate_json,
        timeout=60
    )
    assert script_completion_state == 'COMPLETED', \
        f"Expected resource allocation script to be COMPLETED, instead was {script_completion_state}"


@when(
    parsers.parse('I tell the OET to configure a subarray and perform scan for duration {duration} sec using script '
                  '{script} and {configure_json}'))
def observe_sbi(duration, script, configure_json, result):
    """
    Use the OET Rest API to observe using observing script and Configure JSON

    Args:
        duration (float): scan duration time
        script (str): file path to an observing script
        configure_json (str): file path to a configuree json
        result (dict): fixture used to track progress
    """
    subarray = Subarray(result[SUBARRAY_USED])
    poller = Poller(subarray)
    poller.start_polling()
    result[STATE_CHECK] = poller

    script_completion_state = EXECUTOR.execute_script(
        script,
        configure_json,
        duration,
        timeout=300
    )
    assert script_completion_state == 'COMPLETED', \
        f"Expected SBI observation script to be COMPLETED, instead was {script_completion_state}"


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
    assert result[STATE_CHECK].state_transitions_match(expected_states)
