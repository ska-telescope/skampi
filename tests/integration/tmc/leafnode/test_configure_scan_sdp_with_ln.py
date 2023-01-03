"""Configure scan on subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState


@pytest.mark.skamid
@pytest.mark.configure
@scenario(
    "features/sdpln_configure_scan.feature",
    "Configure scan on sdp subarray in mid using the leaf node",
)
def test_configure_scan_on_sdp_subarray_in_mid():
    """Configure scan on sdp subarray in mid using the leaf node."""


# @given("an SDP subarray in the IDLE state") from .conftest


@given("a TMC SDP subarray Leaf Node")
def a_sdp_sln(set_sdp_ln_entry_point):
    """a TMC SDP subarray Leaf Node."""


# @when("I configure it for a scan") from ...conftest


@then("the subarray must be in the READY state")
def the_subarray_must_be_in_the_ready_state(
    allocated_subarray: fxt_types.allocated_subarray,
):
    """the subarray must be in the READY state."""
    sub_array_id = allocated_subarray.id
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(sub_array_id))
    result = sdp_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)




@pytest.mark.skalow
@pytest.mark.configure
@scenario(
    "features/tmc_sdpln_configure.feature",
    "Configure the SDP low using SDP leaf node",
)
def test_configure_scan_on_sdp_subarray_in_low():
    """Configure scan on sdp subarray in low using the leaf node."""

@given("a SDP subarray in the IDLE state")
def a_sdp():
    """a SDP subarray in the IDLE state."""

@given("a TMC SDP subarray Leaf Node", target_fixture="configuration")
def a_tmc_sdp_subarray_leaf_node(set_sdp_ln_entry_point):  # type: ignore
    """a tmc CSP subarray leaf node."""


# @when("I configure it for a scan") from ...conftest


@then("the SDP subarray shall go from IDLE to READY state")
def the_sdp_subarray_shall_go_from_idle_to_ready_state(
    allocated_subarray: fxt_types.allocated_subarray,
):
    """the SDP subarray shall go from IDLE to READY state."""
    sub_array_id = allocated_subarray.id
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(sub_array_id))
    result = sdp_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)
