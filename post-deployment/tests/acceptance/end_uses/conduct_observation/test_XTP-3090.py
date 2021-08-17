"""Test for XTP-3090"""
import os
import logging
import time
import pytest

import tango 

from pytest_bdd import scenario, given, when, then
from assertpy import assert_that

from resources.test_support.helpers import resource

STOW_POSITION = 85.0
INITIAL_AZ = 0 # to be overwritten before stow request

logger = logging.getLogger(__name__)
dish_master = "mid_d0001/elt/master"

@scenario("XTP-3090.feature", "Test dish master simulator stow request")
def test_stow_command():
    pass


@given("a running telescope")
def telescope_is_runnnig(running_telescope):
    pass


@when("I execute a stow command")
def set_stow_mode():
    dp = tango.DeviceProxy(dish_master)
    INITIAL_AZ = resource(dish_master).get('achievedPointing')[1]
    logger.info(f"{dish_master} initial azimuth: {INITIAL_AZ}")
    logger.info(f"{dish_master} initial elevation: {resource(dish_master).get('achievedPointing')[2]}")
    dp.setstowmode()
    logger.info(f"{dish_master} requested dishMode: STOW")


@then("the dish mode should report STOW")
def check_dish_mode():
    assert_that(resource(dish_master).get("dishMode")).is_equal_to("STOW")
    logger.info(f"{dish_master} current dishMode: {resource(dish_master).get('dishMode')}")


@then("the elevation should be almost equal to the stow position")
def check_dish_master_elevation():
    assert_that(resource(dish_master).get("achievedPointing")[2]).is_close_to(STOW_POSITION, 0.5)
    logger.info(f"{dish_master} elevation: {resource(dish_master).get('achievedPointing')[2]}")


@then("the azimuth should remain in the same position")
def check_dish_master_azimuth():
    assert_that(resource(dish_master).get("achievedPointing")[1]).is_equal_to(INITIAL_AZ)
    logger.info(f"{dish_master} azimuth: {resource(dish_master).get('achievedPointing')[2]}")
