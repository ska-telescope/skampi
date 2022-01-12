"""Start up the sdp feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from . import conftest


@pytest.mark.skamid
@pytest.mark.startup
@scenario("features/sdp_start_up_telescope.feature", "Start up the sdp in mid")
def test_sdp_start_up_telescope_mid():
    """Start up the sdp in mid."""


@pytest.mark.skalow
@pytest.mark.startup
@scenario("features/sdp_start_up_telescope.feature", "Start up the sdp in low")
def test_sdp_start_up_telescope_low():
    """Start up the sdp in low."""


@pytest.mark.skamid
@pytest.mark.startup
@scenario("features/cbf_start_up_telescope.feature", "Start up the cbf in mid")
def test_cbf_start_up_telescope_mid():
    """Start up the cbf in mid."""


@pytest.mark.skalow
@pytest.mark.startup
@scenario("features/cbf_start_up_telescope.feature", "Start up the cbf in low")
def test_cbf_start_up_telescope_low():
    """Start up the cbf in low."""


@pytest.mark.skalow
@pytest.mark.startup
@pytest.mark.skip(reason="current csp mid version not able to do start up")
@scenario("features/csp_start_up_telescope.feature", "Start up the csp in mid")
def test_csp_start_up_telescope_mid():
    """Start up the csp in mid."""


@pytest.mark.skalow
@pytest.mark.startup
@scenario("features/csp_start_up_telescope.feature", "Start up the csp in low")
def test_csp_start_up_telescope_low():
    """Start up the csp in low."""


@pytest.mark.skalow
@pytest.mark.startup
@scenario("features/mccs_start_up_telescope.feature", "Start up the MCCS")
def test_mccs_start_up_telescope():
    """Start up the csp in low."""


@given("an SDP")
def a_sdp(set_sdp_entry_point):
    """a SDP."""


@given("an CSP")
def a_csp(set_csp_entry_point):
    """a CSP."""


@given("an CBF")
def a_cbf(set_cbf_entry_point):
    """a CBF."""


@given("the MCCS")
def a_mccs(set_mccs_entry_point):
    """a MCCS."""


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
    csp_master = con_config.get_device_proxy(tel.csp.controller)
    result = csp_master.read_attribute("state").value
    assert_that(result).is_equal_to("ON")
    for index in range(1, conftest.NR_OFF_SUBARRAYS + 1):
        subarray = con_config.get_device_proxy(tel.csp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(result).is_equal_to("ON")


@then("the cbf must be on")
def the_cbf_must_be_on():
    """the cbf must be on."""
    tel = names.TEL()
    cbf_controller = con_config.get_device_proxy(tel.csp.cbf.controller)
    result = cbf_controller.read_attribute("state").value
    assert_that(result).is_equal_to("ON")
    # only check subarray 1 for cbf low
    if tel.skalow:
        nr_of_subarrays = 1
    else:
        nr_of_subarrays = conftest.NR_OFF_SUBARRAYS
    for index in range(1, nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.csp.cbf.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(result).is_equal_to("ON")


@then("the MCCS must be on")
def the_mccs_must_be_on():
    """the MCCS must be on."""
    tel = names.TEL()
    assert tel.skalow
    mccs_controller = con_config.get_device_proxy(tel.skalow.mccs.master)
    result = mccs_controller.read_attribute("state").value
    assert_that(result).is_equal_to("ON")
    # only check subarray 1 for cbf low


@pytest.mark.skip(reason="only run this test for diagnostic purposes during dev")
@pytest.mark.usefixtures("setup_sdp_mock")
def test_test_sdp_startup(run_mock):
    """Test the test using a mock SUT"""
    run_mock(test_sdp_start_up_telescope_mid)


@pytest.mark.skip(reason="only run this test for diagnostic purposes during dev")
@pytest.mark.usefixtures("setup_csp_mock")
def test_test_csp_startup(run_mock):
    """Test the test using a mock SUT"""
    run_mock(test_csp_start_up_telescope_mid)


@pytest.mark.skip(reason="only run this test for diagnostic purposes during dev")
@pytest.mark.usefixtures("setup_cbf_mock")
def test_test_cbf_startup(run_mock):
    """Test the test using a mock SUT"""
    run_mock(test_cbf_start_up_telescope_mid)
