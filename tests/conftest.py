import logging
import time

import pytest
import tango
from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse
from ska_tango_base.testing.mock import MockChangeEventCallback
from tango import CmdArgType, DeviceProxy

LOGGER = logging.getLogger(__name__)


def retrieve_attr_value(dev_proxy, attr_name):
    """Get the attribute reading from device"""
    current_val = dev_proxy.read_attribute(attr_name)
    if current_val.type == CmdArgType.DevEnum:
        current_val = getattr(dev_proxy, attr_name).name
    elif current_val.type == CmdArgType.DevState:
        current_val = str(current_val.value)
    else:
        current_val = current_val.value
    return current_val


@pytest.fixture(scope="module")
def dish_leaf_node_device_name():
    return "ska_mid/tm_leaf_node/d0001"


@pytest.fixture(scope="module")
def dish_manager_device_name():
    return "mid_d0001/elt/master"


@pytest.fixture(scope="module")
def dish_structure_device_name():
    return "mid_d0001/lmc/ds_simulator"


@pytest.fixture(scope="module")
def spf_device_name():
    return "mid_d0001/spf/simulator"


@pytest.fixture(scope="module")
def spfrx_device_name():
    return "mid_d0001/spfrx/simulator"


@pytest.fixture(scope="module")
def devices_under_test():
    device_proxies = {}
    return device_proxies


def wait_for_change_on_resource(
    dev_proxy, attr_name, expected_val, timeout=120
):
    """Wait a while for a change in an attribute value"""
    checkpoint = timeout / 4
    start_time = time.time()
    time_elapsed = 0

    while time_elapsed <= timeout:
        current_val = retrieve_attr_value(dev_proxy, attr_name)
        # for progress attributes check for presence (in)
        if current_val == expected_val or expected_val in current_val:
            break

        if (time_elapsed % checkpoint) == 0:
            print(f"Waiting for {attr_name} to transition to {expected_val}")
            time.sleep(0.8 * checkpoint)
        time_elapsed = int(time.time() - start_time)


@pytest.fixture(scope="module")
def change_event_callbacks():
    """
    Return a dictionary of Tango device change event callbacks
    with asynchrony support.

    :return: a collections.defaultdict that returns change event
        callbacks by name.
    """

    class _ChangeEventDict:
        def __init__(self):
            self._dict = {}

        def __getitem__(self, key):
            if key not in self._dict:
                self._dict[key] = MockChangeEventCallback(
                    key, called_timeout=180.0
                )
            return self._dict[key]

    return _ChangeEventDict()


@pytest.fixture(scope="module")
def multi_tango_change_event_helper(
    devices_under_test, change_event_callbacks
):
    """
    Return a helper to simplify subscription to the multiple
    devices under test with a callback.

    :param devices_under_test: The devices under test
    :param change_event_callbacks: dictionary of callbacks with
        asynchrony support, specifically for receiving Tango device
        change events.
    """

    class _TangoChangeEventHelper:
        def subscribe(self, device_name, attribute_name):
            device_under_test = devices_under_test[device_name]
            device_under_test.subscribe_event(
                attribute_name,
                tango.EventType.CHANGE_EVENT,
                change_event_callbacks[attribute_name],
            )
            return change_event_callbacks[attribute_name]

    return _TangoChangeEventHelper()


@pytest.fixture(scope="module")
def modes_command_map():
    return {
        "STANDBY_LP": "SetStandbyLPMode",
        "STANDBY_FP": "SetStandbyFPMode",
        "OPERATE": "SetOperateMode",
        "STOW": "SetStowMode",
    }


@pytest.fixture(scope="module")
def command_progress_map():
    return {
        "SetStandbyLPMode": "setStandbyLPModeProgress",
        "SetStandbyFPMode": "setStandbyFPModeProgress",
        "SetOperateMode": "setOperateModeProgress",
        "SetStowMode": "setstowmodeprogress",
    }


