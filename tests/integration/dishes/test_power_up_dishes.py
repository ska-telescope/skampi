"""Assign dishes to subarray feature tests."""
from enum import IntEnum
import logging
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.datatypes.attributes import DishMode

from resources.models.dish_model.entry_point import DishEntryPoint


from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)

# log capturing


@pytest.mark.skamid
@pytest.mark.startup
@scenario(
    "features/dishes_power_up.feature",
    "Make a set of dishes go to full power state",
)
def test_power_up_dishes():
    """Make a set of dishes go to full power state."""


@given("a set of available dishes", target_fixture="composition")
def an_dish_subarray(
    base_composition: conf_types.Composition,
    set_up_subarray_log_checking_for_dishes,  # type: ignore
    entry_point: DishEntryPoint,
) -> conf_types.Composition:
    """a set of available dishes"""
    # we set the dishes intending to be assigned as an attribute of the entrypoint
    return base_composition


# .. @when("I switch those dishes to fullpower") from conftest


@then("those dishes shall be in full power")
def those_dishes_shall_be_in_full_power(
    sut_settings: SutTestSettings, entry_point: DishEntryPoint
):
    """Then those dishes shall be in full power."""
    tel = names.TEL()
    assert tel.skamid, "incorrect telescope: Low instead of Mid"
    for dish_name in tel.skamid.dishes(entry_point.dishes_to_assign):
        dish = con_config.get_device_proxy(dish_name)
        result = dish.read_attribute("dishmode").value
        dish_mode: IntEnum = DishMode(result).name
        assert_that(dish_mode).is_equal_to("STANDBY_FP")
