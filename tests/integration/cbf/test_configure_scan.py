import pytest


from pytest_bdd import given, scenario, then
from assertpy import assert_that

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState

from ..conftest import SutTestSettings
from .. import conftest


@pytest.mark.skalow
@pytest.mark.cbf
@pytest.mark.configure
@scenario("features/cbf_configure_scan.feature", "Configure scan on CBF low subarray")
def test_configure_scan_on_cbf_low_subarray():
    """Configure scan on CBF low subarray."""


@given("an CBF subarray in IDLE state", target_fixture="configuration")
def an_cbf_subarray_in_idle_state(
    set_up_log_checking_for_cbf_subarray,  # pylint: disable=unused-argument
    cbf_base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: conftest.SutTestSettings,
) -> None:
    """an CBF subarray in IDLE state."""
    subarray_allocation_spec.receptors = sut_settings.receptors
    subarray_allocation_spec.subarray_id = sut_settings.subarray_id
    return cbf_base_configuration


# use when from ..shared_assign_resources in ..conftest.py
# @when("I assign resources to it")

# use when from ..shared_assign_resources in ..conftest.py
# @when("I configure it for scan")


@then("the CBF subarray must be in READY state")
def the_cbf_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    cbf_subarray = con_config.get_device_proxy(
        tel.csp.cbf.subarray(sut_settings.subarray_id)
    )
    result = cbf_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)


# mock tests
# TODO
