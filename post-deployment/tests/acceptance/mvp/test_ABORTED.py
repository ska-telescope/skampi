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
from resources.test_support.oet_helpers import ScriptExecutor

from tango import DevFailed
from time import sleep


LOGGER = logging.getLogger(__name__)

EXECUTOR = ScriptExecutor()


def end():
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    obsstate = resource('ska_mid/tm_subarray_node/1').get('obsState')
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
    set_telescope_to_standby()


@pytest.mark.skamid
@scenario("test_ABORTED.feature", "Recovering sub-array from ABORTED")
def test_recovery_from_aborted():
    """"""


@pytest.mark.skamid
@scenario("test_ABORTED.feature", "Recovering sub-array from FAULT")
def test_recovery_from_fault():
    """"""


@given('the sub-array is in ObsState ABORTED')
def set_subarray_to_aborted():
    """
    Set sub-array to ABORTED state by sending Abort command after resources
    are allocated.
    """
    if telescope_is_in_standby():
        set_telescope_to_running()
    take_subarray(1).to_be_composed_out_of(2)

    subarray = SubArray(1)
    subarray.abort()
    assert resource('ska_mid/tm_subarray_node/1').get('obsState') == 'ABORTED'


@given('the sub-array is in ObsState FAULT')
def set_subarray_to_fault():
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

    assert resource('ska_mid/tm_subarray_node/1').get('obsState') == 'FAULT'

    # Need to sleep here because sub-array goes to FAULT before FAULT callbacks are
    # complete and so the Restart command gets stuck (bug).
    #sleep(4)


@when(parsers.parse('I tell the OET to run <script>'))
def run_script(script):
    """

    Args:
        script (str): file path to an observing script
    """
    LOGGER.info("PROCESS: Running script %s ", script)
    execution_result = EXECUTOR.execute_script(
        script=script,
        timeout=10
    )
    assert execution_result,  "PROCESS: Script execution failed"


@then(parsers.parse('the sub-array goes to ObsState <obsstate>'))
def check_final_subarray_state(obsstate):
    """

    Args:
        obsstate (str): Sub-array Tango device ObsState
    """
    subarray_state = resource('ska_mid/tm_subarray_node/1').get('obsState')
    assert subarray_state == obsstate
    end()

