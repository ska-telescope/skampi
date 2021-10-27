#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-2418
----------------------------------
Test for releasing resources
"""
import logging

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from resources.test_support.controls_low import (set_telescope_to_running,
                                                 set_telescope_to_standby,
                                                 to_be_composed_out_of,
                                                 telescope_is_in_standby)
from resources.test_support.helpers_low import resource
from resources.test_support.oet_helpers import ScriptExecutor
from ska.scripting.domain import SubArray

LOGGER = logging.getLogger(__name__)

EXECUTOR = ScriptExecutor()

# used as labels within the result fixture
# this should be refactored at some point to something more elegant
SUBARRAY_USED = 'Sub-array'


@pytest.fixture(name="result")
def fixture_result():
    """structure used to hold details of the intermediate result at each stage of the test"""
    fixture = {SUBARRAY_USED: 'ska_low/tm_subarray_node/1'}
    yield fixture
    # teardown
    end(fixture)


def end(result):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    subarray = SubArray(1)
    obsstate = resource(result[SUBARRAY_USED]).get('obsState')
    if obsstate == "IDLE":
        LOGGER.info("CLEANUP: tearing down composed subarray (IDLE)")
        subarray.deallocate()
    set_telescope_to_standby()


@pytest.mark.oetlow
@pytest.mark.skalow
@pytest.mark.quarantine
@scenario("XTP-2413.feature", "Release resources")
def test_release_resources():
    """Deallocate Resources."""
    pass


@given('the sub-array is in ObsState IDLE')
def set_subarray_to_idle(result):
    """
    Set sub-array to idle state after resources are allocated.
    """
    if telescope_is_in_standby():
        LOGGER.info("Starting up telescope")
        set_telescope_to_running()
    LOGGER.info("Assigning resources")
    to_be_composed_out_of()
    subarray_state = resource(result[SUBARRAY_USED]).get('obsState')
    assert subarray_state == 'IDLE', \
        f"Expected sub-array to be in IDLE but instead was in {subarray_state}"
    LOGGER.info("Sub-array is in ObsState IDLE")


@when(parsers.parse('I tell the OET to release resources by running {script}'))
def run_deallocation_script(script):
    """
    Use the OET Rest API to run a deallocation script

    Args:
        script (str): file path to an deallocate script
    """
    script_completion_state = EXECUTOR.execute_script(
        script=script,
        timeout=30
    )
    assert script_completion_state == 'COMPLETED', \
        f"Expected deallocation script to be COMPLETED, instead was {script_completion_state}"

    LOGGER.info("Deallocation script completed successfully")


@then(parsers.parse('the sub-array goes to ObsState {obsstate}'))
def check_final_subarray_state(obsstate, result):
    """
    Check that sub-array device is in the expected state.

    Args:
        obsstate (str): Sub-array Tango device ObsState
        result (dict): fixture used to track test progress
    """
    subarray_state = resource(result[SUBARRAY_USED]).get('obsState')
    assert subarray_state == obsstate, \
        f"Expected sub-array to be in {obsstate} but instead was in {subarray_state}"
    LOGGER.info("Sub-array is in ObsState %s", obsstate)
