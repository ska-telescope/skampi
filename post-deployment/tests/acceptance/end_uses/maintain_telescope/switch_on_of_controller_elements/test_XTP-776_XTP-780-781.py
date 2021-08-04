#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_XTP-780-781
----------------------------------
Telescope startup and standby using OET scripts
"""
import logging

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from resources.test_support.controls import (set_telescope_to_running,
                                             set_telescope_to_standby,
                                             telescope_is_in_standby,
                                             tmc_is_on)
from resources.test_support.helpers import resource
from resources.test_support.oet_helpers import ScriptExecutor

# used as labels within the oet_result fixture
# this should be refactored at some point to something more elegant
CENTRAL_NODE_USED = 'central_node'

EXECUTOR = ScriptExecutor()

LOGGER = logging.getLogger(__name__)


@pytest.fixture(name="result")
def fixture_result():
    """structure used to hold details of the intermediate result at each stage of the test"""
    fixture = {CENTRAL_NODE_USED: 'ska_mid/tm_central/central_node'}
    yield fixture
    # teardown
    end()


def end():
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    if not telescope_is_in_standby():
        set_telescope_to_standby()

@pytest.mark.skip()
@pytest.mark.fast
@pytest.mark.oetmid
@pytest.mark.skamid
@pytest.mark.quarantine
@scenario("XTP-776.feature", "Starting up telescope")
def test_telescope_startup():
    """Telescope startup test."""

@pytest.mark.skip()
@pytest.mark.fast
@pytest.mark.oetmid
@pytest.mark.skamid
@pytest.mark.quarantine
@scenario("XTP-776.feature", "Setting telescope to stand-by")
def test_telescope_in_standby():
    """Set telescope to standby test."""


@given('telescope is in OFF State')
def set_telescope_in_off_state(result):
    """
    Set telescope to OFF state (stand-by) if it is not yet OFF.
    """
    LOGGER.info("Set telescope to stand-by")
    if not telescope_is_in_standby():
        set_telescope_to_standby()
    telescope_state = resource(result[CENTRAL_NODE_USED]).get('telescopeState')
    assert telescope_state == 'STANDBY', \
        f"Expected telescope to be OFF but instead was {telescope_state}"
    LOGGER.info("Telescope is in OFF state")


@given('telescope is in ON State')
def set_telescope_in_on_state(result):
    """
    Set telescope to ON state (startup) if it's not yet ON.
    """
    LOGGER.info("Before starting the telescope checking if the TMC is in ON state")
    assert(tmc_is_on())
    LOGGER.info("Starting up telescope")
    if telescope_is_in_standby():
        set_telescope_to_running()
    telescope_state = resource(result[CENTRAL_NODE_USED]).get('telescopeState')
    assert telescope_state == 'ON', \
        f"Expected telescope to be ON but instead was {telescope_state}"
    LOGGER.info("Telescope is in ON state")


@when(parsers.parse('I tell the OET to run {script}'))
def run_startup_standby_script(script):
    """
    Use the OET Rest API to run a script

    Args:
        script (str): file path to an observing script
    """
    # Execute startup or standby script
    script_completion_state = EXECUTOR.execute_script(
        script=script,
        timeout=30
    )
    assert script_completion_state == 'COMPLETED', \
        f"Expected script to be COMPLETED, instead was {script_completion_state}"


@then(parsers.parse('the central node goes to state {state}'))
def check_final_state(state, result):
    """
    Check that the central node device is in the expected state.

    Args:
        state (str): State central node is expected to be in
        result (dict): fixture used to track test progress
    """
    final_state = resource(result[CENTRAL_NODE_USED]).get('telescopeState')
    assert final_state == state, \
        f"Expected telescope to be {state} but instead was {final_state}"
    LOGGER.info("Central node is in %s state", state)

