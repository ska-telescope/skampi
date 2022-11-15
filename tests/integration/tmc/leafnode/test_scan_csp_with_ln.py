
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState

from tests.integration import conftest


@pytest.mark.skamid
@scenario(
    "features/tmc_cspln_scan.feature",
    "Scan the csp mid using csp leaf node"
)
def test_scan_cspsubarray_for_a_scan_in_mid():
    """Scan cspsubarray for a scan in mid using the csp leaf node."""

@given("a CSP subarray in the READY state")
def a_csp():
    """a CSP subarray in the READY state."""

@given("a TMC CSP subarray Leaf Node", target_fixture="configuration")
def a_tmc_csp_subarray_leaf_node():
    """a tmc CSP subarray leaf node."""
    tel = names.TEL()
    sut_settings = conftest.SutTestSettings()

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        csp_subarray_leaf_node = con_config.get_device_proxy(
            tel.tm.subarray(index).csp_leaf_node
        )
        result = csp_subarray_leaf_node.ping()
        assert result > 0



@then("the CSP subarray shall go from READY to SCANNING state")
def the_csp_subarray_shall_go_from_ready_to_scanning_state(
    allocated_subarray: fxt_types.allocated_subarray,
):
    """the CSP subarray shall go from READY to SCANNING state."""
    sub_array_id = allocated_subarray.id
    tel = names.TEL()
    csp_subarray = con_config.get_device_proxy(tel.csp.subarray(sub_array_id))
    result = csp_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.SCANNING)