"""
Tests to configure a scan using a predefined config
"""
import logging
import pytest
from pytest_bdd import given, parsers, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from resources.models.mvp_model.states import ObsState
from ..conftest import SutTestSettings
from ska_ser_skallop.mvp_fixtures.context_management import (
    SubarrayContext,
    TelescopeContext,
)
from .oet_helpers import ScriptExecutor

logger = logging.getLogger(__name__)
EXECUTOR = ScriptExecutor()



@scenario("features/oet_configure_scan.feature", "Configure a scan using a predefined config")
def test_configure_subarray():
    """
    Test that we can configure a scan using a predefined configuration.

        Scenario: Configure a scan using a predefined config
            Given subarray <subarray_id> that has been allocated
                <nr_of_dishes> according to <SB_config>
            When I configure the subarray to perform a <scan_config>
                scan
            Then the subarray is in the condition to run a scan
    """

@given("A running telescope for executing observations on a subarray")
def a_running_telescope(running_telescope: TelescopeContext):
    pass

@when(
    parsers.parse(
        "I tell the OET to scan SBI using script  {script} and SB {sb_json}"
    )
)
def when_configure_resources_from_sbi(
    script,
    sb_json,
    context_monitoring: fxt_types.context_monitoring,
    subarray: SubarrayContext,
    exec_settings: fxt_types.exec_settings,
):
    """
    Use the OET Rest API to run script that configure resources from given SBI.

    Args:
        script (str): file path to an observing script
        sb_json (str): file path to a scheduling block
    """
    with context_monitoring.context_monitoring():
        subarray.clear_configuration_when_finished(exec_settings)
        script_completion_state = EXECUTOR.execute_script(script, sb_json)
        assert (
            script_completion_state == "COMPLETE"
        ), f"Expected configure resource allocation script to be COMPLETED, instead was {script_completion_state}"


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
