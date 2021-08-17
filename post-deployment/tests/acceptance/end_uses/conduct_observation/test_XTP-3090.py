"""Test for XTP-3090"""
import logging
import pytest
import time

import tango

from pytest_bdd import scenario, given, when, then
from assertpy import assert_that

from resources.test_support.helpers import resource

STOW_POSITION = 85.0
INITIAL_AZ = 0  # to be overwritten before stow request
DISH_MASTER = "mid_d0001/elt/master"
LOGGER = logging.getLogger(__name__)



@scenario("XTP-3090.feature", "Test dish master simulator stow request")
def test_stow_command():
    pass


@given("a running telescope")
def telescope_is_running(running_telescope):
    pass


@when("I execute a stow command")
def set_stow_mode():
    dsh_proxy = tango.DeviceProxy(DISH_MASTER)
    INITIAL_AZ = resource(DISH_MASTER).get("achievedPointing")[1]
    LOGGER.info(f"{DISH_MASTER} initial azimuth: {INITIAL_AZ}")
    LOGGER.info(
        f"{DISH_MASTER} initial elevation: {resource(DISH_MASTER).get('achievedPointing')[2]}"
    )
    dsh_proxy.setstowmode()
    LOGGER.info(f"{DISH_MASTER} requested dishMode: STOW")


@then("the dish mode should report STOW")
def check_dish_mode():
    assert_that(resource(DISH_MASTER).get("dishMode")).is_equal_to("STOW")
    LOGGER.info(f"{DISH_MASTER} current dishMode: {resource(DISH_MASTER).get('dishMode')}")


@then("the elevation should be almost equal to the stow position")
def check_dish_master_elevation():
    future = time.time() + 5  # 5 seconds from now
    current_el = resource(DISH_MASTER).get("achievedPointing")[2]
    dish_far_from_target = not (STOW_POSITION - current_el == pytest.approx(1, abs=1))

    while dish_far_from_target:
        now = time.time()
        current_el = resource(DISH_MASTER).get("achievedPointing")[2]
        dish_far_from_target = not (STOW_POSITION - current_el == pytest.approx(1, abs=1))
        time.sleep(1)  # sleep to avoid using full CPU resources while we wait to get on target
        if future < now:
            raise Exception("Timeout occurred")

    assert_that(resource(DISH_MASTER).get("achievedPointing")[2]).is_close_to(STOW_POSITION, 1.0)
    LOGGER.info(f"{DISH_MASTER} elevation: {resource(DISH_MASTER).get('achievedPointing')[2]}")


@then("the azimuth should remain in the same position")
def check_dish_master_azimuth():
    assert_that(resource(DISH_MASTER).get("achievedPointing")[1]).is_equal_to(INITIAL_AZ)
    LOGGER.info(f"{DISH_MASTER} azimuth: {resource(DISH_MASTER).get('achievedPointing')[1]}")
