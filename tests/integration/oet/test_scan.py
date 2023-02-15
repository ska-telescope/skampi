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
from ..conftest import SutTestSettings

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
) -> conf_types.ScanConfiguration:
    """a subarray in READY state"""
    return base_configuration

@when("I command it to scan for a given period")
def i_command_it_to_scan_low(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    allocated_subarray: fxt_types.allocated_subarray,
):
    """I configure it for a scan."""
    subarray_id = allocated_subarray.id
    with context_monitoring.context_monitoring():
        with configured_subarray.scan(
                integration_test_exec_settings
        ):
            subarray = SubArray(subarray_id)
            subarray.scan()

@then("the subarray must be in the SCANNING state until finished")
def the_sdp_subarray_must_be_in_the_scanning_state(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """the SDP subarray must be in the SCANNING state until finished."""
    tel = names.TEL()
    tmc_subarray_name = tel.tm.subarray(configured_subarray.id)
    tmc_subarray = con_config.get_device_proxy(tmc_subarray_name)

    result = tmc_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.SCANNING)
    # afterwards it must be ready
    context_monitoring.re_init_builder()
    context_monitoring.wait_for(tmc_subarray_name).for_attribute(
        "obsstate"
    ).to_become_equal_to(
        "READY", ignore_first=False, settings=integration_test_exec_settings
    )
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(tmc_subarray_name)
    result = tmc_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)