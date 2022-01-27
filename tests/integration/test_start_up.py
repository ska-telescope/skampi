"""Start up the sdp feature tests."""
import logging
import re
from typing import List, cast
import os

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.subscribing.message_board import MessageBoard

from . import conftest

logger = logging.getLogger(__name__)

# global settings


@pytest.fixture(name="start_up_test_exec_settings")
def fxt_start_up_test_exec_settings(
    exec_settings: fxt_types.exec_settings,
) -> fxt_types.exec_settings:
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


@pytest.mark.skamid
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
@pytest.mark.skip(reason="current mccs-low version is deprecated")
@scenario("features/mccs_start_up_telescope.feature", "Start up the MCCS")
def test_mccs_start_up_telescope():
    """Start up the csp in low."""


# transit checking


@pytest.fixture(name="set_up_transit_checking_for_cbf")
@pytest.mark.usefixtures("set_cbf_entry_point")
def fxt_set_up_transit_checking_for_cbf(transit_checking: fxt_types.transit_checking):
    tel = names.TEL()
    # only do this for skamid as no inner devices used for low
    if tel.skamid:
        if os.getenv("DEVENV"):
            # only do transit checking in dev as timeout problems can lead to false positives
            devices_to_follow = cast(List, [tel.csp.cbf.subarray(1)])
            subject_device = tel.csp.cbf.controller
            transit_checking.check_that(subject_device).transits_according_to(
                ["ON"]
            ).on_attr("state").when_transit_occur_on(
                devices_to_follow, ignore_first=True, devices_to_follow_attr="state"
            )


@pytest.fixture(name="set_up_transit_checking_for_csp")
@pytest.mark.usefixtures("set_csp_entry_point")
@pytest.mark.usefixtures("exec_env")
def fxt_set_up_transit_checking_for_csp(
    exec_env, transit_checking: fxt_types.transit_checking
):
    tel = names.TEL()
    if tel.skalow:
        # if os.getenv("DEVENV"):
        # only do transit checking in dev as timeout problems can lead to false positives
        devices_to_follow = cast(
            List,
            [
                tel.csp.subarray(1),
                tel.csp.cbf.subarray(1),
                tel.csp.subarray(2),
                tel.csp.cbf.subarray(2),
                tel.csp.cbf.controller,
            ],
        )
        subject_device = tel.csp.controller
        transit_checking.check_that(subject_device).transits_according_to(
            ["ON"]
        ).on_attr("state").when_transit_occur_on(
            devices_to_follow, ignore_first=True, devices_to_follow_attr="state"
        )


# log capturing


@pytest.fixture(name="set_up_log_checking_for_cbf")
@pytest.mark.usefixtures("set_cbf_entry_point")
def fxt_set_up_log_capturing_for_cbf(log_checking: fxt_types.log_checking):
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        cbf_controller = str(tel.csp.cbf.controller)
        subarray = str(tel.csp.cbf.subarray(1))
        log_checking.capture_logs_from_devices(cbf_controller, subarray)


@pytest.fixture(name="set_up_log_checking_for_csp")
@pytest.mark.usefixtures("set_cbf_entry_point")
def fxt_set_up_log_checking_for_cspf(log_checking: fxt_types.log_checking):
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        cbf_controller = str(tel.csp.controller)
        subarray = str(tel.csp.subarray(1))
        log_checking.capture_logs_from_devices(cbf_controller, subarray)


@given("an SDP")
def a_sdp(set_sdp_entry_point):
    """a SDP."""


@given("an CSP")
def a_csp(
    set_csp_entry_point, set_up_transit_checking_for_csp, set_up_log_checking_for_csp
):
    """a CSP."""


@given("an CBF")
def a_cbf(
    set_cbf_entry_point, set_up_transit_checking_for_cbf, set_up_log_checking_for_cbf
):
    """a CBF."""


@given("the MCCS")
def a_mccs(set_mccs_entry_point):
    """a MCCS."""


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
    for index in range(1, conftest.NR_OFF_SUBARRAYS + 1):
        subarray = con_config.get_device_proxy(tel.sdp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(result).is_equal_to("ON")


@then("the csp must be on")
def the_csp_must_be_on(transit_checking: fxt_types.transit_checking):
    """the csp must be on."""
    tel = names.TEL()
    csp_master = con_config.get_device_proxy(tel.csp.controller)
    result = csp_master.read_attribute("state").value
    assert_that(result).is_equal_to("ON")
    for index in range(1, conftest.NR_OFF_SUBARRAYS + 1):
        subarray = con_config.get_device_proxy(tel.csp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(result).is_equal_to("ON")
    if transit_checking:
        checker = transit_checking.checker
        assert checker
        logger.info(checker.print_outcome_for(checker.subject_device))
        checker.assert_that(checker.subject_device).is_behind_all_on_transit("ON")


@then("the cbf must be on")
def the_cbf_must_be_on(transit_checking: fxt_types.transit_checking):
    """the cbf must be on."""
    tel = names.TEL()
    cbf_controller = con_config.get_device_proxy(tel.csp.cbf.controller)
    result = cbf_controller.read_attribute("state").value
    assert_that(result).is_equal_to("ON")
    # only check subarray 1 for cbf
    nr_of_subarrays = 1
    for index in range(1, nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.csp.cbf.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(result).is_equal_to("ON")
    if transit_checking:
        checker = transit_checking.checker
        assert checker
        logger.info(checker.print_outcome_for(checker.subject_device))
        checker.assert_that(checker.subject_device).is_behind_all_on_transit("ON")


@then("the MCCS must be on")
def the_mccs_must_be_on():
    """the MCCS must be on."""
    tel = names.TEL()
    assert tel.skalow
    mccs_controller = con_config.get_device_proxy(tel.skalow.mccs.master)
    result = mccs_controller.read_attribute("state").value
    assert_that(result).is_equal_to("ON")
    # only check subarray 1 for cbf low


# test validation


@pytest.mark.test_tests
@pytest.mark.usefixtures("setup_sdp_mock")
def test_test_sdp_startup(run_mock):
    """Test the test using a mock SUT"""
    run_mock(test_sdp_start_up_telescope_mid)


@pytest.mark.test_tests
@pytest.mark.usefixtures("setup_csp_mock")
def test_test_csp_startup(run_mock):
    """Test the test using a mock SUT"""
    run_mock(test_csp_start_up_telescope_mid)


# @pytest.mark.skip(reason="mocking model does not have low-cbf/control/0")
@pytest.mark.test_tests
@pytest.mark.usefixtures("setup_cbf_mock")
def test_test_cbf_startup(run_mock):
    """Test the test using a mock SUT"""
    run_mock(test_cbf_start_up_telescope_mid)
