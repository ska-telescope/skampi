
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from tests.integration import conftest





@pytest.mark.trupti
@pytest.mark.skalow
@scenario(
    "features/tmc_cspln_assign.feature",
    "Assign resources to csp low subarray using TMC leaf node"
)
def test_assign_resources_on_csp_in_low():
    """Scan cspsubarray for a scan in low using the csp leaf node."""


@given("a CSP subarray in the EMPTY state")
def a_csp():
    """a CSP subarray in the EMPTY state."""

@given("a TMC CSP subarray Leaf Node", target_fixture="assign")
def a_tmc_csp_subarray_leaf_node(set_csp_ln_entry_point,base_composition: conf_types.Composition):
    """a tmc CSP subarray leaf node."""
    tel = names.TEL()
    sut_settings = conftest.SutTestSettings()

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        csp_subarray_leaf_node = con_config.get_device_proxy(
            tel.tm.subarray(index).csp_leaf_node
        )
        result = csp_subarray_leaf_node.ping()
        assert result > 0
    #return base_composition



@then("the CSP subarray must be in IDLE state")
def the_csp_subarray_must_be_in_idle_state(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """The CSP goes back to READY state when finished"""
    tel = names.TEL()
    csp_subarray_name = tel.csp.subarray(configured_subarray.id)
    csp_subarray = con_config.get_device_proxy(csp_subarray_name)
    context_monitoring.re_init_builder()
    context_monitoring.wait_for(csp_subarray_name).for_attribute(
        "obsstate"
    ).to_become_equal_to(
        "IDLE", ignore_first=False, settings=integration_test_exec_settings
    )
    result = csp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.IDLE)