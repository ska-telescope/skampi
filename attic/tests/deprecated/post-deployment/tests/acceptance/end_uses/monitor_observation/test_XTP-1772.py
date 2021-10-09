#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-1772
----------------------------------
Tests for recovering sub-array from ABORTED (XTP-1773) and FAULT (XTP-1774),
stopping script execution and sending Abort command to sub-array (XTP-1775) and
stopping script execution without sending Abort command to sub-array (XTP-1776)
"""
import logging

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from ska.scripting.domain import SubArray
from ska_tmc_cdm.messages.subarray_node.configure import ConfigureRequest, DishConfiguration
from ska_tmc_cdm.messages.subarray_node.configure.core import ReceiverBand

from resources.test_support.controls import (set_telescope_to_running,
                                             set_telescope_to_standby,
                                             take_subarray,
                                             telescope_is_in_standby,
                                             tmc_is_on)
from resources.test_support.helpers import resource
from resources.test_support.oet_helpers import ScriptExecutor, REST_CLIENT

from tango import DevFailed # type: ignore
from time import sleep


LOGGER = logging.getLogger(__name__)

EXECUTOR = ScriptExecutor()

# used as labels within the result fixture
# this should be refactored at some point to something more elegant
SUBARRAY_USED = 'Sub-array'
SCRIPT_ID = 'Script ID'


@pytest.fixture(name="result")
def fixture_result():
    """structure used to hold details of the intermediate result at each stage of the test"""
    fixture = {SUBARRAY_USED: 'ska_mid/tm_subarray_node/1', SCRIPT_ID: None}
    yield fixture
    # teardown
    end(fixture)


def end(result):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    obsstate = resource(result[SUBARRAY_USED]).get('obsState')
    LOGGER.info("CLEANUP: Sub-array in obsState %s ", obsstate)
    if obsstate == "IDLE":
        LOGGER.info("CLEANUP: tearing down composed sub-array (IDLE)")
        take_subarray(1).and_release_all_resources()
    if obsstate == "ABORTED":
        LOGGER.info("CLEANUP: restarting aborted sub-array")
        sub = SubArray(1)
        sub.restart()
    if obsstate in ["RESOURCING", "RESTARTING", "RESETTING", "ABORTING"]:
        LOGGER.warning(
            "Subarray is still in %s Please restart MVP manually to complete tear down",
            obsstate)
        raise Exception("Unable to tear down test setup")
    set_telescope_to_standby()


@pytest.mark.oetmid
@pytest.mark.quarantine
@pytest.mark.skamid
@scenario("XTP-1772.feature", "Recovering sub-array from ABORTED")
def test_recovery_from_aborted():
    """Test recovering (resetting/restarting) sub-array from ABORTED state
    Given the sub-array is in ObsState ABORTED
    When I tell the OET to run <script>
    Then the sub-array goes to ObsState <obsstate>

    Examples:
        | script 				            | obsstate	|
        | file:///app/scripts/restart.py	| EMPTY		|
        | file:///app/scripts/reset.py		| IDLE		|
    """


@given('the sub-array is in ObsState ABORTED')
def set_subarray_to_aborted(result):
    """
    Set sub-array to ABORTED state by sending Abort command after resources
    are allocated.
    """
    LOGGER.info("Before starting the telescope checking if the TMC is in ON state")
    assert(tmc_is_on())
    if telescope_is_in_standby():
        set_telescope_to_running()
    take_subarray(1).to_be_composed_out_of(2)

    subarray = SubArray(1)
    subarray.abort()

    subarray_state = resource(result[SUBARRAY_USED]).get('obsState')
    assert subarray_state == 'ABORTED', \
        f"Expected sub-array to be in ABORTED but instead was in {subarray_state}"

    LOGGER.info("Sub-array has been set to ABORTED")


@pytest.mark.oetmid
@pytest.mark.skamid
@pytest.mark.skip(reason="Partial Fault scenario is not yet handled in MVP")
@scenario("XTP-1772.feature", "Recovering sub-array from FAULT")
def test_recovery_from_fault():
    """Test recovering (resetting/restarting) sub-array from FAULT state
    Given the sub-array is in ObsState FAULT
    When I tell the OET to run <script>
    Then the sub-array goes to ObsState <obsstate>

    Examples:
        | script 				            | obsstate	|
        | file:///app/scripts/restart.py	| EMPTY		|
        | file:///app/scripts/reset.py		| IDLE		|
    """


@given('the sub-array is in ObsState FAULT')
def set_subarray_to_fault(result):
    """
    Set sub-array to FAULT state by sending incomplete JSON in the Configure
    command.
    """
    LOGGER.info("Before starting the telescope checking if the TMC is in ON state")
    assert(tmc_is_on())
    if telescope_is_in_standby():
        set_telescope_to_running()
    take_subarray(1).to_be_composed_out_of(2)

    subarray = SubArray(1)

    conf_req = ConfigureRequest()
    conf_req.dish = DishConfiguration(receiver_band=ReceiverBand.BAND_1)

    # To set sub-array to FAULT, catch and ignore
    # the DevFailed of a bad Configure command
    try:
        subarray.configure_from_cdm(conf_req)
    except DevFailed:
        pass

    subarray_state = resource(result[SUBARRAY_USED]).get('obsState')
    assert subarray_state == 'FAULT', \
        f"Expected sub-array to be in FAULT but instead was in {subarray_state}"

    LOGGER.info("Sub-array has been set to FAULT")


@when('I tell the OET to run <script>')
def run_script(script):
    """

    Args:
        script (str): file path to an observing script
    """
    script_completion_state = EXECUTOR.execute_script(
        script=script,
        timeout=10
    )
    assert script_completion_state == 'COMPLETED', \
        f"Expected script to be COMPLETED, instead was {script_completion_state}"

    LOGGER.info("Script completed successfully")


@then('the sub-array goes to ObsState <obsstate>')
@then(parsers.parse('the sub-array goes to ObsState {obsstate}'))
def check_final_subarray_state(obsstate, result):
    """

    Args:
        obsstate (str): Sub-array Tango device ObsState
        result (dict): Sub-array Tango device ObsState
    """
    subarray_state = resource(result[SUBARRAY_USED]).get('obsState')
    assert subarray_state == obsstate, \
        f"Expected sub-array to be in {obsstate} but instead was in {subarray_state}"

    LOGGER.info("Sub-array is in ObsState %s", obsstate)

@pytest.mark.oetmid
@pytest.mark.skamid
@pytest.mark.quarantine
@scenario("XTP-1772.feature", "Stopping script execution and sending Abort command to sub-array")
def test_stop_script_and_abort_subarray():
    """
    Given OET is executing script file:///app/scripts/observe_sb.py with SB scripts/data/long_sb.json
    When I stop the script execution using OET
    Then the script execution is terminated
    And abort.py script is run
    And the sub-array goes to ObsState ABORTED
    """

@pytest.mark.oetmid
@pytest.mark.skamid
@pytest.mark.quarantine
@scenario("XTP-1772.feature", "Stopping script execution without aborting sub-array")
def test_stop_script():
    """
    Given OET is executing script file:///app/scripts/observe_sb.py with SB scripts/data/long_sb.json
    When I stop the script execution using OET setting abort flag to False
    Then the script execution is terminated
    And the sub-array ObsState is not ABORTED
    """


@given(parsers.parse('OET is executing script {script} with SB {sb_json}'))
def start_script_execution(script, sb_json, result):
    """
    """
    LOGGER.info("Before starting the telescope checking if the TMC is in ON state")
    assert(tmc_is_on())
    if telescope_is_in_standby():
        set_telescope_to_running()
    take_subarray(1).to_be_composed_out_of(2)

    _ = EXECUTOR.create_script(script)
    task = EXECUTOR.start_script(sb_json)

    result[SCRIPT_ID] = task.task_id

    assert task.state == 'RUNNING', \
        f"Expected script to be RUNNING, instead was {task.state}"


@when('I stop the script execution using OET')
def stop_script_execution_and_abort():
    REST_CLIENT.stop()


@then('abort.py script is run')
def check_abort_script_is_run(result):
    abort_script = EXECUTOR.get_latest_script()

    assert 'abort.py' in abort_script.script, \
        f"Expected abort script to be the latest script, instead got {abort_script.script}"

    LOGGER.info("Waiting for script %s to complete", abort_script.script)

    # Wait for abort script to complete to make sure it succeeds and
    # sub-array will be in ObsState ABORTED
    script_end_state = EXECUTOR.wait_for_script_to_complete(abort_script.task_id,
                                                            timeout=10)
    assert script_end_state == 'COMPLETED', \
        f"Expected abort script to be COMPLETED, instead was {script_end_state}"

    LOGGER.info("Abort script was completed successfully")


@when('I stop the script execution using OET setting abort flag to False')
def stop_script_execution():
    REST_CLIENT.stop(run_abort=False)


@then('the script execution is terminated')
def check_script_was_stopped(result):
    script = EXECUTOR.get_script_by_id(result[SCRIPT_ID])
    assert script.state == 'STOPPED', f'Observing script state is {script.state} instead of STOPPED'

    LOGGER.info("Script %s was stopped successfully", script.script)


@then('the sub-array ObsState is not ABORTED')
def check_subarray_is_not_aborted(result):
    assert resource(result[SUBARRAY_USED]).get('obsState') not in ['ABORTED', 'ABORTING'], \
        "Sub-array should not have been aborted"
