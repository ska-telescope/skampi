"""Configure a scan on csp subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types


@pytest.mark.tmc
@pytest.mark.csp_related
@pytest.mark.skamid
@scenario(
    "features/tmc_cspln_configure.feature",
    "Configure the csp mid using csp leaf node",
)
def test_configure_cspsubarray_for_a_scan_in_mid():
    """Configure cspsubarray for a scan in mid using the csp leaf node."""


@pytest.mark.tmc
@pytest.mark.csp_related
@pytest.mark.skalow
@scenario(
    "features/tmc_cspln_configure.feature",
    "Configure the csp low using csp leaf node",
)
def test_configure_cspsubarray_for_a_scan_in_low():
    """Configure cspsubarray for a scan in low using the csp leaf node."""


@given("a CSP subarray in the IDLE state")
def a_csp():
    """a CSP subarray in the IDLE state."""


@given("a TMC CSP subarray Leaf Node", target_fixture="configuration")
def a_tmc_csp_subarray_leaf_node(set_csp_ln_entry_point):
    """
    a tmc CSP subarray leaf node.

    :param set_csp_ln_entry_point: An object to set csp leafnode entry point
    """


# @when("I configure it for a scan") from ...conftest


@then("the CSP subarray shall go from IDLE to READY state")
def the_csp_subarray_shall_go_from_idle_to_ready_state(
    allocated_subarray: fxt_types.allocated_subarray,
):
    """
    the CSP subarray shall go from IDLE to READY state.

    :param allocated_subarray: The allocated subarray to be configured.
    """
    sub_array_id = allocated_subarray.id
    tel = names.TEL()
    csp_subarray = con_config.get_device_proxy(tel.csp.subarray(sub_array_id))
    result = csp_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)
