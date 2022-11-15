"""Run scan on telescope subarray feature tests."""

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from resources.models.mvp_model.states import ObsState
from ..conftest import SutTestSettings

@pytest.mark.skip
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.scan
@scenario("features/tmc_scan.feature", "Run a scan from TMC")
def test_tmc_scan_on_mid_subarray():
    """Run a scan on TMC mid telescope subarray."""


@given("a TMC")
def a_tmc():
    """an TMC"""


@given("a subarray in READY state", target_fixture="scan")
def a_subarray_in_ready_state(
    set_up_subarray_log_checking_for_tmc, 
    base_configuration: conf_types.ScanConfiguration,  
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: SutTestSettings,
) -> conf_types.ScanConfiguration:
    """a subarray in READY state."""
    return base_configuration
    

# @when("I command it to scan for a given period")


@then("the telescope subarray shall go from READY to SCANNING state")
def the_telescope_subarray_shall_go_from_ready_to_scanning_state(
    sut_settings: SutTestSettings, integration_test_exec_settings: fxt_types.exec_settings,
):
    """the telescope subarray shall go from READY to SCANNING state"""
    tel = names.TEL()
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(
        str(tel.tm.subarray(sut_settings.subarray_id)))
    tmc_subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = tmc_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.SCANNING)


@then("the telescope subarray shall go back to READY when finished scanning")
def the_telescope_subarray_shall_go_back_to_ready_when_finished_scanning(
    sut_settings: SutTestSettings, integration_test_exec_settings: fxt_types.exec_settings,
):
    """the telescope subarray shall go back to READY when finished scanning"""
    tel = names.TEL()
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(
        str(tel.tm.subarray(sut_settings.subarray_id)))
    tmc_subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = tmc_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)