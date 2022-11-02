"""Run scan on subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState

from ... import conftest


@pytest.mark.skip(reason="WIP")
@pytest.mark.skamid
@pytest.mark.configure
@scenario(
    "features/sdpln_run_scan.feature",
    "Run scan on sdp subarray in mid using the leaf node",
)
def test_run_scan_on_sdp_subarray_in_mid():
    """Run scan on sdp subarray in mid using the leaf node."""


# @given("an SDP subarray in READY state") from .conftest


@given("a TMC SDP subarray Leaf Node")
def a_sdp_sln():
    """a TMC SDP subarray Leaf Node."""


# @when("I run a scan on the SDP") from ...conftest


@then("the SDP subarray shall go from READY to SCANNING")
def the_subarray_shall_be_in_the_scanning_state(
    allocated_subarray: fxt_types.allocated_subarray,
):
    """the SDP subarray shall go from READY to SCANNING."""
    sub_array_id = allocated_subarray.id
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(sub_array_id))
    result = sdp_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.SCANNING)
