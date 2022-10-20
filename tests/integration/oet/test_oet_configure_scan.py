"""
Tests to configure subarray and observe scan
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

SUBARRAY_USED = 'subarray_node'
SCHEDULING_BLOCK = 'Scheduling Block'
STATE_CHECK = 'State Transitions'

EXECUTOR = ScriptExecutor()

LOGGER = logging.getLogger(__name__)


@pytest.mark.skamid
@pytest.mark.k8s
@scenario("features/oet_configure_scan.feature", "Configure scan with a SBI on OET subarray in mid")
def test_resource_scan():
    """
    Given A running telescope with 2 dishes are allocated to sub-array for executing observations
    When I tell the OET to configure a sub-array and perform scan using script
    file:///app/scripts/observe.py --subarray_id=3 and data/mid_sb_example.json
    Then the sub-array passes through ObsStates IDLE, CONFIGURING, SCANNING, READY
    """


@given("an OET")
def a_oet():
    """an OET"""



@when(
    parsers.parse(
        "I tell the OET to configure a sub-array and perform scan using script  {script} and SBI {sb_json}"
    )
)
def when_configure_resources_from_sbi(
    script,
    sb_json,
    context_monitoring: fxt_types.context_monitoring,
    running_telescope: fxt_types.running_telescope,
    sut_settings: SutTestSettings,
    exec_settings: fxt_types.exec_settings
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
