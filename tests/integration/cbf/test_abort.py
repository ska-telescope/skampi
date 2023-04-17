import pytest


from pytest_bdd import given, scenario, then, when
from assertpy import assert_that

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types


from resources.models.mvp_model.states import ObsState

from ..conftest import SutTestSettings


@pytest.mark.skalow
@pytest.mark.cbf
@pytest.mark.assign
@scenario("features/cbf_abort_scan.feature", "Test successful Abort Scan on CBF")
def test_test_successful_abort_scan_on_cbf():
    """Test successful Abort Scan on CBF."""


@given("a subarray in aborted state whilst busy running a scan")
def a_subarray_in_aborted_state_whilst_busy_running_a_scan(
    configured_subarray: fxt_types.configured_subarray,
    integration_test_exec_settings: fxt_types.exec_settings,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    sut_settings: SutTestSettings,
):
    """a subarray in aborted state whilst busy running a scan."""
    subarray = sut_settings.default_subarray_name
    integration_test_exec_settings.attr_synching = False
    configured_subarray.set_to_scanning(integration_test_exec_settings)
    context_monitoring.builder.set_waiting_on(subarray).for_attribute(
        "obsstate"
    ).to_become_equal_to("ABORTED")
    with context_monitoring.wait_before_complete(integration_test_exec_settings):
        entry_point.abort_subarray(sut_settings.subarray_id)


@when("I restart the subarray")
def i_restart_the_subarray(
    context_monitoring: fxt_types.context_monitoring,
    sut_settings: SutTestSettings,
    integration_test_exec_settings: fxt_types.exec_settings,
    entry_point: fxt_types.entry_point,
):
    """I restart the subarray."""
    subarray = sut_settings.default_subarray_name
    context_monitoring.builder.set_waiting_on(subarray).for_attribute(
        "obsstate"
    ).to_become_equal_to("ABORTED")
    with context_monitoring.wait_before_complete(integration_test_exec_settings):
        entry_point.restart_subarray(sut_settings.subarray_id)


@then("the subarray goes to EMPTY")
def the_subarray_goes_to_empty(
    sut_settings: SutTestSettings,
):
    """the subarray goes to EMPTY."""
    tel = names.TEL()
    cbf_subarray = con_config.get_device_proxy(
        tel.csp.cbf.subarray(sut_settings.subarray_id)
    )
    result = cbf_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.EMPTY)
