#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_ABORTED
----------------------------------

"""
import logging

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from ska.scripting.domain import SubArray
from ska.cdm.messages.subarray_node.configure import ConfigureRequest, DishConfiguration
from ska.cdm.messages.subarray_node.configure.core import ReceiverBand

from resources.test_support.controls import (restart_subarray,
                                             set_telescope_to_running,
                                             set_telescope_to_standby,
                                             take_subarray,
                                             telescope_is_in_standby)
from resources.test_support.helpers import resource
from resources.test_support.oet_helpers import ScriptExecutor, REST_CLIENT

from tango import DevFailed
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
    if obsstate == "IDLE":
        LOGGER.info("CLEANUP: tearing down composed subarray (IDLE)")
        take_subarray(1).and_release_all_resources()
    if obsstate == "ABORTED":
        sub = SubArray(1)
        sub.restart()
    if obsstate in ["RESTARTING", "RESETTING", "ABORTING"]:
        LOGGER.warning(
            "Subarray is still in %s Please restart MVP manually to complete tear down",
            obsstate)
        raise Exception("Unable to tear down test setup")
    set_telescope_to_standby()


@pytest.mark.script_execution
@pytest.mark.skamid
@scenario("XTP-1772.feature", "Recovering sub-array from ABORTED")
def test_recovery_from_aborted():
    """"""


@given('the sub-array is in ObsState ABORTED')
def set_subarray_to_aborted(result):
    """
    Set sub-array to ABORTED state by sending Abort command after resources
    are allocated.
    """
    if telescope_is_in_standby():
        set_telescope_to_running()
    take_subarray(1).to_be_composed_out_of(2)

    subarray = SubArray(1)
    subarray.abort()
    assert resource(result[SUBARRAY_USED]).get('obsState') == 'ABORTED'


@pytest.mark.skamid
@pytest.mark.skip(reason="Disabled due to error when resetting/restarting from FAULT")
@scenario("XTP-1772.feature", "Recovering sub-array from FAULT")
def test_recovery_from_fault():
    """"""


@given('the sub-array is in ObsState FAULT')
def set_subarray_to_fault(result):
    """
    Set sub-array to FAULT state by sending incomplete JSON in the Configure
    command.
    """
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

    assert resource(result[SUBARRAY_USED]).get('obsState') == 'FAULT'

    # Need to sleep here because sub-array goes to FAULT before FAULT callbacks are
    # complete and so the Restart command gets stuck (bug).
    #sleep(4)


@when('I tell the OET to run <script>')
def run_script(script):
    """

    Args:
        script (str): file path to an observing script
    """
    LOGGER.info("PROCESS: Running script %s ", script)
    script_completion_state = EXECUTOR.execute_script(
        script=script,
        timeout=10
    )
    assert script_completion_state == 'COMPLETED',  "PROCESS: Script execution failed"


@then('the sub-array goes to ObsState <obsstate>')
@then(parsers.parse('the sub-array goes to ObsState {obsstate}'))
def check_final_subarray_state(obsstate, result):
    """

    Args:
        obsstate (str): Sub-array Tango device ObsState
        result (dict): Sub-array Tango device ObsState
    """
    subarray_state = resource(result[SUBARRAY_USED]).get('obsState')
    assert subarray_state == obsstate


@pytest.mark.oet
@pytest.mark.skamid
@scenario("XTP-1772.feature", "Stopping script execution and sending Abort command to sub-array")
def test_stop_script_and_abort_subarray():
    """"""


@pytest.mark.oet
@pytest.mark.skamid
@scenario("XTP-1772.feature", "Stopping script execution without aborting sub-array")
def test_stop_script():
    """"""


@given(parsers.parse('OET is executing script {script} with SB {sb_json}'))
def start_script_execution(script, sb_json, result):
    """
    """
    if telescope_is_in_standby():
        set_telescope_to_running()
    take_subarray(1).to_be_composed_out_of(2)

    _ = EXECUTOR.create_script(script)
    task = EXECUTOR.start_script(sb_json)

    result[SCRIPT_ID] = task.task_id

    assert task.state == 'RUNNING'


@when('I stop the script execution using OET')
def stop_script_execution_and_abort():
    REST_CLIENT.stop()


@then('abort.py script is run')
def check_abort_script_is_run(result):
    abort_script = EXECUTOR.get_latest_script()
    LOGGER.info('Abort script: %s', abort_script.script)
    script_end_state = EXECUTOR.wait_for_script_to_complete(abort_script.task_id,
                                                            timeout=10)
    assert script_end_state == 'COMPLETED'


@when('I stop the script execution using OET setting abort flag to False')
def stop_script_execution():
    REST_CLIENT.stop(run_abort=False)


@then('the script execution is terminated')
def check_script_was_stopped(result):
    script = EXECUTOR.get_script_by_id(result[SCRIPT_ID])
    assert script.state == 'STOPPED', ('Observing script state is %s instead of STOPPED', script.state)


@then('the sub-array ObsState is not ABORTED')
def check_subarray_is_not_aborted(result):
    assert resource(result[SUBARRAY_USED]).get('obsState') not in ['ABORTED', 'ABORTING']

