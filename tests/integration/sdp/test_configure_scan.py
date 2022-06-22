"""Configure scan on subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState

from .. import conftest

@pytest.mark.skalow
@pytest.mark.configure
@scenario(
    "features/sdp_configure_scan.feature", "Configure scan on sdp subarray in low"
)
def test_configure_scan_on_sdp_subarray_in_low():
    """Configure scan on sdp subarray in low."""


@pytest.mark.skamid
@pytest.mark.configure
@scenario(
    "features/sdp_configure_scan.feature", "Configure scan on sdp subarray in mid"
)
def test_configure_scan_on_sdp_subarray_in_mid():
    """Configure scan on sdp subarray in mid."""


@given("an SDP subarray in IDLE state", target_fixture="configuration")
def an_sdp_subarray_in_idle_state(
    set_up_subarray_log_checking_for_sdp,
    sdp_base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: conftest.SutTestSettings,
) -> conf_types.ScanConfiguration:
    """an SDP subarray in IDLE state."""
    subarray_allocation_spec.receptors = sut_settings.receptors
    subarray_allocation_spec.subarray_id = sut_settings.subarray_id
    # will use default composition for the allocated subarray
    # subarray_allocation_spec.composition
    return sdp_base_configuration


# use when from global conftest
# @when("I configure it for a scan")


@then("the subarray must be in the READY state")
def the_subarray_must_be_in_the_ready_state(
    allocated_subarray: fxt_types.allocated_subarray,
):
    """the subarray must be in the READY state."""
    sub_array_id = allocated_subarray.id
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(sub_array_id))
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)


# mocking


@pytest.mark.skip(reason="only run this test for diagnostic purposes during dev")
@pytest.mark.usefixtures("setup_sdp_mock")
def test_test_sdp_configure_scan(run_mock):
    """Test the test using a mock SUT"""
    run_mock(test_configure_scan_on_sdp_subarray_in_mid)
