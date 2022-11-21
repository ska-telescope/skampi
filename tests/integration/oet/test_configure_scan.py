"""
test_XTP-776
----------------------------------
Tests for observing SBI (XTP-778)
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
@scenario("features/oet_configure_scan.feature", "Observing a Scheduling Block")
def test_observing_sbi():
    """
		Given Subarray is in the ObsState IDLE
		When I tell the OET to observe using script "<script>" and SBI "<sb_json>"
		Then the Subarray goes to ObsState CONFIGURING

    Examples:
    |script                             |sb_json                     |
    |file:///scripts/observe_mid_sb.py  |/tmp/oda/mid_sb_example.json|

    """

@given("Subarray is in the ObsState IDLE")
def the_subarray_must_be_in_idle_state(
        allocated_subarray: fxt_types.allocated_subarray, sut_settings: SutTestSettings
):
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)

    central_node = con_config.get_device_proxy(tel.tm.central_node)
    assert str(central_node.read_attribute("telescopeState").value) == "ON"


@when(
    parsers.parse(
        "I tell the OET to observe using script {script} and SBI {sb_json}"
    )
)
def when_observe_sbi(
        script,
        sb_json,
        allocated_subarray: fxt_types.allocated_subarray,
        context_monitoring: fxt_types.context_monitoring,
):
    """
    Use the OET Rest API to run script that observe SBI.

    Args:
        script (str): file path to an observing script
        sb_json (str): file path to a scheduling block
    """
    allocated_subarray.disable_automatic_teardown()
    with context_monitoring.context_monitoring():
        script_completion_state = EXECUTOR.execute_script(script, sb_json)
        assert (
                script_completion_state == "COMPLETE"
        ), f"Expected observing script to be COMPLETED, instead was {script_completion_state}"

@then(parsers.parse("the Subarray goes to ObsState {obsstate}"))
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
    ), f"Expected Subarray to be in {obsstate} but instead was in {subarray_state}"
    logger.info("Subarray is in ObsState %s", obsstate)

