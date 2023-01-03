"""Assign Resource on a SDP Subarray"""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState
from ... import conftest
from ...conftest import SutTestSettings 

@pytest.mark.skalow
@pytest.mark.assign
@scenario(
    "features/sdpln_assign_release.feature",
    "Assign Release resources on sdp subarray in low using the leaf node",
)

def test_assign_release_on_sdp_subarray_in_low():
    """Assign Release on sdp subarray in low using the leaf node."""


@given("an SDP subarray in Empty state")
def an_sdp_subarray_in_empty_state(
    sdp_base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: conftest.SutTestSettings,
) -> conf_types.ScanConfiguration:
    """an SDP subarray in Empty state."""
    subarray_allocation_spec.receptors = sut_settings.receptors
    subarray_allocation_spec.subarray_id = sut_settings.subarray_id
    # will use default composition for the allocated subarray
    # subarray_allocation_spec.composition
    return sdp_base_configuration


@given("a TMC SDP subarray Leaf Node")
def a_sdp_sln(set_sdp_ln_entry_point):
    """a TMC SDP subarray Leaf Node."""


# @when("I command it to assign resource for a given period") from ...conftest

@then("the subarray must be in IDLE state")
def the_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)
