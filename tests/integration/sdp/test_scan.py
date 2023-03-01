"""Configure scan on subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState


@pytest.mark.skalow
@pytest.mark.scan
@pytest.mark.sdp
@scenario("features/sdp_scan.feature", "Run a scan on sdp subarray in low")
def test_run_a_scan_on_sdp_subarray_in_low():
    """CRun a scan on sdp subarray in low."""


@pytest.mark.skamid
@pytest.mark.scan
@pytest.mark.sdp
@scenario("features/sdp_scan.feature", "Run a scan on sdp subarray in mid")
def test_run_a_scan_on_sdp_subarray_in_mid():
    """Run a scan on sdp subarray in mid."""


# use from local conftest
# @given("an SDP subarray in READY state")


# use when from global conftest
# @when("I command it to scan for a given period")


@then("the SDP subarray must be in the SCANNING state until finished")
def the_sdp_subarray_must_be_in_the_scanning_state(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """the SDP subarray must be in the SCANNING state until finished."""
    tel = names.TEL()
    sdp_subarray_name = tel.sdp.subarray(configured_subarray.id)
    sdp_subarray = con_config.get_device_proxy(sdp_subarray_name)

    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.SCANNING)
    # afterwards it must be ready
    context_monitoring.re_init_builder()
    context_monitoring.wait_for(sdp_subarray_name).for_attribute(
        "obsstate"
    ).to_become_equal_to(
        "READY", ignore_first=False, settings=integration_test_exec_settings
    )
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)
