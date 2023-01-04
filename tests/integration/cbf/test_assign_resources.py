import pytest


from pytest_bdd import given, scenario, then
from assertpy import assert_that

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

from resources.models.mvp_model.states import ObsState

from ..conftest import SutTestSettings

## @pytest.mark.skamid
@pytest.mark.cbf
@pytest.mark.assign
@scenario(
    "features/cbf_assign_resources.feature", "Assign resources to CBF mid subarray"
)
def test_assign_resources_to_cbf_mid_subarray():
    """Assign resources to CBF mid subarray."""


@pytest.mark.skip(reason="cbf low not integrated")
## @pytest.mark.skalow
@pytest.mark.cbf
@pytest.mark.assign
@scenario(
    "features/cbf_assign_resources.feature", "Assign resources to CBF low subarray"
)
def test_assign_resources_to_cbf_low_subarray():
    """Assign resources to CBF low subarray."""


@given("an CBF subarray", target_fixture="composition")
def an_cbf_subarray(
    set_up_log_checking_for_cbf_subarray,  # pylint: disable=unused-argument
    cbf_base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """an SDP subarray."""
    return cbf_base_composition


# use when from ..shared_assign_resources in ..conftest.py
# @when("I assign resources to it")


@then("the CBF subarray must be in IDLE state")
def the_cbf_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    cbf_subarray = con_config.get_device_proxy(
        tel.csp.cbf.subarray(sut_settings.subarray_id)
    )
    result = cbf_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.IDLE)


# mock tests
# TODO
