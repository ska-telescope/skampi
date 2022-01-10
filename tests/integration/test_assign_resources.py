"""Assign resources to subarray feature tests."""
import logging
from typing import cast

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


@pytest.mark.skip(reason="test still in dev phase")
@pytest.mark.skalow
@scenario(
    "features/sdp_assign_resources.feature", "Assign resources to sdp subarray in low"
)
def test_assign_resources_to_sdp_subarray_in_low():
    """Assign resources to sdp subarray in low."""


@pytest.mark.skip(reason="test still in dev phase")
@pytest.mark.skamid
@scenario(
    "features/sdp_assign_resources.feature", "Assign resources to sdp subarray in mid"
)
def test_assign_resources_to_sdp_subarray_in_mid():
    """Assign resources to sdp subarray in mid."""


@given("an SDP subarray", target_fixture="test_func_settings")
def an_sdp_subarray(
    set_sdp_entry_point, exec_settings: fxt_types.exec_settings
) -> fxt_types.exec_settings:
    """an SDP subarray."""
    test_func_settings = exec_settings.replica(log_enabled=True)
    sdp_subarray = names.TEL().sdp.subarray(SUB_ARRAY_ID)
    test_func_settings.capture_logs_from(str(sdp_subarray))
    return test_func_settings


@when("I assign resources to it", target_fixture="message_board")
def i_assign_resources_to_it(
    running_telescope: fxt_types.running_telescope,
    exec_settings: fxt_types.exec_settings,
    entry_point: fxt_types.entry_point,
    sb_config: fxt_types.sb_config,
    tmp_path,
    test_func_settings: fxt_types.exec_settings,
) -> MessageBoardBase:
    """I assign resources to it."""
    composition = conf_types.CompositionByFile(
        tmp_path, conf_types.CompositionType.STANDARD
    )
    running_telescope.release_subarray_when_finished(
        SUB_ARRAY_ID, RECEPTORS, exec_settings
    )
    builder = entry_point.set_waiting_for_assign_resources(SUB_ARRAY_ID)
    with device_logging_context(builder, test_func_settings.get_log_specs()):
        board = None
        try:
            with wait_for(
                entry_point.set_waiting_for_assign_resources(SUB_ARRAY_ID), timeout=300
            ) as board:
                entry_point.compose_subarray(
                    SUB_ARRAY_ID, RECEPTORS, composition, sb_config.sbid
                )
                exec_settings.touch()
        except EWhilstWaiting as exception:
            if board:
                logs = board.play_log_book()
                logger.info(f"Log messages during waiting:\n{logs}")
                raise exception
    return cast(MessageBoardBase, board)


@then("the subarray must be in IDLE state")
def the_subarray_must_be_in_idle_state(message_board: MessageBoardBase):
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(SUB_ARRAY_ID))
    result = sdp_subarray.read_attribute("obsstate").value
    # try:
    assert_that(result).is_equal_to(ObsState.IDLE)
    # except AssertionError as exception:
    logs = message_board.play_log_book()
    logger.info(f"Log messages during resource asignment:\n{logs}")
    # raise exception


# @pytest.mark.skip(reason="only run this test for diagnostic purposes during dev")
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
