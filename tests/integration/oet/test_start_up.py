"""
test_XTP-780-781
----------------------------------
Telescope startup and standby using OET scripts
"""
import logging
import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names

from .oet_helpers import ScriptExecutor

logger = logging.getLogger(__name__)
EXECUTOR = ScriptExecutor()


@pytest.mark.skamid
@pytest.mark.startup
@scenario("features/oet_start_up_telescope.feature", "Starting up mid telescope")
def test_telescope_startup_mid():
    """Telescope startup test."""


@given("an OET")
def a_oet():
    """an OET"""


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


@then(parsers.parse('the central node must be {state}'))
def check_final_state(state):
    """
    Check that the central node device is in the expected state.

    Args:
        state (str): State central node is expected to be in
    """
    tel = names.TEL()
    central_node = con_config.get_device_proxy(tel.central_node)
    final_state = central_node.read_attribute("state").value
    assert_that(str(final_state)).is_equal_to("ON")
    assert final_state == state, \
        f"Expected telescope to be {state} but instead was {final_state}"
    logger.info("Central node is in %s state", state)
