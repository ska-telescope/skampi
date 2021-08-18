"""Test for XTP-3090"""
import logging
import pytest
import time

import tango

from pytest_bdd import scenario, given, when, then
from assertpy import assert_that

from resources.test_support.helpers import resource, watch

STOW_POSITION = 85.0
DISH_MASTER = "mid_d0001/elt/master"
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
        LOGGER.info(f"Restoring {DISH_MASTER} to STANDBY state")
        dsh_proxy = tango.DeviceProxy(DISH_MASTER)
        dsh_proxy.setstandbyfpmode()

    request.addfinalizer(put_dish_in_standby_fp_mode)


@scenario("XTP-3090.feature", "Test dish master simulator stow request")
def test_stow_command():
    pass


@given("dish master reports any allowed dish mode")
def dish_master_reports_any_dish_mode():
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

    current_dish_mode = resource(DISH_MASTER).get("dishMode")
    assert_that(allowed_dish_modes).contains(current_dish_mode)
    LOGGER.info(f"{DISH_MASTER} initial dishMode: {current_dish_mode}")


@when("I execute a stow command")
def set_stow_mode(az):
    az['initial_az'] = resource(DISH_MASTER).get("achievedPointing")[1]
    dsh_proxy = tango.DeviceProxy(DISH_MASTER)
    LOGGER.info(f"{DISH_MASTER} initial azimuth: {az['initial_az']}")
    LOGGER.info(
        f"{DISH_MASTER} initial elevation: {resource(DISH_MASTER).get('achievedPointing')[2]}"
    )
    dsh_proxy.setstowmode()
    LOGGER.info(f"{DISH_MASTER} requested dishMode: STOW")


@then("the dish mode should report STOW")
def check_dish_mode():
    LOGGER.info(f"Waiting for {DISH_MASTER} dishMode to report STOW")
    watch_dish_mode = watch(resource(DISH_MASTER)).for_a_change_on("dishMode")
    watch_dish_mode.wait_until_value_changed_to("STOW")
    assert_that(resource(DISH_MASTER).get("dishMode")).is_equal_to("STOW")
    LOGGER.info(f"{DISH_MASTER} current dishMode: {resource(DISH_MASTER).get('dishMode')}")


@then("the elevation should be almost equal to the stow position")
def check_dish_master_elevation():
    future = time.time() + 5  # 5 seconds from now
    current_el = resource(DISH_MASTER).get("achievedPointing")[2]
    dish_far_from_stow_position = not (STOW_POSITION - current_el == pytest.approx(1, abs=1))

    while dish_far_from_stow_position:
        now = time.time()
        current_el = resource(DISH_MASTER).get("achievedPointing")[2]
        dish_far_from_stow_position = not (STOW_POSITION - current_el == pytest.approx(1, abs=1))
        time.sleep(1)  # sleep to avoid using full CPU resources while we wait to get on target
        if future < now:
            raise Exception("Timeout occurred")

    assert_that(resource(DISH_MASTER).get("achievedPointing")[2]).is_close_to(STOW_POSITION, 1.0)
    LOGGER.info(f"{DISH_MASTER} elevation: {resource(DISH_MASTER).get('achievedPointing')[2]}")


@then("the azimuth should remain in the same position")
def check_dish_master_azimuth(az):
    assert_that(resource(DISH_MASTER).get("achievedPointing")[1]).is_equal_to(az['initial_az'])
    LOGGER.info(f"{DISH_MASTER} azimuth: {resource(DISH_MASTER).get('achievedPointing')[1]}")