@pytest.fixture(scope="module")
def modes_helper(
    multi_tango_change_event_helper,
    devices_under_test,
    modes_command_map,
    command_progress_map,
):
    """
    A helper that manages device modes using events

    :param multi_tango_change_event_helper: Event subscription helper
    :type multi_tango_change_event_helper: _TangoChangeEventHelper
    """

    class _ModesHelper:
        def ensure_dish_master_mode(self, device_name, mode_name):
            """Move dish master to mode_name.
            Via STANDBY_FP, to ensure any mode can move to any mode.
            """
            dish_master_proxy = devices_under_test[device_name]
            if dish_master_proxy.dishMode.name == mode_name:
                LOGGER.info("Dish master is already at requested mode")
                return

            if dish_master_proxy.dishMode.name == "CONFIG":
                LOGGER.info("Dish master is in CONFIG")
                return

            # Move to standard mode STANDBY_FP if not there already
            # or skip going to STANDBY_FP is requested mode is STOW
            if (
                dish_master_proxy.dishMode.name != "STANDBY_FP"
                and mode_name != "STOW"
            ):
                self.dish_master_go_to_mode(device_name, "STANDBY_FP")

            self.dish_master_go_to_mode(device_name, mode_name)

        def dish_master_go_to_mode(self, device_name, mode_name):
            """Move device to mode_name"""
            dish_master_proxy = devices_under_test[device_name]
            if dish_master_proxy.dishMode.name == mode_name:
                LOGGER.info("Dish master is already at requested mode")
                return

            change_event_helper = multi_tango_change_event_helper.subscribe(
                device_name, "dishMode"
            )
            initial_dish_mode = ev = dish_master_proxy.dishMode.value

            # Move to mode_name
            command_name = modes_command_map[mode_name]
            # progress_attribute = command_progress_map[command_name]
            # progress_value = getattr(dish_master_proxy, progress_attribute)[0]

            LOGGER.info(
                f"Moving {dish_master_proxy} from "
                f"{dish_master_proxy.dishMode.name} to {mode_name}"
            )

            # Check if a command is in progress
            # if progress_value == "RUNNING":
            #     LOGGER.info(
            #         f"{dish_master_proxy} command {command_name} is in progress"
            #         f" as per {progress_attribute} with value {progress_value}"
            #     )
            # else:
            # SetOperateMode requires that there is a configured band
            # Request to go to band1 if there is no selected band
            unwanted_band_values = ["UNKNOWN", "NONE", "ERROR", "UNDEFINED"]
            if (
                dish_master_proxy.configuredBand.name in unwanted_band_values
                and mode_name == "OPERATE"
            ):
                LOGGER.info(
                    f"{dish_master_proxy} has no band configured. Requesting to go to band 1 before {command_name} "
                )
                dish_master_proxy.command_inout("ConfigureBand1", " ")
                wait_for_change_on_resource(
                    dish_master_proxy, "configuredBand", "B1"
                )
            LOGGER.info(f"{dish_master_proxy} executing {command_name} ")
            dish_master_proxy.command_inout(command_name)

            # so long as the events capture the previous dish mode, keep
            # checking for the next events. Do this for about 5 mins
            future = time.time() + 300
            # just in case band selection request didn't finish
            # properly before executing mode transition, prevent
            # CONFIG change event from breaking loop
            NONE = 7
            tries = 1
            while ev == initial_dish_mode or ev == NONE:
                now = time.time()
                time.sleep(0.5)
                try:
                    # continue waiting for events
                    ev = change_event_helper.get_next_change_event()
                    LOGGER.info(f"Got change event on dishMode: {ev}")
                except AssertionError:
                    LOGGER.info("Change event callback has not been called")
                    # sometimes weird things happen: events stop coming through and
                    # the requested command doesn't finish properly. resolve this temporarily
                    # by requesting the command again to get the event system going
                    # progress_value = getattr(dish_master_proxy, progress_attribute)[0]
                    # if progress_value == "COMPLETED" and tries == 1:
                    #     LOGGER.info(f"{dish_master_proxy} executing {command_name} again")
                    #     dish_master_proxy.command_inout(command_name)
                    #     future = time.time() + 300
                    #     tries += 1
                if future < now:
                    break
            wait_for_change_on_resource(
                dish_master_proxy, "dishMode", mode_name
            )
            assert (
                dish_master_proxy.dishMode.name == mode_name
            ), f"Expected {dish_master_proxy} to be in {mode_name} mode"

    return _ModesHelper()


# BACKGROUND
@given("dish_leaf_node, dish_manager, dish_structure, spf, spfrx devices")
def create_device_proxies(
    dish_leaf_node_device_name,
    dish_manager_device_name,
    dish_structure_device_name,
    spf_device_name,
    spfrx_device_name,
    devices_under_test,
):
    if dish_leaf_node_device_name not in devices_under_test:
        devices_under_test[dish_leaf_node_device_name] = DeviceProxy(
            dish_leaf_node_device_name
        )

    if dish_manager_device_name not in devices_under_test:
        devices_under_test[dish_manager_device_name] = DeviceProxy(
            dish_manager_device_name
        )

    if dish_structure_device_name not in devices_under_test:
        devices_under_test[dish_structure_device_name] = DeviceProxy(
            dish_structure_device_name
        )

    if spf_device_name not in devices_under_test:
        devices_under_test[spf_device_name] = DeviceProxy(spf_device_name)

    if spfrx_device_name not in devices_under_test:
        devices_under_test[spfrx_device_name] = DeviceProxy(spfrx_device_name)


# GIVENS
@given(parse("spfrx b{band_number}CapabilityState reports {expected_state}"))
def given_check_spfrx_capability_state(check_spfrx_capability_state):
    pass


@given(parse("spf b{band_number}CapabilityState reports {expected_state}"))
def given_check_spf_capability_state(check_spf_capability_state):
    pass


@given(parse("dish_manager dishMode reports {dish_mode}"))
def check_dish_manager_dish_mode(
    dish_mode, dish_manager_device_name, devices_under_test, modes_helper
):
    # pylint: disable=missing-function-docstring
    dish_master_proxy = devices_under_test[dish_manager_device_name]
    modes_helper.ensure_dish_master_mode(dish_manager_device_name, dish_mode)
    current_dish_mode = retrieve_attr_value(dish_master_proxy, "dishMode")
    LOGGER.info(f"{dish_master_proxy} dishMode: {current_dish_mode}")


@given(parse("dish_structure operatingMode reports {operating_mode}"))
def check_dish_structure_operating_mode(
    operating_mode, dish_structure_device_name, devices_under_test
):
    # pylint: disable=missing-function-docstring
    dish_structure_proxy = devices_under_test[dish_structure_device_name]
    current_operating_mode = retrieve_attr_value(
        dish_structure_proxy, "operatingMode"
    )
    assert current_operating_mode == operating_mode
    LOGGER.info(
        f"{dish_structure_proxy} operatingMode: {current_operating_mode}"
    )
