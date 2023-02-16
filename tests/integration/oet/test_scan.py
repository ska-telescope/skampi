"""Scan on telescope subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from resources.models.mvp_model.states import ObsState
from ska_oso_scripting.objects import SubArray
from .. import conftest


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.scan
@scenario("features/oet_scan.feature", "Run a scan on low subarray from OET")
def test_oet_scan_on_low_subarray():
    """Run a scan on OET low telescope subarray."""


@given("an OET")
def a_oet():
    """an OET"""


@given("a subarray in READY state", target_fixture="scan")
def a_low_subarray_in_ready_state(
    base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: conftest.SutTestSettings,
) -> conf_types.ScanConfiguration:
    """a subarray in READY state"""
    subarray_allocation_spec.receptors = sut_settings.receptors
    subarray_allocation_spec.subarray_id = sut_settings.subarray_id
    return base_configuration


@when("I command it to scan for a given period")
def i_command_it_to_scan_low(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: conftest.SutTestSettings,
):
    """I configure it for a scan."""
    subarray_id = sut_settings.subarray_id
    tel = names.TEL()
    context_monitoring.set_waiting_on(tel.tm.subarray(subarray_id)).for_attribute(
        "obsstate"
    ).to_change_in_order(["SCANNING", "READY"])
    with context_monitoring.observe_while_running(integration_test_exec_settings):
        subarray = SubArray(subarray_id)
        subarray.scan(scan_duration=30)

@then("the subarray must be in the SCANNING state until finished")
def the_subarray_must_be_in_the_scanning_state(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """the subarray must be in the SCANNING state until finished."""
    recorder = integration_test_exec_settings.recorder
    tel = names.TEL()
    tmc_subarray_name = str(tel.tm.subarray(configured_subarray.id))
    tmc_subarray = con_config.get_device_proxy(tmc_subarray_name)
    """occurrences = recorder._occurrences  # type: ignore
    tmc_state_changes = [
        occurrence.attr_value
        for occurrence in occurrences
        if (
            (occurrence.attr_name == tmc_subarray_name)
            & (occurrence.attr_name == "obsstate")
        )
    ]
    assert_that(tmc_state_changes).is_equal_to(["SCANNING", "READY"])"""

    result = tmc_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)
