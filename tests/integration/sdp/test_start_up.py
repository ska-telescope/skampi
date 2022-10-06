"""Start up the sdp feature tests."""
import logging

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names

from .. import conftest

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="Temporary skips for testing")
@pytest.mark.skamid
@pytest.mark.startup
@scenario("features/sdp_start_up_telescope.feature", "Start up the sdp in mid")
def test_sdp_start_up_telescope_mid():
    """Start up the sdp in mid."""


@pytest.mark.skip(reason="Temporary skips for testing")
@pytest.mark.skalow
@pytest.mark.startup
@scenario("features/sdp_start_up_telescope.feature", "Start up the sdp in low")
def test_sdp_start_up_telescope_low():
    """Start up the sdp in low."""


@given("an SDP")
def a_sdp():
    """a SDP."""


# when
# use @when("I start up the telescope") from ..shared_startup

# thens


@then("the sdp must be on")
def the_sdp_must_be_on(sut_settings: conftest.SutTestSettings):
    """the sdp must be on."""
    tel = names.TEL()
    sdp_master = con_config.get_device_proxy(tel.sdp.master)
    result = sdp_master.read_attribute("state").value
    assert_that(str(result)).is_equal_to("ON")
    for index in range(1, sut_settings.nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.sdp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("ON")


# test validation


@pytest.mark.skip(reason="Temporary skips for testing")
@pytest.mark.test_tests
@pytest.mark.usefixtures("setup_sdp_mock")
def test_test_sdp_startup(run_mock):
    """Test the test using a mock SUT"""
    run_mock(test_sdp_start_up_telescope_mid)
