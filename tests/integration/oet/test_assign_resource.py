"""
test_XTP-776
----------------------------------
Tests for creating SBI (XTP-779), allocating resources from SBI (XTP-777)
"""

import logging
import os
import requests

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from resources.models.mvp_model.states import ObsState
from ..conftest import SutTestSettings

from .oet_helpers import ScriptExecutor

logger = logging.getLogger(__name__)
EXECUTOR = ScriptExecutor()

@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.k8s
@scenario("features/oet_assign_resources.feature", "Creating a new SBI with updated SB IDs and PB IDs")
def test_sbi_creation():
    """
    Given the SKUID service is running
    When I tell the OET to run file:///scripts/create_sbi.py using data/mid_sb_example.json
    Then the script completes successfully
    """


@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.k8s
@scenario("features/oet_assign_resources.feature", "Allocating resources with a SBI")
def test_resource_allocation():
    """
    Given an OET
    And  sub-array is in ObsState EMPTY
    When I tell the OET to allocate resources using script file:///scripts/allocate_from_file_sb.py and SBI data/mid_sb_example.json
    Then the sub-array goes to ObsState IDLE
    """


@given("an OET")
def a_oet():
    """an OET"""


@given("an telescope subarray", target_fixture="composition")
def an_sdp_subarray(
    set_up_subarray_log_checking_for_tmc, base_composition: conf_types.Composition
) -> conf_types.Composition:
    """an telescope subarray."""
    return base_composition


@given("sub-array is in ObsState EMPTY")
def the_subarray_must_be_in_empty_state(sut_settings: SutTestSettings):
    """the subarray must be in EMPTY state."""
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.EMPTY)



@when(parsers.parse("I tell the OET to create SBI using script {script} and SB {sb_json}"))
def when_create_sbi(
    script,
    sb_json,
    context_monitoring: fxt_types.context_monitoring,
):
    """
    Use the OET Rest API to run a script that creates SBI from given SB.

    Args:
        script (str): file path to an observing script
        sb_json (str): file path to a scheduling block
    """
    # Execute startup or standby script
    with context_monitoring.context_monitoring():
        script_completion_state = EXECUTOR.execute_script(script, sb_json, timeout=30)
        assert (
            script_completion_state == "COMPLETE"
        ), f"Expected SBI creation script to be COMPLETED, instead was {script_completion_state}"


@when(parsers.parse('I tell the OET to allocate resources using script {script} and SBI {sb_json}'))
def when_allocate_resources_from_sbi(
        script,
        sb_json,
        context_monitoring: fxt_types.context_monitoring,
):
    """
    Use the OET Rest API to run script that allocates resources from given SBI.

    Args:
        script (str): file path to an observing script
        sb_json (str): file path to a scheduling block
    """
    with context_monitoring.context_monitoring():
        script_completion_state = EXECUTOR.execute_script(
            script,
            sb_json,
            timeout=30
        )
        assert script_completion_state == 'COMPLETE', \
            f"Expected resource allocation script to be COMPLETED, instead was {script_completion_state}"



@then('the script completes successfully')
def check_script_completed():
    """
    Check that the script that was last run has completed successfully.
    """
    script = EXECUTOR.get_latest_script()
    assert script.state == 'COMPLETE', \
        f"Expected script to be COMPLETED, instead was {script.state}"


@then(parsers.parse('the sub-array goes to ObsState {obsstate}'))
def check_final_subarray_state(obsstate,sut_settings: SutTestSettings):
    """
    Check that the final state of the sub-array is as expected.

    Args:
        obsstate (str): Sub-array Tango device ObsState
    """
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    subarray_state = subarray.read_attribute("obsState").value
    assert subarray_state == obsstate, \
        f"Expected sub-array to be in {obsstate} but instead was in {subarray_state}"
    logger.info("Sub-array is in ObsState %s", obsstate)

