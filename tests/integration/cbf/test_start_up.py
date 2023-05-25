"""Start up the cbf feature tests."""
import logging
import os
from typing import List, cast

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.skamid
@pytest.mark.cbf
@pytest.mark.startup
@scenario("features/cbf_start_up_telescope.feature", "Start up the cbf in mid")
def test_cbf_start_up_telescope_mid():
    """Start up the cbf in mid."""


@pytest.mark.csp_related
@pytest.mark.skalow
@pytest.mark.cbf
@pytest.mark.startup
@scenario("features/cbf_start_up_telescope.feature", "Start up the cbf in low")
def test_cbf_start_up_telescope_low():
    """Start up the cbf in low."""


@pytest.fixture(name="set_up_transit_checking_for_cbf")
@pytest.mark.usefixtures("set_cbf_entry_point")
def fxt_set_up_transit_checking_for_cbf(
    transit_checking: fxt_types.transit_checking,
):
    """set up transit checking for cbf startup (if DEVENV enabled)

    :param transit_checking: fixture used by skallop
    """
    tel = names.TEL()
    # only do this for skamid as no inner devices used for low
    if tel.skamid:
        if os.getenv("DEVENV"):
            # only do transit checking in dev as timeout problems
            # can lead to false positives
            devices_to_follow = cast(List, [tel.csp.cbf.subarray(1)])
            subject_device = tel.csp.cbf.controller
            transit_checking.check_that(subject_device).transits_according_to(["ON"]).on_attr(
                "state"
            ).when_transit_occur_on(
                devices_to_follow,
                ignore_first=True,
                devices_to_follow_attr="state",
            )


@pytest.fixture(name="set_up_log_checking_for_cbf")
@pytest.mark.usefixtures("set_cbf_entry_point")
def fxt_set_up_log_capturing_for_cbf(log_checking: fxt_types.log_checking):
    """
    Set up log checking (using log consumer) on cbf.

    :param log_checking: skallop fixture used to set up log checking.
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        cbf_controller = str(tel.csp.cbf.controller)
        subarray = str(tel.csp.cbf.subarray(1))
        log_checking.capture_logs_from_devices(cbf_controller, subarray)


@given("an CBF")
def a_cbf(
    set_cbf_entry_point,  # pylint: disable=unused-argument
    set_up_transit_checking_for_cbf,  # pylint: disable=unused-argument
    set_up_log_checking_for_cbf,  # pylint: disable=unused-argument
):
    """
    a CBF.

    :param set_cbf_entry_point: Object to set cbf entry point
    :param set_up_transit_checking_for_cbf: Object to set up transit checking for cbf
    :param set_up_log_checking_for_cbf: Object to set up log checking for cbf
    """


# when
# use @when("I start up the telescope") from ..conftest


@then("the cbf must be on")
def the_cbf_must_be_on(transit_checking: fxt_types.transit_checking):
    """
    the cbf must be on.

    :param transit_checking: a fixture for transit checking
    """
    tel = names.TEL()
    cbf_controller = con_config.get_device_proxy(tel.csp.cbf.controller)
    result = cbf_controller.read_attribute("state").value
    assert_that(str(result)).is_equal_to("ON")
    # only check subarray 1 for cbf
    nr_of_subarrays = 1
    for index in range(1, nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.csp.cbf.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("ON")


# test validation


@pytest.mark.test_tests
@pytest.mark.usefixtures("setup_cbf_mock")
def test_test_cbf_startup(run_mock):
    """
    Test the test using a mock SUT

    :param run_mock: A mock device initialization
    """
    run_mock(test_cbf_start_up_telescope_mid)
