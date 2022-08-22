import logging
import time

from datetime import datetime, timedelta

import pytest
import tango
from integration.dish.utils import (
    retrieve_attr_value,
    wait_for_change_on_resource,
)
from pytest_bdd import scenario, then, when
from pytest_bdd.parsers import parse
from tango import CmdArgType, DeviceProxy


LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="module", name="event_subs")
def fixture_event_subs():
    # pylint: disable=missing-function-docstring
    return {"evt_id": None, "cb": None}


@pytest.mark.skamid
@scenario(
    "dish_leaf_node_configure.feature", "Test dishleafnode Configure command"
)
def test_configure():
    # pylint: disable=missing-function-docstring
    pass


@when(parse("I issue Configure command on dish_leaf_node"))
def configure(
    dish_leaf_node_device_name,
    dish_manager_device_name,
    devices_under_test,
    event_subs,
):
    # pylint: disable=missing-function-docstring
    dish_leaf_node_proxy = devices_under_test[dish_leaf_node_device_name]
    dish_manager_proxy = devices_under_test[dish_manager_device_name]
    # subscribe to change event for dishMode
    dish_mode_cb = tango.utils.EventCallback()
    evt_id = dish_manager_proxy.subscribe_event(
        "dishMode", tango.EventType.CHANGE_EVENT, dish_mode_cb, []
    )
    event_subs["cb"] = dish_mode_cb
    event_subs["evt_id"] = evt_id
    # dish_leaf_node_proxy.Configure()
    future_time = datetime.utcnow() + timedelta(days=1)
    dish_manager_proxy.ConfigureBand2(future_time.isoformat())
    LOGGER.info("DishLeafNode requested to configureband2 on dish")


@then("dish_manager dishMode should report CONFIG briefly")
def check_dish_mode(dish_manager_device_name, devices_under_test, event_subs):
    # pylint: disable=missing-function-docstring
    time.sleep(2)
    dish_manager_proxy = devices_under_test[dish_manager_device_name]
    # CONFIG is a transient mode change. Detect this transition
    # by inspecting the events received for CONFIG:7
    cb = event_subs["cb"]
    dish_mode_evts = [
        evt_data.attr_value.value for evt_data in cb.get_events()
    ]
    LOGGER.info(dish_mode_evts)
    LOGGER.info(dish_manager_proxy.configuredBand)
    # dish_manager_proxy.unsubscribe_event(event_subs["evt_id"])
    CONFIG = 6
    assert CONFIG in dish_mode_evts
    LOGGER.info(f"{dish_manager_proxy} dishMode transitioned to CONFIG")

@then("dish_structure indexerPosition should report B2")
def check_dish_structure_indexer_position(dish_structure_device_name, devices_under_test):
    # pylint: disable=missing-function-docstring
    time.sleep(2)
    dish_structure_proxy = devices_under_test[dish_structure_device_name]
    # wait_for_change_on_resource(dish_manager_proxy, "dishMode", "OPERATE")
    indexer_positioner = retrieve_attr_value(
        dish_structure_proxy, "indexerPosition"
    )
    assert indexer_positioner == "B2"
    LOGGER.info(f"{dish_structure_proxy} indexerPosition: {indexer_positioner}")


@then("spf bandInFocus should report B2")
def check_spf_band_in_focus(spf_device_name, devices_under_test):
    # pylint: disable=missing-function-docstring
    time.sleep(2)
    spf_proxy = devices_under_test[spf_device_name]
    # wait_for_change_on_resource(dish_manager_proxy, "dishMode", "OPERATE")
    band_in_focus = retrieve_attr_value(
        spf_proxy, "bandInFocus"
    )
    assert band_in_focus == "B2"
    LOGGER.info(f"{spf_proxy} bandInFocus: {band_in_focus}")


@then("spfrx operatingMode should report DATA_CAPTURE")
def check_spfrx_operating_mode(spfrx_device_name, devices_under_test):
    # pylint: disable=missing-function-docstring
    time.sleep(2)
    spfrx_proxy = devices_under_test[spfrx_device_name]
    # wait_for_change_on_resource(dish_manager_proxy, "dishMode", "OPERATE")
    operating_mode = retrieve_attr_value(
        spfrx_proxy, "operatingMode"
    )
    assert operating_mode == "DATA_CAPTURE"
    LOGGER.info(f"{spfrx_proxy} operatingMode: {operating_mode}")


@then("spfrx configuredBand should report B2")
def check_spfrx_configured_band(spfrx_device_name, devices_under_test):
    # pylint: disable=missing-function-docstring
    time.sleep(2)
    spfrx_proxy = devices_under_test[spfrx_device_name]
    # wait_for_change_on_resource(dish_manager_proxy, "dishMode", "OPERATE")
    configured_band = retrieve_attr_value(
        spfrx_proxy, "configuredBand"
    )
    assert configured_band == "B2"
    LOGGER.info(f"{spfrx_proxy} configuredBand: {configured_band}")


@then("dish_manager configuredBand should report B2")
def check_dish_manager_configured_band(dish_manager_device_name, devices_under_test):
    # pylint: disable=missing-function-docstring
    time.sleep(2)
    dish_manager_proxy = devices_under_test[dish_manager_device_name]
    # wait_for_change_on_resource(dish_manager_proxy, "dishMode", "OPERATE")
    current_configured_band = retrieve_attr_value(
        dish_manager_proxy, "configuredBand"
    )
    assert current_configured_band == "B2"
    LOGGER.info(f"{dish_manager_proxy} dishMode: {current_configured_band}")


@then("dish_manager dishMode should report STANDBY_FP")
def check_dish_manager_dish_mode(dish_manager_device_name, devices_under_test):
    # pylint: disable=missing-function-docstring
    dish_manager_proxy = devices_under_test[dish_manager_device_name]
    # wait_for_change_on_resource(dish_manager_proxy, "dishMode", "OPERATE")
    current_dish_mode = retrieve_attr_value(dish_manager_proxy, "dishMode")
    assert current_dish_mode == "STANDBY_FP"
    LOGGER.info(f"{dish_manager_proxy} dishMode: {current_dish_mode}")
