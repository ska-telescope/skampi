"""Start up the sdp feature tests."""
import logging

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names

from . import conftest

logger = logging.getLogger(__name__)


@pytest.mark.skamid
@pytest.mark.startup
@scenario(
    "features/sdpln_start_up_telescope.feature",
    "Start up the sdp in mid using the leaf node",
)
def test_sdpln_start_up_telescope_mid():
    """Start up the sdp in mid using the ln."""


@pytest.mark.skalow
@pytest.mark.startup
@scenario(
    "features/sdpln_start_up_telescope.feature",
    "Start up the sdp in low using the leaf node",
)
def test_sdpln_start_up_telescope_low():
    """Start up the sdp in low using the ln."""
    logger.info("Started test execution")


@given("an SDP")
def a_sdp(set_sdp_ln_entry_point):
    """a SDP."""
    logger.info("Entry point set to %s", set_sdp_ln_entry_point)


@given("an SDP leaf node")
def a_sdp_ln():
    """a SDP leaf node."""


# when
# use @when("I start up the telescope") from .conftest

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
