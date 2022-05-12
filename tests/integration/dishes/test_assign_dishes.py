"""Assign dishes to subarray feature tests."""
import logging
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types


from resources.models.mvp_model.states import ObsState

from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)

# log capturing


@pytest.mark.skamid
@pytest.mark.assign
@scenario(
    "features/dishes_assign_resources.feature",
    "Make a set of dishes in full power state when assigned to a subarray",
)
def test_assign_dishes_to_subarray_in_mid():
    """Make a set of dishes in full power state when assigned to a subarray."""


@given("a set of available dishes", target_fixture="dish_ids")
def an_sdp_subarray(
    base_composition: list[int], set_up_subarray_log_checking_for_dishes
) -> conf_types.Composition:
    """a set of available dishes"""
    return base_composition


# .. @when("I assign those dishes to a subarray") from conftest


@then("those dishes shall be in full power")
def those_dishes_shall_be_in_full_power(
    sut_settings: SutTestSettings, dish_ids: list[int]
):
    """Then those dishes shall be in full power."""
    tel = names.TEL()
    for dish_name in tel.skamid.dishes(dish_ids):
        dish = con_config.get_device_proxy(dish_name)
        result = dish.read_attribute("dishmode").value
        assert_that(str(result)).is_equal_to("STANDBY-FP")
