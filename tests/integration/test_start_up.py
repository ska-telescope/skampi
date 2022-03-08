"""Start up the sdp feature tests."""
import logging
import os

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from . import conftest

logger = logging.getLogger(__name__)

# global settings


@pytest.fixture(name="start_up_test_exec_settings")
def fxt_start_up_test_exec_settings(
    exec_settings: fxt_types.exec_settings,
) -> fxt_types.exec_settings:
    """General test execution settings for start up.

    :param exec_settings: Fixture as used by skallop
    :return: updated fixture
    """
    start_up_test_exec_settings = exec_settings.replica()
    start_up_test_exec_settings.time_out = 30
    if os.getenv("LIVE_LOGGING"):
        start_up_test_exec_settings.run_with_live_logging()
    if os.getenv("REPLAY_EVENTS_AFTERWARDS"):
        start_up_test_exec_settings.replay_events_afterwards()
    return start_up_test_exec_settings


# tests marking


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


@given("an SDP")
def a_sdp(set_sdp_entry_point):  # pylint: disable=unused-argument
    """a SDP."""


# whens


@when("I start up the telescope")
def i_start_up_the_telescope(
    standby_telescope: fxt_types.standby_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    start_up_test_exec_settings: fxt_types.exec_settings,
):
    """I start up the telescope."""
    with context_monitoring.context_monitoring():
        with standby_telescope.wait_for_starting_up(start_up_test_exec_settings):
            entry_point.set_telescope_to_running()


# thens


@then("the sdp must be on")
def the_sdp_must_be_on():
    """the sdp must be on."""
    tel = names.TEL()
    sdp_master = con_config.get_device_proxy(tel.sdp.master)
    result = sdp_master.read_attribute("state").value
    assert_that(result).is_equal_to("ON")
    for index in range(1, conftest.NR_OF_SUBARRAYS + 1):
        subarray = con_config.get_device_proxy(tel.sdp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(result).is_equal_to("ON")


# test validation


@pytest.mark.test_tests
@pytest.mark.usefixtures("setup_sdp_mock")
def test_test_sdp_startup(run_mock):
    """Test the test using a mock SUT"""
    run_mock(test_sdp_start_up_telescope_mid)
