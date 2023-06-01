"""Start up the csp feature tests."""
import logging
import os

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from .. import conftest

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.csp_startup
@pytest.mark.csp_related
@pytest.mark.skamid
@pytest.mark.csplmc
@pytest.mark.startup
@scenario("features/csp_start_up_telescope.feature", "Start up the csp in mid")
def test_csp_start_up_telescope_mid():
    """Start up the csp in mid."""


@pytest.mark.csp_startup
@pytest.mark.csp_related
@pytest.mark.skalow
@pytest.mark.csplmc
@pytest.mark.startup
@scenario("features/csp_start_up_telescope.feature", "Start up the csp in low")
def test_csp_start_up_telescope_low():
    """Start up the csp in low."""


# log checking


@pytest.fixture(name="set_up_log_checking_for_csp")
@pytest.mark.usefixtures("set_csp_entry_point")
def fxt_set_up_log_checking_for_csp(
    log_checking: fxt_types.log_checking,
    sut_settings: conftest.SutTestSettings,
):
    """Set up log checking (using log consumer) on cbf.
    :param log_checking: skallop fixture used to set up log checking.
    :param sut_settings: A class representing the settings for the system under test.
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        cbf_controller = str(tel.csp.controller)
        subarray = str(tel.csp.subarray(sut_settings.subarray_id))
        log_checking.capture_logs_from_devices(cbf_controller, subarray)


@given("an CSP")
def a_csp(
    set_up_log_checking_for_csp,  # pylint: disable=unused-argument
):
    """
    a CSP.

    :param set_up_log_checking_for_csp: skallop fixture used to set up log checking.
    """


# when
# use @when("I start up the telescope") from ..conftest


@then("the csp must be on")
def the_csp_must_be_on(
    sut_settings: conftest.SutTestSettings,
):
    """
    the csp must be on.

    :param sut_settings: A class representing the settings for the system under test.
    """
    tel = names.TEL()
    csp_master = con_config.get_device_proxy(tel.csp.controller)
    result = csp_master.read_attribute("state").value
    assert_that(str(result)).is_equal_to("ON")
    nr_of_subarrays = sut_settings.nr_of_subarrays
    for index in range(1, nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.csp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("ON")


# test validation
@pytest.mark.test_tests
@pytest.mark.usefixtures("setup_csp_mock")
def test_test_csp_startup(run_mock):
    """Test the test using a mock SUT
    :param run_mock: a run mock object
    """
    run_mock(test_csp_start_up_telescope_mid)
