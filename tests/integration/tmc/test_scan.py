"""Run scan on telescope subarray feature tests."""

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from ..conftest import SutTestSettings

@pytest.mark.tmc
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.scan
@scenario("features/tmc_scan.feature", "Run a scan from TMC")
def test_tmc_scan_on_mid_subarray():
    """Run a scan on TMC mid telescope subarray."""


@pytest.mark.tmc
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.scan
@scenario("features/tmc_scan.feature", "Run a scan on low subarray from TMC")
def test_tmc_scan_on_low_subarray():
    """Run a scan on TMC low telescope subarray."""


@given("an TMC")
def a_tmc():
    """an TMC"""


@given("a subarray in READY state", target_fixture="scan")
def a_subarray_in_ready_state(
    set_up_subarray_log_checking_for_tmc,
    base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: SutTestSettings,
) -> conf_types.ScanConfiguration:
    """
    a subarray in READY state

    :param set_up_subarray_log_checking_for_tmc: To set up subarray log checking for tmc.
    :param base_configuration: the base scan configuration.
    :param subarray_allocation_spec: the specification for the subarray allocation.
    :param sut_settings: the SUT test settings.
    :return: the base configuration for the subarray.
    """
    return base_configuration


# @when("I command it to scan for a given period")


@then("the subarray must be in the SCANNING state until finished")
def the_sdp_subarray_must_be_in_the_scanning_state(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    the SDP subarray must be in the SCANNING state until finished.

    :param configured_subarray: The configured subarray.
    :param context_monitoring: The context monitoring configuration.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    tel = names.TEL()
    tmc_subarray_name = tel.tm.subarray(configured_subarray.id)
    tmc_subarray = con_config.get_device_proxy(tmc_subarray_name)

    result = tmc_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.SCANNING)
    # afterwards it must be ready
    context_monitoring.re_init_builder()
    context_monitoring.wait_for(tmc_subarray_name).for_attribute("obsstate").to_become_equal_to(
        "READY", ignore_first=False, settings=integration_test_exec_settings
    )
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(  # noqa: E501
        str(tmc_subarray_name), time_source="local"
    )
    result = tmc_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)
