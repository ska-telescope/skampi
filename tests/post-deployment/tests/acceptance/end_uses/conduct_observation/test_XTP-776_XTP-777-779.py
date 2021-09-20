#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-776
----------------------------------
SKA-Mid tests for creating SBI (XTP-779), allocating resources from SBI (XTP-777)
and observing SBI (XTP-778)
"""
import logging
import os

import pytest
import requests
from pytest_bdd import given, parsers, scenario, then, when

from resources.test_support.controls import (set_telescope_to_running,
                                             set_telescope_to_standby,
                                             take_subarray,
                                             restart_subarray,
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


@pytest.mark.oetmid
@pytest.mark.skamid
@scenario("XTP-776.feature", "Creating a new SBI with updated SB IDs and PB IDs")
def test_sbi_creation():
    """
    Given the SKUID service is running
    When I tell the OET to run file:///app/scripts/create_sbi.py using scripts/data/example_sb.json
    Then the script completes successfully
    """


@pytest.mark.skip
@pytest.mark.oetmid
@pytest.mark.skamid
@pytest.mark.quarantine
@scenario("XTP-776.feature", "Allocating resources with a SBI")
def test_resource_allocation():
    """
    Given sub-array is in ObsState EMPTY
    And the OET has used file:///app/scripts/create_sbi.py to create SBI scripts/data/example_sb.json
    When I tell the OET to allocate resources using script file:///app/scripts/allocate_from_file_sb.py
      and SBI scripts/data/example_sb.json
    Then the sub-array goes to ObsState IDLE
    """


@pytest.mark.skip
@pytest.mark.oetmid
@pytest.mark.skamid
@pytest.mark.quarantine
@scenario("XTP-776.feature", "Observing a Scheduling Block")
def test_observing_sbi():
    """
    Given the OET has used file:///app/scripts/create_sbi.py to create SBI scripts/data/example_sb.json
    And OET has allocated resources with file:///app/scripts/allocate_from_file_sb.py and scripts/data/example_sb.json
    When I tell the OET to observe SBI scripts/data/example_sb.json using script file:///app/scripts/observe_sb.py
    Then the sub-array passes through ObsStates IDLE, CONFIGURING, SCANNING, CONFIGURING, SCANNING, CONFIGURING,
      SCANNING, CONFIGURING, SCANNING, IDLE
    """


@given('the SKUID service is running')
def check_skuid_service_is_running(result):
    """
    Check that the SKA UID service is reachable at SKUID_URL environment variable.
    """
    skuid_url = os.environ["SKUID_URL"]
    if not skuid_url.startswith("http"):
        skuid_url = "http://" + skuid_url
    LOGGER.info("Checking SKUID is running at %s", skuid_url)
    resp = requests.get(skuid_url)
    assert resp.status_code == 200


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


@given(parsers.parse('the OET has used {script} to create SBI {sb_json}'))
def create_sbi(script, sb_json):
    """
    Use the OET Rest API to run SBI creation script.

    Args:
        script (str): file path to an observing script
        sb_json (str): file path to a scheduling block
    """
    script_completion_state = EXECUTOR.execute_script(
        script,
        sb_json,
        timeout=10
    )
    assert script_completion_state == 'COMPLETED', \
        f"Expected SBI creation script to be COMPLETED, instead was {script_completion_state}"


@given(parsers.parse('OET has allocated resources with {script} and {sb_json}'))
def allocate_resources_from_sbi(script, sb_json):
    """
    Use the OET Rest API to run resource allocation script with SB JSON

    Args:
        script (str): file path to an observing script
        sb_json (str): file path to a scheduling block
    """
    LOGGER.info("Before starting the telescope checking if the TMC is in ON state")
    assert(tmc_is_on())
    if telescope_is_in_standby():
        set_telescope_to_running()

    script_completion_state = EXECUTOR.execute_script(
        script,
        sb_json,
        timeout=300
    )
    assert script_completion_state == 'COMPLETED', \
        f"Expected resource allocation script to be COMPLETED, instead was {script_completion_state}"


@when(parsers.parse('I tell the OET to create SBI using script {script} and SB {sb_json}'))
def when_create_sbi(script, sb_json):
    """
    Use the OET Rest API to run a script that creates SBI from given SB.

    Args:
        script (str): file path to an observing script
        sb_json (str): file path to a scheduling block
    """
    script_completion_state = EXECUTOR.execute_script(
        script,
        sb_json,
        timeout=30
    )
    assert script_completion_state == 'COMPLETED', \
        f"Expected SBI creation script to be COMPLETED, instead was {script_completion_state}"


@when(parsers.parse('I tell the OET to allocate resources using script {script} and SBI {sb_json}'))
def when_allocate_resources_from_sbi(script, sb_json):
    """
    Use the OET Rest API to run script that allocates resources from given SBI.

    Args:
        script (str): file path to an observing script
        sb_json (str): file path to a scheduling block
    """
    script_completion_state = EXECUTOR.execute_script(
        script,
        sb_json,
        timeout=300
    )
    assert script_completion_state == 'COMPLETED', \
        f"Expected resource allocation script to be COMPLETED, instead was {script_completion_state}"


@when(parsers.parse('I tell the OET to observe SBI {sb_json} using script {script}'))
def observe_sbi(sb_json, script, result):
    """
    Use the OET Rest API to observe SBI using observing script and SBI JSON

    Args:
        sb_json (str): file path to a scheduling block
        script (str): file path to an observing script
        result (dict): fixture used to track progress
    """
    subarray_url = result[SUBARRAY_USED]
    recorder = ObsStateRecorder(subarray_url)
    recorder.start_recording()
    result[STATE_CHECK] = recorder

    script_completion_state = EXECUTOR.execute_script(
        script,
        sb_json,
        timeout=300
    )
    assert script_completion_state == 'COMPLETED', \
        f"Expected SBI observation script to be COMPLETED, instead was {script_completion_state}"


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


@then('the script completes successfully')
def check_script_completed():
    """
    Check that the script that was last run has completed successfully.
    """
    script = EXECUTOR.get_latest_script()
    assert script.state == 'COMPLETED', \
        f"Expected script to be COMPLETED, instead was {script.state}"


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

