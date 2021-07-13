from typing import Any, Iterator, List,Tuple, Union
import pytest
from types import SimpleNamespace
import logging

from skallop.event_handling import builders
from skallop.event_handling.occurences import Occurrences
from skallop.subscribing.base import MessageBoardBase
from skallop.mvp_control.describing import mvp_names
from skallop.mvp_fixtures.context_management import TelescopeContext
from skallop.mvp_control.entry_points.base import EntryPoint
from skallop.mvp_control.event_waiting import wait

logger = logging.getLogger(__name__)

class Context(SimpleNamespace):
    pass

@pytest.fixture(name='context')
def fxt_context():
    return Context()

@pytest.fixture(name='devices')
def fxt_devices()->List[str]:
    devices = mvp_names.Masters()
    for index in range(1,4):
        devices = devices + mvp_names.SubArrays(index)
    for index in range(1,5):
        devices = devices + mvp_names.Sensors(index).subtract('vcc')
    return devices.list
    

@pytest.fixture(name='transit_checking')
def fxt_transit_checker(devices, standby_telescope: TelescopeContext)-> Tuple[Occurrences, MessageBoardBase]:
    builder = builders.get_message_board_builder()
    central_node = mvp_names.Mid.tm.central_node
    checker = (
        builder.check_that(central_node)
        .transits_according_to(["ON"])
        .on_attr("telescopeState")
        .when_transit_occur_on(devices,ignore_first=True)
    )
    board  = standby_telescope.push_context_onto_test(wait.waiting_context(builder))
    return checker, board


# @pytest.mark.xfail
@pytest.mark.skamid
def test_start_up(
        transit_checking: Tuple[Occurrences, MessageBoardBase],
        standby_telescope: TelescopeContext,
        entry_point: EntryPoint
    ):

    checker, board = transit_checking
    entry_point.set_telescope_to_running()
    standby_telescope.telescopeState = "ON"
    try:
        wait.wait(board, 60, live_logging=False)
    except wait.EWhilstWaiting as exception:
        logs = board.play_log_book()
        logger.info(f"Log messages during waiting:\n{logs}")
        raise exception
    checking_logs = checker.print_outcome_for(checker.subject_device)
    logger.info(f"Results of checking:\n{checking_logs}")
    checker.assert_that(checker.subject_device).is_behind_all_on_transit("ON")
