"""Configure Bandwith and point dishes."""
import pytest
from pytest_bdd import given, scenario, then

from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
from resources.models.dish_model.entry_point import DishEntryPoint
from ska_ser_skallop.datatypes.attributes import DishMasterPointingState


@pytest.mark.skamid
@pytest.mark.assign
@scenario(
    "features/dishes_configure.feature",
    "Configure Dishes for a subarrray scan",
)
def test_configure_dishes_for_a_subarray_scan():
    """Configure Dishes for a subarrray scan."""


@given("an set of dish masters currently assigned to a subarray in IDLE state")
def an_set_of_dish_masters_currently_assigned_to_a_subarray_in_idle_state():
    """an set of dish masters currently assigned to a subarray in IDLE state."""


@given(
    "a scan configuration with a particular target position and desired freq band",
    target_fixture="configuration",
)
def a_scan_configuration(
    set_up_subarray_log_checking_for_dishes,  # type: ignore
    dish_base_configuration: conf_types.ScanConfiguration,
) -> conf_types.ScanConfiguration:
    """a scan configuration with a particular target position and desired freq band."""
    # will use default composition for the allocated subarray
    # subarray_allocation_spec.composition
    return dish_base_configuration


# use when from global conftest
# @when("I configure it for a scan")


@then(
    "the dishes shall be in a reported state actively tracking the desired source position at the "
    "desired frequency"
)
def those_dishes_shall_be_in_full_power(entry_point: DishEntryPoint):
    """Then those dishes shall be in full power."""
    tel = names.TEL()
    assert tel.skamid, "Incorrect Telescope: Low, this test is Mid only"
    for dish_name in tel.skamid.dishes(entry_point.dishes_to_assign):
        dish = con_config.get_device_proxy(dish_name)
        result = dish.read_attribute("pointingstate").value
        pointingstate = DishMasterPointingState(result).name
        expected = ["READY", "TRACK"]
        assert pointingstate in [
            "READY",
            "TRACK",
        ], f"Got {pointingstate} but expected {expected}"
