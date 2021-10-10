from typing import List,Tuple
import pytest
from types import SimpleNamespace
import logging

from ska_ser_skallop.event_handling import builders
from ska_ser_skallop.event_handling import occurences
from ska_ser_skallop.event_handling.occurences import Occurrences
from ska_ser_skallop.subscribing.base import MessageBoardBase
from ska_ser_skallop.mvp_control.describing import mvp_names
from ska_ser_skallop.mvp_fixtures.context_management import TelescopeContext
from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from ska_ser_skallop.mvp_control.event_waiting import wait


logger = logging.getLogger(__name__)

class Context(SimpleNamespace):
    pass

@pytest.fixture(name='context')
def fxt_context():
    return Context()

@pytest.fixture(name='devices')
def fxt_devices()->List[str]:
    tel = mvp_names.TEL()
    devices = tel.masters().subtract('tm')
    if tel.skamid:
        for index in range(1,2):
            devices = devices + tel.subarrays(index).subtract('tm')
        for index in range(1,5):
            devices = devices + tel.sensors(index).subtract('vcc').subtract('tm')
    return devices.list
    

@pytest.fixture(name='transit_checking')
def fxt_transit_checker(devices, standby_telescope: TelescopeContext, )-> Tuple[Occurrences, MessageBoardBase]:
    builder = builders.get_message_board_builder()
    tel = mvp_names.TEL()
    central_node = tel.tm.central_node
    att = "telescopeState" if tel.skamid else 'state'
    checker = (
        builder.check_that(central_node)
        .transits_according_to(["ON"])
        .on_attr(att)
        .when_transit_occur_on(devices,ignore_first=True, devices_to_follow_attr='state')
    )
    board  = standby_telescope.push_context_onto_test(wait.waiting_context(builder))
    return checker, board

def check_startup(
        transit_checking: Tuple[Occurrences, MessageBoardBase],
        standby_telescope: TelescopeContext,
        entry_point: EntryPoint
    ):

    checker, board = transit_checking
    entry_point.set_telescope_to_running()
    standby_telescope.state = "ON"
    try:
        wait.wait(board, 100, live_logging=False)
    except wait.EWhilstWaiting as exception:
        logs = board.play_log_book()
        logger.info(f"Log messages during waiting:\n{logs}")
        raise exception
    checking_logs = checker.print_outcome_for(checker.subject_device)
    logger.info(f"Results of checking:\n{checking_logs}")
    try:
        checker.assert_that(checker.subject_device).is_behind_all_on_transit("ON")
    except AssertionError as error:
        logs = board.play_log_book()
        logger.info(f"Error in occurrences test: Log messages during waiting:\n{logs}")
        raise error


@pytest.mark.skamid
def test_start_up(
        transit_checking: Tuple[Occurrences, MessageBoardBase],
        standby_telescope: TelescopeContext,
        entry_point: EntryPoint
    ):

    check_startup(
        transit_checking,
        standby_telescope,
        entry_point
    )

@pytest.mark.xfail
@pytest.mark.skalow
def test_start_up_low(
        transit_checking: Tuple[Occurrences, MessageBoardBase],
        standby_telescope: TelescopeContext,
        entry_point: EntryPoint
    ):

    check_startup(
        transit_checking,
        standby_telescope,
        entry_point
    )
