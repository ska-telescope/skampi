import logging

import pytest
from pytest_bdd import given, scenario, then
from ska_ser_skallop.connectors.configuration import get_device_proxy
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.startup
@scenario(
    "features/tmc_alarm_handler.feature",
    "Configure Alarm for IDLE Observation State",
)
def test_tmc_mid_alarm_for_subarray_idle():
    """Configure Alarm for IDLE Observation State in mid."""


@given("an telescope subarray", target_fixture="composition")
def a_telescope_subarray(
    base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """
    an telescope subarray.

    :param base_composition : An object for base composition
    :return: base composition
    """
    return base_composition


@given(
    "an Alarm handler configured to raise an alarm when the subarray obsState"
    " is IDLE"
)
def an_alarm_handler():
    """an Alarm Handler"""
    alarm_handler = get_device_proxy("alarm/handler/01")
    alarm_formula = (
        "tag=subarray_idle;formula=(ska_mid/tm_subarray_node/1/obsstate =="
        ' 2);priority=log;group=none;message=("alarm for subarray node idle")'
    )
    alarm_handler.command_inout("Load", alarm_formula)


@then("alarm must be raised with Unacknowledged state")
def validate_alarm_state():
    """Validate Alarm is raised for IDLE Observation state"""
    brd = get_message_board_builder()
    brd.set_waiting_on("alarm/handler/01").for_attribute(
        "alarmUnacknowledged"
    ).to_become_equal_to(("subarray_idle",))
