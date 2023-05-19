"""
test_XTP-780-781
----------------------------------
Telescope startup and standby using OET scripts
"""
import logging
import time

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from ska_oso_scripting.objects import Telescope
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from .oet_helpers import ScriptExecutor

logger = logging.getLogger(__name__)
EXECUTOR = ScriptExecutor()


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.startup
@pytest.mark.k8s
@scenario("features/oet_startup_standby_telescope.feature", "Starting up telescope")
def test_telescope_startup():
    """Telescope startup test."""


@pytest.mark.oet
@pytest.mark.skalow
@pytest.mark.startup
@pytest.mark.k8s
@scenario(
    "features/oet_startup_standby_telescope.feature",
    "Starting up low telescope",
)
def test_telescope_startup_low():
    """Telescope startup test."""


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.standby
@pytest.mark.k8s
@scenario(
    "features/oet_startup_standby_telescope.feature",
    "Setting telescope to stand-by",
)
def test_telescope_standby():
    """Set telescope to standby test."""


@given("telescope is in STANDBY or OFF state")
def a_telescope_on_standby_or_off_state(
    standby_telescope: fxt_types.standby_telescope,
):
    """
    a telescope on standby or off state
    :param standby_telescope: The standby telescope instance to be started.

    """
    tel = names.TEL()
    central_node = con_config.get_device_proxy(tel.tm.central_node, fast_load=True)
    assert str(central_node.read_attribute("telescopeState").value) in [
        "STANDBY",
        "OFF",
    ]


@given("low telescope")
def a_low_telescope_():
    """a telescope"""


@given("telescope is in ON state")
def a_telescope_in_the_on_state(
    running_telescope: fxt_types.running_telescope,
):
    """
    a telescope in the ON state
    :param running_telescope: The running telescope instance.
    """
    tel = names.TEL()
    central_node = con_config.get_device_proxy(tel.tm.central_node)
    assert str(central_node.read_attribute("telescopeState").value) == "ON"


@pytest.fixture(name="observe_csp_during_on_of")
def fxt_observe_csp_during_on_of(
    context_monitoring: fxt_types.context_monitoring,
):
    """
    A fixture to observe csp during on off
    :param context_monitoring: The context monitoring configuration.
    """
    tel = names.TEL()
    if tel.skalow:
        context_monitoring.set_waiting_on(tel.csp.controller).for_attribute(
            "obsState"
        ).and_observe()


@when(parsers.parse("I tell the OET to run startup script {script}"))
def run_startup_script(
    script,
    standby_telescope: fxt_types.standby_telescope,
    integration_test_exec_settings: fxt_types.exec_settings,
    observe_csp_during_on_of,
    context_monitoring: fxt_types.context_monitoring,
):
    """
    Use the OET Rest API to run a script

    :param script: file path to an observing script
    :type script: str
    :param standby_telescope: The standby telescope instance to be started.
    :param integration_test_exec_settings: The integration test execution settings.
    :param context_monitoring: The context monitoring configuration.
    :param observe_csp_during_on_of: A fixture to observe csp during on off

    """

    with context_monitoring.observe_while_running(integration_test_exec_settings):
        standby_telescope.switch_off_after_test(integration_test_exec_settings)
        script_completion_state = EXECUTOR.execute_script(script=script, timeout=30)
        assert script_completion_state == "COMPLETE", (
            "Expected script to be COMPLETE, instead was" f" {script_completion_state}"
        )
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

    :param script: file path to an observing script
    :param running_telescope: The running telescope instance.
    :param integration_test_exec_settings: The integration test execution settings.
    :param context_monitoring: The context monitoring configuration.
    """

    with context_monitoring.observe_while_running(integration_test_exec_settings):
        running_telescope.disable_automatic_setdown()
        with running_telescope.wait_for_shutting_down():
            script_completion_state = EXECUTOR.execute_script(script=script, timeout=30)
        assert script_completion_state == "COMPLETE", (
            "Expected script to be COMPLETE, instead was" f" {script_completion_state}"
        )


@when(parsers.parse("I turn telescope to ON state"))
def startup_telescope_low(
    standby_telescope: fxt_types.standby_telescope,
    integration_test_exec_settings: fxt_types.exec_settings,
    context_monitoring: fxt_types.context_monitoring,
):
    """
    Use the OET OSO Scripting to Turn On Telescope

    :param standby_telescope: The standby telescope instance to be started.
    :param integration_test_exec_settings: The integration test execution settings.
    :param context_monitoring: The context monitoring configuration.
    """
    standby_telescope.disable_automatic_setdown()
    with context_monitoring.context_monitoring():
        with standby_telescope.wait_for_starting_up(integration_test_exec_settings):
            logger.info("OET Commands are being used")
            telescope = Telescope()
            telescope.on()


@given("the Telescope is in ON state")
def the_telescope_is_on(
    standby_telescope: fxt_types.standby_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    I start up the telescope.

    :param standby_telescope: The standby telescope instance to be started.
    :param entry_point: The entry point to the system under test.
    :param context_monitoring: The context monitoring configuration.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    standby_telescope.disable_automatic_setdown()
    with context_monitoring.context_monitoring():
        with standby_telescope.wait_for_starting_up(integration_test_exec_settings):
            logger.info("The entry point being used is : %s", entry_point)
            entry_point.set_telescope_to_running()


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
    assert str(final_state) == "ON", f"Expected telescope to be ON but instead was {final_state}"
    logger.info("Central node is in ON state")
