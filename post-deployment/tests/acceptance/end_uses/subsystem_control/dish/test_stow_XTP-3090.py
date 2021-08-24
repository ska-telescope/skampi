"""Test for XTP-3090"""
import logging
import pytest
import time

import tango

from pytest_bdd import scenario, given, when, then
from assertpy import assert_that

from resources.test_support.helpers import resource, watch


# values for stow position and elevation drive rate are
# from the dish behaviour in ska-tmc
STOW_POSITION = 85.0
ELEV_DRIVE_MAX_RATE = 1.0
DISH = "mid_d0001/elt/master"
LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope='module')
def az():
   return {'initial_az': 0}  # to be overwritten before stow request


@pytest.fixture(autouse=True, scope="module")
def restore_dish_state(request):
    """A teardown function which will ensure that the dish is restored to
    STANDBY state
    """

    def put_dish_in_standby_fp_mode():
        LOGGER.info(f"Restoring {DISH} to STANDBY state")
        dish_proxy = tango.DeviceProxy(DISH)
        dish_proxy.setstandbyfpmode()

    request.addfinalizer(put_dish_in_standby_fp_mode)


@pytest.mark.skamid
@scenario("XTP-3090.feature", "Test dish stow request")
def test_stow_command():
    pass


@given("dish reports any allowed dish mode")
def dish_reports_any_dish_mode():
    allowed_dish_modes = [
        "OFF",
        "STARTUP",
        "SHUTDOWN",
        "STANDBY_LP",
        "STANDBY_FP",
        "MAINTENANCE",
        "CONFIG",
        "OPERATE",
    ]

    current_dish_mode = resource(DISH).get("dishMode")
    assert_that(allowed_dish_modes).contains(current_dish_mode)
    LOGGER.info(f"{DISH} initial dishMode: {current_dish_mode}")


@when("I execute a stow command")
def set_stow_mode(az):
    az['initial_az'] = resource(DISH).get("achievedPointing")[1]
    dish_proxy = tango.DeviceProxy(DISH)
    LOGGER.info(f"{DISH} initial azimuth: {az['initial_az']}")
    LOGGER.info(
        f"{DISH} initial elevation: {resource(DISH).get('achievedPointing')[2]}"
    )
    dish_proxy.setstowmode()
    LOGGER.info(f"{DISH} requested dishMode: STOW")


@then("the dish mode should report STOW")
def check_dish_mode():
    LOGGER.info(f"Waiting for {DISH} dishMode to report STOW")
    watch_dish_mode = watch(resource(DISH)).for_a_change_on("dishMode")
    watch_dish_mode.wait_until_value_changed_to("STOW")
    assert_that(resource(DISH).get("dishMode")).is_equal_to("STOW")
    LOGGER.info(f"{DISH} current dishMode: {resource(DISH).get('dishMode')}")


@then("the elevation should be almost equal to the stow position")
def check_dish_elevation():
    current_el = resource(DISH).get("achievedPointing")[2]
    el_delta = abs(STOW_POSITION - current_el)
    expected_time_to_move = el_delta / ELEV_DRIVE_MAX_RATE
    stow_time_tolerance = 10 # arbitrary value but should be more than enough
    future = time.time() + expected_time_to_move + stow_time_tolerance
    dish_far_from_stow_position = True

    while dish_far_from_stow_position:
        now = time.time()
        current_el = resource(DISH).get("achievedPointing")[2]
        dish_far_from_stow_position = not (STOW_POSITION - current_el == pytest.approx(1, abs=1))
        time.sleep(1)  # sleep to avoid using full CPU resources while waiting to arrive on target
        if future < now:
            raise Exception("Timeout occurred")

    assert_that(resource(DISH).get("achievedPointing")[2]).is_close_to(STOW_POSITION, 1.0)
    LOGGER.info(f"{DISH} elevation: {resource(DISH).get('achievedPointing')[2]}")


@then("the azimuth should remain in the same position")
def check_dish_azimuth(az):
    assert_that(resource(DISH).get("achievedPointing")[1]).is_equal_to(az['initial_az'])
    LOGGER.info(f"{DISH} azimuth: {resource(DISH).get('achievedPointing')[1]}")
