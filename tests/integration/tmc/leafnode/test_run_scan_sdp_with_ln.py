"""Run scan on subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from ... import conftest


@pytest.mark.skamid
@pytest.mark.configure
@scenario(
    "features/sdpln_run_scan.feature",
    "Run scan on sdp subarray in mid using the leaf node",
)
def test_run_scan_on_sdp_subarray_in_mid():
    """Run scan on sdp subarray in mid using the leaf node."""


@pytest.mark.skalow
@pytest.mark.configure
@scenario(
    "features/tmc_sdpln_scan.feature",
    "Scan the SDP low using SDP leaf node",
)
def test_run_scan_on_sdp_subarray_in_low():
    """Run scan on SDP subarray in low using the leaf node."""


@given("an SDP subarray in READY state")
def an_sdp_subarray_in_ready_state(
    sdp_base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: conftest.SutTestSettings,
) -> conf_types.ScanConfiguration:
    """
    an SDP subarray in READY state.

    :param sdp_base_configuration: the base configuration for the SDP subarray
    :param subarray_allocation_spec: Fixture for subarray allocation specification
    :param sut_settings: A class representing the settings for the system under test.
    :return: the updated sdp base configuration for the SDP subarray
    """
    subarray_allocation_spec.receptors = sut_settings.receptors
    subarray_allocation_spec.subarray_id = sut_settings.subarray_id
    # will use default composition for the allocated subarray
    # subarray_allocation_spec.composition
    return sdp_base_configuration


@given("a TMC SDP subarray Leaf Node")
def a_sdp_sln(set_sdp_ln_entry_point):
    """
    a TMC SDP subarray Leaf Node.

    :param set_sdp_ln_entry_point: An object to set sdp leafnode entry point
    """


# @when("I command it to scan for a given period") from ...conftest


@then("the SDP subarray shall go from READY to SCANNING")
def the_subarray_shall_be_in_the_scanning_state(
    configured_subarray: fxt_types.configured_subarray,
):
    """
    the SDP subarray shall go from READY to SCANNING.

    :param configured_subarray: The configured subarray.
    """
    tel = names.TEL()
    sdp_subarray_name = tel.sdp.subarray(configured_subarray.id)
    sdp_subarray = con_config.get_device_proxy(sdp_subarray_name)

    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.SCANNING)


@then("the SDP shall go back to READY when finished")
def the_subarray_goes_back_to_ready_state(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    The SDP goes back to READY state when finished

    :param configured_subarray: The configured subarray
    :param context_monitoring: Context monitoring object.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    tel = names.TEL()
    sdp_subarray_name = tel.sdp.subarray(configured_subarray.id)
    sdp_subarray = con_config.get_device_proxy(sdp_subarray_name)
    context_monitoring.re_init_builder()
    context_monitoring.wait_for(sdp_subarray_name).for_attribute(
        "obsstate"
    ).to_become_equal_to(
        "READY", ignore_first=False, settings=integration_test_exec_settings
    )
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)
