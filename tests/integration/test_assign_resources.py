"""Assign resources to subarray feature tests."""
import logging
from types import SimpleNamespace
from typing import cast
import os

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.logging import device_logging_context
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.event_waiting.wait import EWhilstWaiting, wait_for
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.subscribing.base import MessageBoardBase

logger = logging.getLogger(__name__)

RECEPTORS = [1, 2]
SUB_ARRAY_ID = 1


@pytest.fixture(name="assign_resources_test_exec_settings")
def fxt_start_up_test_exec_settings(
    exec_settings: fxt_types.exec_settings,
) -> fxt_types.exec_settings:
    start_up_test_exec_settings = exec_settings.replica()
    start_up_test_exec_settings.time_out = 30
    if os.getenv("LIVE_LOGGING"):
        start_up_test_exec_settings.run_with_live_logging()
    if os.getenv("REPLAY_EVENTS_AFTERWARDS"):
        start_up_test_exec_settings.replay_events_afterwards()
    return start_up_test_exec_settings


# resource configurations


@pytest.fixture(name="sdp_base_composition")
def fxt_sdp_base_composition(tmp_path) -> conf_types.Composition:
    composition = conf_types.CompositionByFile(
        tmp_path, conf_types.CompositionType.STANDARD
    )
    return composition


# log capturing


@pytest.fixture(name="set_up_log_checking_for_sdp")
@pytest.mark.usefixtures("set_cbf_entry_point")
def fxt_set_up_log_capturing_for_cbf(log_checking: fxt_types.log_checking):
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        sdp_subarray = str(tel.sdp.subarray(SUB_ARRAY_ID))
        log_checking.capture_logs_from_devices(sdp_subarray)


@pytest.mark.skalow
@scenario(
    "features/sdp_assign_resources.feature", "Assign resources to sdp subarray in low"
)
def test_assign_resources_to_sdp_subarray_in_low():
    """Assign resources to sdp subarray in low."""


@pytest.mark.skamid
@scenario(
    "features/sdp_assign_resources.feature", "Assign resources to sdp subarray in mid"
)
def test_assign_resources_to_sdp_subarray_in_mid():
    """Assign resources to sdp subarray in mid."""


@given("an SDP subarray", target_fixture="composition")
def an_sdp_subarray(
    set_sdp_entry_point,
    set_up_log_checking_for_sdp,
    sdp_base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """an SDP subarray."""
    return sdp_base_composition


@when("I assign resources to it", target_fixture="message_board")
def i_assign_resources_to_it(
    running_telescope: fxt_types.running_telescope,
    exec_settings: fxt_types.exec_settings,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    assign_resources_test_exec_settings: fxt_types.exec_settings,
):
    """I assign resources to it."""

    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_allocating_a_subarray(
            SUB_ARRAY_ID, assign_resources_test_exec_settings
        ):
            running_telescope.release_subarray_when_finished(
                SUB_ARRAY_ID, RECEPTORS, exec_settings
            )
            entry_point.compose_subarray(
                SUB_ARRAY_ID, RECEPTORS, composition, sb_config.sbid
            )


@then("the subarray must be in IDLE state")
def the_subarray_must_be_in_idle_state():
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(SUB_ARRAY_ID))
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.IDLE)


@pytest.mark.test_tests
@pytest.mark.usefixtures("setup_sdp_mock")
def test_test_sdp_assign_resources(
    run_mock, mock_entry_point: fxt_types.mock_entry_point
):
    """Test the test using a mock SUT"""
    run_mock(test_assign_resources_to_sdp_subarray_in_mid)
    mock_entry_point.spy.set_telescope_to_running.assert_called()
    mock_entry_point.spy.compose_subarray.assert_called()
    mock_entry_point.model.sdp.master.spy.command_inout.assert_called()
    mock_entry_point.model.sdp.subarray1.spy.command_inout.assert_called()
