import logging
from datetime import datetime, timedelta

import pytest
import tango
from integration.dish.dish_enums import Band, DishMode
from integration.dish.utils import EventStore
from tango import DeviceProxy

LOGGER = logging.getLogger(__name__)


@pytest.fixture(name="dish_leaf_node", scope="module")
def dish_leaf_node_device_proxy():
    return DeviceProxy("ska_mid/tm_leaf_node/d0001")


@pytest.fixture(name="dish_manager", scope="module")
def dish_manager_device_proxy():
    return DeviceProxy("mid_d0001/elt/master")


@pytest.fixture(name="dish_structure", scope="module")
def dish_structure_device_proxy():
    return DeviceProxy("mid_d0001/lmc/ds_simulator")


@pytest.fixture(name="spf", scope="module")
def spf_device_proxy():
    return DeviceProxy("mid_d0001/spf/simulator")


@pytest.fixture(name="spfrx", scope="module")
def spfrx_device_proxy():
    return DeviceProxy("mid_d0001/spfrx/simulator")


@pytest.fixture
def modes_command_map():
    return {
        "STANDBY_LP": "SetStandbyLPMode",
        "STANDBY_FP": "SetStandbyFPMode",
        "OPERATE": "SetOperateMode",
        "STOW": "SetStowMode",
    }


@pytest.fixture
def event_store():
    """Fixture for storing events"""
    return EventStore()


@pytest.fixture(scope="module")
def dish_manager_event_store():
    """Fixture for storing dish_manager events"""
    return EventStore()


@pytest.fixture(scope="module")
def dish_structure_event_store():
    """Fixture for storing dish structure events"""
    return EventStore()


@pytest.fixture(scope="module")
def spfrx_event_store():
    """Fixture for storing spfrx events"""
    return EventStore()


@pytest.fixture(scope="module")
def spf_event_store():
    """Fixture for storing spf events"""
    return EventStore()


@pytest.fixture
def dish_freq_band_configuration(
    event_store,
    dish_manager,
):
    """
    A helper that manages dish lmc frequency band configuration
    """

    class _BandSelector:
        def go_to_band(self, band_number):
            if dish_manager.configuredBand.name == f"B{band_number}":
                LOGGER.info("Dish master is already at requested band")
                return

            allowed_modes = ["STANDBY_FP", "STOW", "OPERATE"]
            current_dish_mode = dish_manager.dishMode.name
            if not (current_dish_mode in allowed_modes):
                LOGGER.info(
                    f"Dish master cannot request ConfigureBand while in {current_dish_mode}"
                )
                return

            dish_manager.subscribe_event(
                "configuredBand",
                tango.EventType.CHANGE_EVENT,
                event_store,
            )
            event_store.clear_queue()

            future_time = datetime.utcnow() + timedelta(days=1)
            [[_], [_]] = dish_manager.command_inout(
                f"ConfigureBand{band_number}", future_time.isoformat()
            )

            try:
                # wait for events
                event_store.wait_for_value(Band(int(band_number)), timeout=60)
                LOGGER.info(
                    f"{dish_manager} successfully transitioned to Band {band_number}"
                )
            except RuntimeError:
                LOGGER.info(
                    f"Expected {dish_manager} to be in band {band_number}"
                    f" but currently reporting band {dish_manager.configuredBand.name}"
                )

    return _BandSelector()


@pytest.fixture
def modes_helper(
    event_store,
    dish_manager,
    modes_command_map,
):
    """
    A helper that manages device modes using events
    """

    class _ModesHelper:
        def ensure_dish_manager_mode(self, mode_name):
            """Move dish master to mode_name.
            Via STANDBY_FP, to ensure any mode can move to any mode.
            """
            if dish_manager.dishMode.name == mode_name:
                LOGGER.info("Dish master is already at requested mode")
                return

            # Move to standard mode STANDBY_FP if not there already
            # or skip going to STANDBY_FP if requested mode is STOW
            if (
                dish_manager.dishMode.name != "STANDBY_FP"
                and mode_name != "STOW"
            ):
                self.dish_manager_go_to_mode("STANDBY_FP")

            self.dish_manager_go_to_mode(mode_name)

        def dish_manager_go_to_mode(self, mode_name):
            """Move device to mode_name"""
            if dish_manager.dishMode.name == mode_name:
                LOGGER.info("Dish master is already at requested mode")
                return

            dish_manager.subscribe_event(
                "dishMode",
                tango.EventType.CHANGE_EVENT,
                event_store,
            )
            event_store.clear_queue()

            # Move to mode_name
            command_name = modes_command_map[mode_name]
            LOGGER.info(
                f"Moving {dish_manager} from "
                f"{dish_manager.dishMode.name} to {mode_name}"
            )

            LOGGER.info(f"{dish_manager} executing {command_name} ")
            [[_], [_]] = dish_manager.command_inout(command_name)

            try:
                # wait for events
                event_store.wait_for_value(DishMode[mode_name], timeout=60)
                LOGGER.info(
                    f"{dish_manager} successfully transitioned to {mode_name} mode"
                )
            except RuntimeError:
                LOGGER.info(
                    f"Expected {dish_manager} to be in {mode_name} dish mode"
                    f" but currently reporting {dish_manager.dishMode.name} dish mode"
                )

    return _ModesHelper()
