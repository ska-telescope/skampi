"""Configure scan on telescope subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types


from resources.models.mvp_model.states import ObsState

from ..conftest import SutTestSettings

@pytest.mark.skamid
@pytest.mark.configure
@scenario("features/tmc_configure_scan.feature", "Configure scan on telescope subarray in mid")
def test_configure_scan_on_tmc_subarray_in_mid():
    """Configure scan on telescope subarray in mid."""


# @given("a telescope subarray in IDLE state", target_fixture="configuration")
# def an_telescope_subarray_in_idle_state(
#     set_up_subarray_log_checking_for_tmc,
#     base_configuration: conf_types.ScanConfiguration,
#     subarray_allocation_spec: fxt_types.subarray_allocation_spec,
#     sut_settings: SutTestSettings,
# ) -> conf_types.ScanConfiguration:
#     """a telescope subarray in IDLE state."""
#     subarray_allocation_spec.receptors = sut_settings.receptors
#     subarray_allocation_spec.subarray_id = sut_settings.subarray_id
#     return base_configuration

@given("an TMC")
def a_tmc():
    """an TMC"""


@given("an telescope subarray", target_fixture="composition")
def an_telescope_subarray(
    set_up_subarray_log_checking_for_tmc, base_composition: conf_types.Composition
) -> conf_types.Composition:
    """an telescope subarray."""
    return base_composition


@given("a subarray in the IDLE state")
def a_subarray_in_the_idle_state():
    """a subarray in the IDLE state."""

# @when("I configure it for scan")


@then("the subarray must be in the READY state")
def the_subarray_must_be_in_the_ready_state(
    allocated_subarray: fxt_types.allocated_subarray,
):
    """the subarray must be in the READY state."""
    sub_array_id = allocated_subarray.id
    tel = names.TEL()
    tmc_subarray = con_config.get_device_proxy(tel.tm.subarray(sub_array_id))
    result = tmc_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)

