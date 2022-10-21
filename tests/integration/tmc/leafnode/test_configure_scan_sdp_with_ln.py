"""Configure scan on subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState

from ... import conftest


@pytest.mark.skamid
@pytest.mark.configure
@scenario(
    "features/sdpln_configure_scan.feature",
    "Configure scan on sdp subarray in mid using the leaf node"
)
def test_configure_scan_on_sdp_subarray_in_mid():
    """Configure scan on sdp subarray in mid using the leaf node."""


@given("an SDP subarray leaf node", target_fixture="configuration")
def an_sdp_subarray_leaf_node():
    """an SDP subarray leaf node."""
    tel = names.TEL()
    sut_settings = conftest.SutTestSettings()

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        sdp_subarray_leaf_node = con_config.get_device_proxy(
            tel.tm.subarray(index).sdp_leaf_node
        )
        result = sdp_subarray_leaf_node.ping()
        assert result > 0

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
