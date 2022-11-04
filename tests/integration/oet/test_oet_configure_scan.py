"""
Tests to configure a scan using a predefined config
"""
import logging
import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from resources.models.mvp_model.states import ObsState
from ..conftest import SutTestSettings
from .oet_helpers import ScriptExecutor

logger = logging.getLogger(__name__)
EXECUTOR = ScriptExecutor()


@pytest.mark.skamid
@pytest.mark.k8s
@scenario("features/oet_configure_scan.feature", "Configure a scan using a predefined config")
def test_configure_subarray():
    """
    Test that we can configure a scan using a predefined configuration.

    Scenario: Configure a scan using a predefined config
        Given A running telescope for executing observations on a subarray
        When I tell the OET to scan SBI using script file:///scripts/observe_sb.py --subarray_id=3 and SB /tmp/oda/mid_sb_example.json
        Then the sub-array goes to ObsState READY
    """

@given("an OET")
def a_oet():
    """an OET"""


@given("sub-array is in ObsState EMPTY")
def the_subarray_must_be_in_empty_state(
    running_telescope: fxt_types.running_telescope, sut_settings: SutTestSettings
):
    """the subarray must be in EMPTY state."""
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.EMPTY)

@when(
    parsers.parse(
        "I tell the OET to config SBI using script {script} and SB {sb_json}"
    )
)
def when_configure_resources_from_sbi(
    script,
    sb_json,
    context_monitoring: fxt_types.context_monitoring,
    # configured_subarray: fxt_types.configured_subarray,
    running_telescope: fxt_types.running_telescope,
    exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """
    Use the OET Rest API to run script that configure resources from given SBI.

    Args:
        script (str): file path to an observing script
        sb_json (str): file path to a scheduling block
    """
    with context_monitoring.context_monitoring():
        running_telescope.release_subarray_when_finished(
            sut_settings.subarray_id, sut_settings.receptors, exec_settings
        )
        # configured_subarray.clear_configuration_when_finished(exec_settings)
        script_completion_state = EXECUTOR.execute_script(script, sb_json)
        assert (
            script_completion_state == "COMPLETE"
        ), f"Expected configure script to be COMPLETED, instead was {script_completion_state}"
        # logger.info("Expected configure script to be COMPLETED, instead was %s", script_completion_state)


@then(parsers.parse("the sub-array goes to ObsState {obsstate}"))
def check_final_subarray_state(
    obsstate: str,
    sut_settings: SutTestSettings,
):
    """
    Check that the final state of the sub-array is as expected.

    Args:
        obsstate (str): Sub-array Tango device ObsState
    """
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    subarray_state = ObsState(subarray.read_attribute("obsState").value).name
    assert (
        subarray_state == obsstate
    ), f"Expected sub-array to be in {obsstate} but instead was in {subarray_state}"
    logger.info("Sub-array is in ObsState %s", obsstate)
