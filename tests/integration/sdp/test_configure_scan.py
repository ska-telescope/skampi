"""Configure scan on subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

@pytest.mark.skip
@pytest.mark.skalow
@pytest.mark.configure
@pytest.mark.sdp
@scenario(
    "features/sdp_configure_scan.feature",
    "Configure scan on sdp subarray in low",
)
def test_configure_scan_on_sdp_subarray_in_low():
    """Configure scan on sdp subarray in low."""


@pytest.mark.skamid
@pytest.mark.configure
@pytest.mark.sdp
@scenario(
    "features/sdp_configure_scan.feature",
    "Configure scan on sdp subarray in mid",
)
def test_abort_configuring_in_mid():
    """Configure scan on sdp subarray in mid."""


@pytest.mark.skamid
@pytest.mark.configure
@pytest.mark.sdp
@scenario(
    "features/sdp_configure_scan.feature",
    "Configure scan on sdp subarray in mid",
)
def test_configure_scan_on_sdp_subarray_in_mid():
    """Configure scan on sdp subarray in mid."""


# use from local conftest
# @given("an SDP subarray in IDLE state", target_fixture="configuration")

# use when from global conftest
# @when("I configure it for a scan")


@then("the subarray must be in the READY state")
def the_subarray_must_be_in_the_ready_state(
    allocated_subarray: fxt_types.allocated_subarray,
):
    """
    the subarray must be in the READY state.

    :param allocated_subarray: The allocated subarray to be configured.
    """
    sub_array_id = allocated_subarray.id
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(sub_array_id))
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)


# mocking


@pytest.mark.skip(reason="only run this test for diagnostic purposes during dev")
@pytest.mark.usefixtures("setup_sdp_mock")
def test_test_sdp_configure_scan(run_mock):
    """
    Test the test using a mock SUT
    :param run_mock: run mock object
    """
    run_mock(test_configure_scan_on_sdp_subarray_in_mid)
