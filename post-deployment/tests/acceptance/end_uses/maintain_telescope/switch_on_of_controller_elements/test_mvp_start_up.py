from typing import Any, Iterator, List,Tuple, Union
import pytest
from types import SimpleNamespace
import logging

logger = logging.getLogger(__name__)

from skallop.event_handling import builders
from skallop.mvp_control.describing import mvp_names
from skallop.mvp_control.telescope import start_up as tel
from skallop.mvp_control.entry_points.base import EntryPoint
from skallop.mvp_fixtures import telescope as tel_fxt
from skallop.connectors import configuration as con_conf
from skallop.mvp_control.event_waiting import wait

class Context(SimpleNamespace):
    pass

@pytest.fixture(name='context')
def fxt_context() -> Iterator[Any]:
    context = Context()
    # uncomment this if you want to test only local
    ##
    # context.mvp_stubbed=True
    ##
    yield context

@pytest.fixture(name='devices')
def fxt_devices()->List[str]:
    devices = mvp_names.Masters()
    for index in range(1,4):
        devices = devices + mvp_names.SubArrays(index)
    for index in range(1,5):
        devices = devices + mvp_names.Sensors(index).subtract('vcc')
    return devices.list
    
@pytest.fixture(name='checking_transits_during_start_up')
def fxt_checking_transits_during_start_up(devices: List[str]) -> Tuple[builders.Occurrences, builders.MessageBoardBuilder]:

    builder = builders.MessageBoardBuilder()
    central_node = mvp_names.Mid.tm.central_node
    transitions = ['ON']
    checker = (
        builder.check_that(central_node)
        .transits_according_to(transitions)
        .on_attr("state")
        .when_transit_occur_on(devices,ignore_first=True)
    )
    return checker, builder

@pytest.fixture(name='prepare_switch_on')
def fxt_prepare_switch_on(running_telescope_args,
    checking_transits_during_start_up: Tuple[builders.Occurrences, builders.MessageBoardBuilder],
    context: Context,
):

    context.checker, builder = checking_transits_during_start_up
    # with log.device_logging(builder,compose_args.devices_to_log):
    with tel_fxt.tear_down_when_finished(running_telescope_args):
        with wait.waiting_context(builder) as board:
            context.board = board
            yield




@pytest.mark.skamid
def test_start_up(prepare_switch_on,running_telescope_args:tel_fxt.RunningTelescopeSettings,context:Context, entry_point: EntryPoint):
    checker: builders.Occurrences = context.checker
    args = running_telescope_args
    # when I start up the telescope
    logger.info('setting telescope to running')
    entry_point.set_telescope_to_running()
    checker: builders.Occurrences = context.checker
    wait.wait(context.board, 15)
    #logs = context.board.play_log_book()
    #logger.info(f"Log messages during waiting:\n{logs}")
    checking_logs = checker.print_outcome_for(checker.subject_device)
    logger.info(f"Results of checking:\n{checking_logs}")
    checker.assert_that(checker.subject_device).is_behind_all_on_transit("ON")
    #checker.assert_that(checker.subject_device).is_behind_all_on_transit("IDLE")
