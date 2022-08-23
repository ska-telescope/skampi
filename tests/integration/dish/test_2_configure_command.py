import logging
import time
from datetime import datetime, timedelta

import pytest
import tango
from integration.dish.dish_enums import DishMode
from integration.dish.utils import retrieve_attr_value
from pytest_bdd import given, scenario, then, when
from pytest_bdd.parsers import parse

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

@given(parse("dish_manager dishMode reports {dish_mode}"))
def check_dish_manager_dish_mode(dish_mode, dish_manager, modes_helper):
    # pylint: disable=missing-function-docstring
    modes_helper.ensure_dish_manager_mode(dish_mode)
    current_dish_mode = retrieve_attr_value(dish_manager, "dishMode")
    LOGGER.info(f"{dish_manager} dishMode: {current_dish_mode}")

@when("I issue Configure command on dish_leaf_node")
def configure_band_2(
    dish_manager,
    dish_manager_event_store,
):
    # pylint: disable=missing-function-docstring
    # subscribe to change event for dishMode
    dish_manager.subscribe_event(
        "dishMode",
        tango.EventType.CHANGE_EVENT,
        dish_manager_event_store,
    )
    dish_manager_event_store.clear_queue()

    # dish_leaf_node_proxy.Configure()
    future_time = datetime.utcnow() + timedelta(days=1)
    dish_manager.ConfigureBand2(future_time.isoformat())
    LOGGER.info("DishLeafNode requested to configureband2 on dish")

@then("dish_manager dishMode should report CONFIG briefly")
def check_dish_mode(dish_manager, dish_manager_event_store):
    # pylint: disable=missing-function-docstring
    # wait longer for dish manager to receive events for initial dish mode
    dish_mode_evts = dish_manager_event_store.get_queue_values(timeout=120)
    dish_mode_evts = [evt[1] for evt in dish_mode_evts]
    assert DishMode["CONFIG"] in dish_mode_evts
    LOGGER.info(f"{dish_manager} dishMode transitioned to CONFIG")

    # sundry check to be sure configure band
    # finished before checking sub devices
    assert DishMode["STANDBY_FP"] in dish_mode_evts

@then("dish_structure indexerPosition should report B2")
def check_dish_structure_indexer_position(dish_structure):
    # pylint: disable=missing-function-docstring
    # wait_for_change_on_resource(dish_manager_proxy, "dishMode", "OPERATE")
    indexer_positioner = retrieve_attr_value(
        dish_structure, "indexerPosition"
    )
    assert indexer_positioner == "B2"
    LOGGER.info(f"{dish_structure} indexerPosition: {indexer_positioner}")


@then("spf bandInFocus should report B2")
def check_spf_band_in_focus(spf):
    # pylint: disable=missing-function-docstring
    band_in_focus = retrieve_attr_value(
        spf, "bandInFocus"
    )
    assert band_in_focus == "B2"
    LOGGER.info(f"{spf} bandInFocus: {band_in_focus}")


@then("spfrx operatingMode should report DATA_CAPTURE")
def check_spfrx_operating_mode(spfrx):
    # pylint: disable=missing-function-docstring
    operating_mode = retrieve_attr_value(
        spfrx, "operatingMode"
    )
    assert operating_mode == "DATA_CAPTURE"
    LOGGER.info(f"{spfrx} operatingMode: {operating_mode}")


@then("spfrx configuredBand should report B2")
def check_spfrx_configured_band(spfrx):
    # pylint: disable=missing-function-docstring
    configured_band = retrieve_attr_value(
        spfrx, "configuredBand"
    )
    assert configured_band == "B2"
    LOGGER.info(f"{spfrx} configuredBand: {configured_band}")


@then("dish_manager configuredBand should report B2")
def check_dish_manager_configured_band(dish_manager):
    # pylint: disable=missing-function-docstring
    current_configured_band = retrieve_attr_value(
        dish_manager, "configuredBand"
    )
    assert current_configured_band == "B2"
    LOGGER.info(f"{dish_manager} dishMode: {current_configured_band}")


@then("dish_manager dishMode should report STANDBY_FP")
def check_dish_manager_dish_mode(dish_manager):
    # pylint: disable=missing-function-docstring
    current_dish_mode = retrieve_attr_value(dish_manager, "dishMode")
    assert current_dish_mode == "STANDBY_FP"
    LOGGER.info(f"{dish_manager} dishMode: {current_dish_mode}")
