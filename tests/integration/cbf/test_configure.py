"""Configure subarray feature tests."""
import logging

import pytest
from pytest_bdd import given, scenario, then
from assertpy import assert_that
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.connectors import configuration as con_config
from resources.models.mvp_model.states import ObsState

from .. import conftest

logger = logging.getLogger(__name__)


@pytest.mark.skamid
@pytest.mark.cbf
@pytest.mark.configure
@scenario(
    "features/cbf_configure_scan.feature",
    "Configure scan on cbf subarray in mid",
)
def test_configure_cbf_mid_subarray():
    """Configure CBF low subarray."""


@pytest.mark.skalow
@pytest.mark.cbf
@pytest.mark.configure
@scenario(
    "features/cbf_configure_scan.feature",
    "Configure scan on cbf subarray in low",
)
def test_configure_cbf_low_subarray():
    """Configure CBF low subarray."""

@given("an CBF subarray", target_fixture="composition")
def an_cbf_subarray(
    set_up_log_checking_for_cbf_subarray,  # pylint: disable=unused-argument
    cbf_base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """an SDP subarray."""
    return cbf_base_composition

@given("an CBF subarray in IDLE state", target_fixture="configuration")
def an_cbf_subarray_in_idle_state(
    set_up_log_checking_for_cbf_subarray,  # pylint: disable=unused-argument
    cbf_base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: conftest.SutTestSettings,
) -> conf_types.ScanConfiguration:
    """an CBF subarray in IDLE state."""
    subarray_allocation_spec.receptors = sut_settings.receptors
    subarray_allocation_spec.subarray_id = sut_settings.subarray_id
    return cbf_base_configuration

# use when from global conftest
# @when("I configure it for a scan")


@then("the CBF subarray must be in READY state ")
def the_subarray_must_be_in_the_ready_state(
    allocated_subarray: fxt_types.allocated_subarray,
):
    """the CBF subarray must be in READY state ."""
    sub_array_id = allocated_subarray.id
    tel = names.TEL()
    cbf_subarray = con_config.get_device_proxy(tel.csp.cbf.subarray(sub_array_id))
    result = cbf_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)
