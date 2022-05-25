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
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from .oet_helpers import ScriptExecutor, observe_while_running

logger = logging.getLogger(__name__)
EXECUTOR = ScriptExecutor()


@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.startup
@pytest.mark.k8s
@scenario("features/oet_start_up_telescope.feature", "Starting up mid telescope")
def test_telescope_startup_mid():
    """Telescope startup test."""


@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.standby
@pytest.mark.k8s
@scenario("features/oet_start_up_telescope.feature", "Setting telescope to stand-by")
def test_telescope_in_standby():
    """Set telescope to standby test."""


@given("an OET")
def a_oet():
    """an OET"""


@given("a telescope in standby or off state")
def a_telescope_on_standby_or_off_state(standby_telescope: fxt_types.standby_telescope):
    "a telescope on standby or off state"


@given("a telescope in the ON state")
def a_telescope_in_the_on_state(running_telescope: fxt_types.running_telescope):
    "a telescope in the ON state"
    running_telescope.disable_automatic_setdown()


@when(parsers.parse("I tell the OET to run {script}"))
def run_startup_standby_script(
    script,
    context_monitoring: fxt_types.context_monitoring,
):
    """
    Use the OET Rest API to run a script

    Args:
        script (str): file path to an observing script
    """
    # Execute startup or standby script
    with observe_while_running(context_monitoring):
        script_completion_state = EXECUTOR.execute_script(script=script, timeout=30)
    assert (
        script_completion_state == "COMPLETE"
    ), f"Expected script to be COMPLETE, instead was {script_completion_state}"


@then(parsers.parse("the central node must be {state}"))
def check_final_state(state):
    """
    Check that the central node device is in the expected state.

    Args:
        state (str): State central node is expected to be in
    """
    tel = names.TEL()
    central_node = con_config.get_device_proxy(tel.tm.central_node)
    final_state = central_node.read_attribute("state").value
    # assert_that(str(final_state)).is_equal_to("ON")
    assert (
        str(final_state) == state
    ), f"Expected telescope to be {state} but instead was {final_state}"
    logger.info("Central node is in %s state", state)
