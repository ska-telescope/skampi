"""Start up the sdp feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from . import conftest


@pytest.mark.skamid
@scenario("features/sdp_start_up_telescope.feature", "Start up the sdp in mid")
def test_sdp_start_up_telescope_mid():
    """Start up the sdp in mid."""


@pytest.mark.skalow
@scenario("features/sdp_start_up_telescope.feature", "Start up the sdp in low")
def test_sdp_start_up_telescope_low():
    """Start up the sdp in low."""


@pytest.mark.skalow
@scenario("features/csp_start_up_telescope.feature", "Start up the csp in mid")
def test_csp_start_up_telescope_mid():
    """Start up the csp in mid."""


@pytest.mark.skalow
@scenario("features/csp_start_up_telescope.feature", "Start up the csp in low")
def test_csp_start_up_telescope_low():
    """Start up the csp in low."""


@given("an SDP")
def a_sdp(set_sdp_entry_point):
    """a SDP."""


@given("an CSP")
def a_csp(set_csp_entry_point):
    """a SDP."""


@when("I start up the telescope")
def i_start_up_the_telescope(
    standby_telescope: fxt_types.standby_telescope,
    entry_point: fxt_types.entry_point,
):
    """I start up the telescope."""
    with standby_telescope.wait_for_starting_up():
        entry_point.set_telescope_to_running()


@then("the sdp must be on")
def the_sdp_must_be_on():
    """the sdp must be on."""
    tel = names.TEL()
    sdp_master = con_config.get_device_proxy(tel.sdp.master)
    result = sdp_master.read_attribute("state").value
    assert_that(result).is_equal_to("ON")
    for index in range(1, conftest.NR_OFF_SUBARRAYS + 1):
        subarray = con_config.get_device_proxy(tel.sdp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(result).is_equal_to("ON")


@then("the csp must be on")
def the_csp_must_be_on():
    """the csp must be on."""
    tel = names.TEL()
    csp_master = con_config.get_device_proxy(tel.csp.master)
    result = csp_master.read_attribute("state").value
    assert_that(result).is_equal_to("ON")
    for index in range(1, conftest.NR_OFF_SUBARRAYS + 1):
        subarray = con_config.get_device_proxy(tel.csp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(result).is_equal_to("ON")


@pytest.mark.skip(reason="only run this test for diagnostic purposes during dev")
@pytest.mark.usefixtures("setup_sdp_mock")
def test_test_sdp_startup(run_mock):
    """Test the test using a mock SUT"""
    run_mock(test_sdp_start_up_telescope_mid)


@pytest.fixture(name="setup_csp_mock")
def fxt_setup_csp_mock(mock_entry_point: fxt_types.mock_entry_point):
    @mock_entry_point.when_set_telescope_to_running
    def mck_set_telescope_to_running():
        mock_entry_point.model.csp.set_states_for_telescope_running()

    @mock_entry_point.when_set_telescope_to_standby
    def mck_set_telescope_to_standby():
        mock_entry_point.model.csp.set_states_for_telescope_standby()


# @pytest.mark.skip(reason="only run this test for diagnostic purposes during dev")
@pytest.mark.usefixtures("setup_csp_mock")
def test_test_csp_startup(run_mock):
    """Test the test using a mock SUT"""
    run_mock(test_csp_start_up_telescope_mid)
