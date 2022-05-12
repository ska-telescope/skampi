"""Start up the telescope from tmc feature tests."""
import logging
import os

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names

from .. import conftest

logger = logging.getLogger(__name__)


@pytest.mark.skamid
@pytest.mark.startup
@scenario(
    "features/tmc_start_up_telescope.feature", "Start up the telescope (SDP only)"
)
def test_tmc_start_up_telescope_mid_sdp_only():
    """Start up the telescope in mid  (sdp only)."""


@pytest.mark.skamid
@pytest.mark.standby
@scenario(
    "features/tmc_start_up_telescope.feature", "Switch of the telescope (SDP only)"
)
def test_tmc_off_telescope_mid_sdp_only():
    """Off the telescope in mid  (sdp only)."""


@given("an TMC")
def a_tmc():
    """an TMC"""


@given("an partial Telescope consisting of SDP only")
def a_partial_telescope():
    """an partial Telescope consisting of SDP only"""


@given("an partial Telescope consisting of SDP only that is ON")
def a_partial_telescope_with_sdp_on():
    """an partial Telescope consisting of SDP only that is ON"""

# when
# use @when("I start up the telescope") from ..conftest

# when
# use @when("I switch off the telescope") from ..conftest

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


@then("the sdp must be off")
def the_sdp_must_be_off(sut_settings: conftest.SutTestSettings):
    """the sdp must be off."""
    tel = names.TEL()
    sdp_master = con_config.get_device_proxy(tel.sdp.master)
    result = sdp_master.read_attribute("state").value
    assert_that(str(result)).is_equal_to("OFF")
    for index in range(1, sut_settings.nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.sdp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("OFF")