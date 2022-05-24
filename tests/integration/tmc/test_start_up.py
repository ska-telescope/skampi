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
nr_of_subarrays = 1

# @pytest.mark.skip(reason="SKB-144 caused by duplicate deviceservers deployed by TMC mocks")
@pytest.mark.skamid
@pytest.mark.startup
@scenario(
    "features/tmc_start_up_telescope.feature", "Start up the telescope"
)
def test_tmc_start_up_telescope_mid():
    """Start up the telescope in mid."""


# @pytest.mark.skip(reason="SKB-144 caused by duplicate deviceservers deployed by TMC mocks")
@pytest.mark.skamid
@pytest.mark.standby
@scenario(
    "features/tmc_start_up_telescope.feature", "Switch of the telescope"
)
def test_tmc_off_telescope_mid_sdp():
    """Off the telescope in mid."""


@given("an TMC")
def a_tmc():
    """an TMC"""


@given("a Telescope consisting SDP, CSP and a Dish")
def a_telescope_with_csp_sdp_and_dish():
    """a Telescope consisting SDP, CSP and a Dish"""


@given("a Telescope consisting SDP, CSP and a Dish that is ON")
def a_telescope_with_sdp_csp_and_dish_on():
    """a Telescope consisting SDP, CSP and a Dish that is ON"""

# when
# use @when("I start up the telescope") from ..conftest

# when
# use @when("I switch off the telescope") from ..conftest

# thens


@then("the sdp, csp and dish must be on")
def the_sdp_csp_and_dish_must_be_on(sut_settings: conftest.SutTestSettings):
    """the sdp, csp and dish must be on."""
    tel = names.TEL()
    mid = names.Mid()
    # Check state attribute of SDP Master
    sdp_master = con_config.get_device_proxy(tel.sdp.master)
    result = sdp_master.read_attribute("state").value
    assert_that(str(result)).is_equal_to("ON")
    for index in range(1, sut_settings.nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.sdp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("ON")
    # Check state attribute of CSP Master
    csp_master = con_config.get_device_proxy(tel.csp.controller)
    result = csp_master.read_attribute("state").value
    assert_that(str(result)).is_equal_to("ON")
    for index in range(1, sut_settings.nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.csp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("ON")
    # Check state attribute of Dish Master
    dish1 = con_config.get_device_proxy(mid.dish(1))
    result = dish1.read_attribute("state").value
    assert_that(str(result)).is_equal_to("ON")
    # Check telescopeState attribute of Central Node
    central_node = con_config.get_device_proxy(tel.tm.central_node)
    result = central_node.read_attribute("telescopeState").value
    assert_that(str(result)).is_equal_to("ON")


@then("the sdp, csp and dish must be off")
def the_sdp_csp_and_dish_must_be_off(sut_settings: conftest.SutTestSettings):
    """the sdp, csp and dish must be off."""
    tel = names.TEL()
    mid = names.Mid()
    # Check state attribute of SDP Master
    sdp_master = con_config.get_device_proxy(tel.sdp.master)
    result = sdp_master.read_attribute("state").value
    assert_that(str(result)).is_equal_to("OFF")
    for index in range(1, sut_settings.nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.sdp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("OFF")
    # Check state attribute of CSP Master
    csp_master = con_config.get_device_proxy(tel.csp.controller)
    result = csp_master.read_attribute("state").value
    assert_that(str(result)).is_equal_to("OFF")
    for index in range(1, sut_settings.nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.csp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("OFF")
    # Check state attribute of Dish Master
    dish1 = con_config.get_device_proxy(mid.dish(1))
    result = dish1.read_attribute("state").value
    assert_that(str(result)).is_equal_to("OFF")
    # Check telescopeState attribute of Central Node
    central_node = con_config.get_device_proxy(tel.tm.central_node)
    result = central_node.read_attribute("telescopeState").value
    assert_that(str(result)).is_equal_to("OFF")
