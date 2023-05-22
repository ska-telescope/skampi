import logging
from pathlib import Path

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from resources.models.mvp_model.env import Observation
from resources.models.mvp_model.states import ObsState
from resources.models.obsconfig.target_spec import ReceiverBand, Target, TargetSpec
from ska_oso_scripting.objects import SubArray
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from ..conftest import SutTestSettings
from .oet_helpers import ScriptExecutor

"""
test_XTP-18866, test_XTP-776
----------------------------------
Tests for Configure the low telescope subarray using OET (XTP-19864)
Tests for Configure the mid telescope subarray using OET (XTP-778)
"""

"""Configure scan on telescope subarray feature tests."""

logger = logging.getLogger(__name__)
EXECUTOR = ScriptExecutor()


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.k8s
@scenario("features/oet_configure_scan.feature", "Observing a Scheduling Block")
def test_observing_sbi():
    """
    Given an OET
    Given sub-array is in the ObsState IDLE
    When I tell the OET to observe using script
     file:///scripts/observe_mid_sb.py
     and SBI /tmp/oda/mid_sb_example.json
    Then the sub-array goes to ObsState IDLE
    """


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.configure
@scenario(
    "features/oet_configure_scan.feature",
    "Configure the low telescope subarray using OET",
)
def test_oet_configure_scan_on_low_subarray():
    """Configure scan on OET low telescope subarray."""


@given("an OET")
def an_oet(observation_config: Observation):
    """
    Set up the observation before starting the test
    :param observation_config: An object for observation config
    """
    # This step has to executed before allocated_subarray
    # fixture is used so that
    # additional scan types are recognised.
    observation_config.add_scan_type_configuration("science_A", ("vis0", "default_beam_type"))
    observation_config.add_scan_type_configuration("calibration_B", ("vis0", "default_beam_type"))
    observation_config.target_specs = {}
    updated_target_specs = {
        "science_A": TargetSpec(
            Target("12:29:06.699 degrees", "02:03:08.598 degrees"),
            "science_A",
            ReceiverBand.BAND_2,
            "vis_channels",
            "all",
            "field_a",
            "test-receive-addresses",
            "two",
        ),
        "calibration_B": TargetSpec(
            Target("12:29:06.699 degrees", "02:03:08.598 degrees"),
            "calibration_B",
            ReceiverBand.BAND_2,
            "vis_channels",
            "all",
            "field_a",
            "test-receive-addresses",
            "two",
        ),
    }
    observation_config.add_target_specs(updated_target_specs)


@given("a valid scan configuration", target_fixture="valid_config_from_file")
def a_valid_scan_configuration():
    """
    A valid scan configuration

    :return: path to json file
    """
    return Path("./tests/resources/test_data/OET_integration/configure_low.json")


@given("sub-array is in the ObsState IDLE")
def the_subarray_must_be_in_idle_state(
    allocated_subarray: fxt_types.allocated_subarray,
    sut_settings: SutTestSettings,
):
    """
    the subarray must be in IDLE state.
    :param allocated_subarray: The allocated subarray to be configured.
    :param sut_settings: A class representing the settings for the system under test.

    """
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)

    central_node = con_config.get_device_proxy(tel.tm.central_node)
    assert str(central_node.read_attribute("telescopeState").value) == "ON"


@when("I configure it for a scan")
def i_configure_it_for_a_scan(
    valid_config_from_file: Path,
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """
    I configure it for a scan.

    :param valid_config_from_file: object for valid config from file with given path
    :param allocated_subarray: The allocated subarray to be configured.
    :param context_monitoring: Context monitoring object.
    :param integration_test_exec_settings: The integration test execution settings.
    :param sut_settings: A class representing the settings for the system under test.

    """
    subarray_id = sut_settings.subarray_id
    subarray = SubArray(subarray_id)
    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_configuring_a_subarray(integration_test_exec_settings):
            subarray.configure_from_file(str(valid_config_from_file), False)


@when(
    parsers.parse("I tell the OET to observe using script {script} and SBI {sb_json}"),
    target_fixture="script_completion_state",
)
def when_observe_sbi(
    script,
    sb_json,
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
):
    """
    Use the OET Rest API to run script that observe SBI.

    :param script: file path to an observing script
    :type script: str
    :param sb_json: file path to a scheduling block
    :type sb_json: str
    :param allocated_subarray: The allocated subarray to be configured.
    :param context_monitoring: Context monitoring object.
    :return: script completion state
    """
    script_completion_state = "UNKNOWN"
    with context_monitoring.context_monitoring():
        # Set the timeout here to lower than skallop timeout (300)
        # so that if the script is stuck, it will be stopped before
        # context monitoring throws a timeout error
        script_completion_state = EXECUTOR.execute_script(script, sb_json, timeout=280)
    logger.info(f"observing script execution status set to {script_completion_state}")
    return script_completion_state


@then("the subarray must be in the READY state")
def the_subarray_must_be_in_the_ready_state(
    sut_settings: SutTestSettings,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    the subarray must be in the READY state.
    :param sut_settings: A class representing the settings for the system under test.
    :param integration_test_exec_settings: A dictionary containing the execution
        settings for the integration tests.
    """
    tel = names.TEL()
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(  # noqa: E501
        str(tel.tm.subarray(sut_settings.subarray_id)), time_source="local"
    )
    oet_subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = oet_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)


@then("the OET will execute the script correctly")
def the_oet_will_execute_the_script_correctly(script_completion_state: str):
    """
    The oet will execute the script correctly
    :param script_completion_state: An object foe script completion state
    :type script_completion_state: str
    """
    assert script_completion_state == "COMPLETE", (
        "Expected observing script to be COMPLETED, instead was" f" {script_completion_state}"
    )


@then(parsers.parse("the sub-array goes to ObsState {obsstate}"))
def check_final_subarray_state(
    obsstate: str,
    sut_settings: SutTestSettings,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    Check that the final state of the sub-array is as expected.

    :param obsstate: Sub-array Tango device ObsState
    :type obsstate: str
    :param sut_settings: A class representing the settings for the system under test.
    :param integration_test_exec_settings: A dictionary containing the execution
        settings for the integration tests.

    """
    tel = names.TEL()
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(  # noqa: E501
        str(tel.tm.subarray(sut_settings.subarray_id)), time_source="local"
    )
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    subarray_state = ObsState(subarray.read_attribute("obsState").value).name
    logger.info("Sub-array is in ObsState %s", subarray_state)
    assert subarray_state == obsstate, (
        f"Expected sub-array to be in {obsstate} but instead was in" f" {subarray_state}"
    )
