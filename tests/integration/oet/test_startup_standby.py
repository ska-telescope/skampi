"""
test_XTP-780-781
----------------------------------
Telescope startup and standby using OET scripts
"""
import logging
import time

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from .oet_helpers import ScriptExecutor

logger = logging.getLogger(__name__)
EXECUTOR = ScriptExecutor()


@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.startup
@pytest.mark.k8s
@scenario("features/oet_startup_standby_telescope.feature", "Starting up telescope")
def test_telescope_startup():
    """Telescope startup test."""


@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.standby
@pytest.mark.k8s
@scenario(
    "features/oet_startup_standby_telescope.feature", "Setting telescope to stand-by"
)
def test_telescope_standby():
    """ Set telescope to standby test."""


@given("telescope is in STANDBY or OFF state")
def a_telescope_on_standby_or_off_state(
    standby_telescope: fxt_types.standby_telescope,
):
    """a telescope on standby or off state"""
    tel = names.TEL()
    central_node = con_config.get_device_proxy(tel.tm.central_node, fast_load=True)
    assert str(central_node.read_attribute("telescopeState").value) in [
        "STANDBY",
        "OFF",
    ]


@given("telescope is in ON state")
def a_telescope_in_the_on_state(running_telescope: fxt_types.running_telescope):
    """a telescope in the ON state"""
    tel = names.TEL()
    central_node = con_config.get_device_proxy(tel.tm.central_node)
    assert str(central_node.read_attribute("telescopeState").value) == "ON"


@when(parsers.parse("I tell the OET to run startup script {script}"))
def run_startup_script(
    script,
    standby_telescope: fxt_types.standby_telescope,
    integration_test_exec_settings: fxt_types.exec_settings,
    context_monitoring: fxt_types.context_monitoring,
):
    """
    Use the OET Rest API to run a script

    Args:
        script (str): file path to an observing script
    """

    with context_monitoring.observe_while_running(integration_test_exec_settings):
        standby_telescope.switch_off_after_test(integration_test_exec_settings)
        script_completion_state = EXECUTOR.execute_script(script=script, timeout=30)
        assert (
            script_completion_state == "COMPLETE"
        ), f"Expected script to be COMPLETE, instead was {script_completion_state}"
        # after success we marked the telescope state to be ON
        standby_telescope.state = "ON"


@when(parsers.parse("I tell the OET to run standby script {script}"))
def run_standby_script(
    script,
    running_telescope: fxt_types.running_telescope,
    integration_test_exec_settings: fxt_types.exec_settings,
    context_monitoring: fxt_types.context_monitoring,
):
    """
    Use the OET Rest API to run a script

    Args:
        script (str): file path to an observing script
    """

    with context_monitoring.observe_while_running(integration_test_exec_settings):
        running_telescope.disable_automatic_setdown()
        with running_telescope.wait_for_shutting_down():
            script_completion_state = EXECUTOR.execute_script(script=script, timeout=30)
        assert (
            script_completion_state == "COMPLETE"
        ), f"Expected script to be COMPLETE, instead was {script_completion_state}"


@then(parsers.parse("the central node goes to state STANDBY"))
def check_final_state_is_off():
    """
    Check that the central node device is in the expected state.
    """
    tel = names.TEL()
    central_node = con_config.get_device_proxy(tel.tm.central_node)
    final_state = central_node.read_attribute("telescopeState").value
    assert (
        str(final_state) == "STANDBY"
    ), f"Expected telescope to be STANDBY but instead was {final_state}"
    logger.info("Central node is in STANDBY state")
    time.sleep(10)


@then(parsers.parse("the central node goes to state ON"))
def check_final_state_is_on():
    """
    Check that the central node device is in the expected state.
    """
    tel = names.TEL()
    central_node = con_config.get_device_proxy(tel.tm.central_node)
    final_state = central_node.read_attribute("telescopeState").value
    assert (
        str(final_state) == "ON"
    ), f"Expected telescope to be ON but instead was {final_state}"
    logger.info("Central node is in ON state")