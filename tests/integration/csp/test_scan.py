"""Configure scan on subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from .. import conftest


@pytest.mark.skip(reason="Disable test as it need update to support new JSON Schema")
@pytest.mark.skalow
@pytest.mark.scan
@scenario("features/csp_scan.feature", "Run a scan on csp subarray in low")
def test_run_a_scan_on_csp_subarray_in_low():
    """Run a scan on csp subarray in low."""


@pytest.mark.skamid
@pytest.mark.scan
@scenario("features/csp_scan.feature", "Run a scan on csp subarray in mid")
def test_run_a_scan_on_csp_subarray_in_mid():
    """Run a scan on sdp subarray in mid."""


@pytest.mark.skamid
@pytest.mark.scan
@pytest.mark.csp
@scenario("features/csp_scan.feature", "Abort Csp scanning")
def test_abort_scanning(disable_clear):
    """Abort scanning.
    :param disable_clear: A disable clear object
    """

# use from local conftest
# @given("an CSP subarray in READY state")

# use when from global conftest
# @when("I command it to scan for a given period")


@then("the CSP subarray must be in the SCANNING state until finished")
def the_csp_subarray_must_be_in_the_scanning_state(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    the SDP subarray must be in the SCANNING state until finished.

    :param configured_subarray: The configured subarray
    :param context_monitoring: Context monitoring object.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    tel = names.TEL()
    csp_subarray_name = tel.csp.subarray(configured_subarray.id)
    csp_subarray = con_config.get_device_proxy(csp_subarray_name)

    result = csp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.SCANNING)
    # afterwards it must be ready
    context_monitoring.re_init_builder()
    context_monitoring.wait_for(csp_subarray_name).for_attribute("obsstate").to_become_equal_to(
        "READY", ignore_first=False, settings=integration_test_exec_settings
    )
    result = csp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)
