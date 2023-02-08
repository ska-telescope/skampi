"""Assign Resource on a SDP Subarray"""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState
from ...conftest import SutTestSettings

@pytest.mark.skip(reason="Test only TMC's test case")
@pytest.mark.skalow
@pytest.mark.assign
@scenario(
    "features/sdpln_assign_release.feature",
    "Assign resources to sdp low subarray using TMC leaf node",
)
def test_assign_resources_on_sdp_in_low():
    """AssignResources on sdp subarray in low using the leaf node."""


@given("a SDP subarray in the EMPTY state", target_fixture="composition")
def an_sdp_subarray_in_empty_state(
    set_sdp_ln_entry_point,
    base_composition: conf_types.Composition
) -> conf_types.Composition:
    """an SDP subarray in Empty state."""
    return base_composition


@given("a TMC SDP subarray Leaf Node")
def a_sdp_sln():
    """a TMC SDP subarray Leaf Node."""


# @when("I assign resources to it") from ...conftest


@then("the SDP subarray must be in IDLE state")
def the_sdp_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
    """the SDP Subarray must be in IDLE state."""
    tel = names.TEL()
    subarray = con_config.get_device_proxy(
        tel.sdp.subarray(sut_settings.subarray_id)
    )
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)
