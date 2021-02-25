import pytest
from time import sleep
from contextlib import contextmanager
from sys import intern
from types import SimpleNamespace
from typing import Any, Iterator, List, NamedTuple, Tuple, Union
from pytest_bdd import scenario, given, when, then
from skallop.event_handling import builders
from skallop.mvp_fixtures import telescope as tel_fxt
from skallop.mvp_fixtures import types as fxt_types
from skallop.mvp_control.entry_points import oet
from skallop.mvp_control.entry_points import base
from skallop.mvp_control.entry_points import types
from skallop.mvp_control.describing import mvp_names
from skallop.event_handling import logging as log
from skallop.mvp_control.event_waiting import wait
from skallop.mvp_fixtures import subarray_composition as sub_comp_fxt
from skallop.mvp_control.subarray import compose
from skallop.mvp_control.subarray import configure
from skallop.subscribing import producers
import logging
import mock


logger = logging.getLogger("__name__")


# uncomment this if you don't want to create real fixtures for testing purposes
# @pytest.fixture(name='running_telescope')
# def fxt_running_telescope():
#    pass

# @pytest.fixture(name='composed_subarray')
# def fxt_composed_subarray():
#    pass

# fixture classes
class Context(SimpleNamespace):
    mvp_stubbed = False

# use this if you want to stub out the mvp


@contextmanager
def stub_out_mvp():
    with mock.patch('mvp_control.subarray.compose.assert_I_can_compose_a_subarray'):
        with mock.patch('mvp_control.telescope.start_up.assert_I_can_set_telescope_to_running'):
            with mock.patch('mvp_control.telescope.start_up.assert_I_can_set_telescope_to_standby'):
                with mock.patch('mvp_control.subarray.compose.tear_down_when_finished'):
                    with mock.patch('mvp_control.subarray.configure.assert_I_can_configure_a_subarray'):
                        with mock.patch('mvp_control.subarray.configure.tear_down_when_finished'):
                            with mock.patch('event_handling.logging.device_logging'):
                                with mock.patch('mvp_control.event_waiting.wait.waiting_context'):
                                    with mock.patch('mvp_control.event_waiting.wait.wait'):
                                        yield


@pytest.fixture(scope="session",name='context')
def fxt_context() -> Iterator[Any]:
    context = Context()
    # uncomment this if you want to test only local
    ##
    # context.mvp_stubbed=True
    ##
    if context.mvp_stubbed:
        with stub_out_mvp():
            yield context
    else:
        yield context


@pytest.fixture(name='base_factory')
def fxt_base_factory(context):
    if context.mvp_stubbed:
        return builders.BaseFactory()
    else:
        return None


@pytest.fixture(scope="session",name='entry_point')
def fxt_entry_point(context) -> base.EntryPoint:
    if not context.mvp_stubbed:
        entry_point = oet.EntryPoint()
    else:
        entry_point = base.EntryPoint()
    return entry_point


# fixture arguments
# running telescope
# overrides base fixture


@pytest.fixture(scope="session",name='running_telescope_args')
def fxt_running_telescope_args(entry_point):
    return tel_fxt.RunningTelescopeArgs(
        entry_point=entry_point,
        log_enabled=False,
        log_spec=[],
        play_logbook=fxt_types.PlaySpec(False),
    )


# background fixtures
@given("A running telescope for executing observations on a subarray")
def a_running_telescope(running_telescope):
    pass


@given("An OET base API for commanding the telescope")
def set_entry_point():
    pass

@pytest.mark.skamid
@scenario(
    "transitions.feature",
    "Allocate dishes to a subarray using a predefined config",
    example_converters=dict(nr_of_dishes=int, subarray_id=int, SB_config=str),
)
def test_allocate():
    pass


## composition fixtures and args classes ##
class ComposeArgs(NamedTuple):
    subarray_id: int
    receptors: List[int]
    composition: types.CompositionByFile
    devices_to_log: List[log.DeviceLogSpec]
    time_out: int
    live_logging: bool
    filter_logs: bool
    log_filter_pattern: str


@pytest.fixture(name='compose_args')
def fxt_compose_args(
    tmp_path: str, nr_of_dishes: int, subarray_id: int, SB_config: str, entry_point: oet.EntryPoint
) -> ComposeArgs:
    receptors = list(range(1, nr_of_dishes + 1))
    devices_to_log = (
        []
    )  # [log.DeviceLogSpec(device) for device in mvp_names.SubArrays(subarray_id).subtract('cbf domain')]
    if SB_config == "standard":
        composition = types.CompositionByFile(
            tmp_path, types.FileCompositionType.standard)
    else:
        raise NotImplementedError(f"{SB_config}")
    return ComposeArgs(
        subarray_id,
        receptors,
        composition,
        devices_to_log,
        time_out=5,
        live_logging=False,
        filter_logs=False,
        log_filter_pattern=r"Transaction\[txn",
    )


@pytest.fixture(name='subarray_internals')
def fxt_subarray_internals(subarray_id: int) -> List[str]:
    return mvp_names.SubArrays(subarray_id).subtract("tm").subtract("cbf domain").list


# use this fixture if you want to wait for a set of states and to observe another for diagnostic
# purposes
@pytest.fixture(name='waiting_for_composition')
def fxt_waiting_for_composition(
    compose_args: ComposeArgs, base_factory
) -> builders.MessageBoardBuilder:
    args = compose_args
    builder = builders.MessageBoardBuilder(base_factory)
    builder.set_waiting_on(str(mvp_names.Mid.tm.subarray(args.subarray_id))).for_attribute(
        "obsState"
    ).to_become_equal_to("IDLE", master=True)
    for device in mvp_names.SubArrays(args.subarray_id).subtract("tm").subtract("cbf domain"):
        builder.set_waiting_on(device).for_attribute("obsState").and_observe()
    return builder


@pytest.fixture(name='allocate_transitions')
def fxt_allocate_transitions() -> List[Union[str, Tuple[str, str]]]:
    return ["EMPTY", ("RESOURCING", "ahead"), "IDLE"]


@pytest.fixture(name='tear_down_args')
def fxt_tear_down_args(
    entry_point: oet.EntryPoint, compose_args: ComposeArgs
) -> compose.ComposeSubarrayArgs:

    return compose.ComposeSubarrayArgs(
        compose_args.subarray_id, compose_args.receptors, entry_point=entry_point
    )


# use this fixture if you want to specifically test and verify the transitions states of one device
# compared to anathor during allocation of resources
@pytest.fixture(name='checking_transits_during_allocation')
def fxt_checking_transits_during_allocation(
    subarray_id: int,
    allocate_transitions: List[Union[str, Tuple[str, str]]],
    subarray_internals: List[str],
    base_factory,
) -> Tuple[builders.Occurrences, builders.MessageBoardBuilder]:

    builder = builders.MessageBoardBuilder(base_factory)
    subarray_node = str(mvp_names.Mid.tm.subarray(subarray_id))
    checker = (
        builder.check_that(subarray_node)
        .transits_according_to(allocate_transitions)
        .on_attr("obsState")
        .when_transist_occur_on(subarray_internals)
    )
    return checker, builder


# uncomment this if you want to use basic waiting for a subarray (fixture = waiting_for_composition)
"""
@pytest.fixture(name='prepare_allocation')
def fxt_prepare_allocation(
        entry_point:oet.EntryPoint,
        compose_args:ComposeArgs,
        tear_down_args: compose.ComposeSubarrayArgs,
        waiting_for_composition:builders.MessageBoardBuilder,
        context:Context):

    compose.assert_I_can_compose_a_subarray(compose_args.subarray_id,compose_args.receptors)
    with log.device_logging(waiting_for_composition,compose_args.devices_to_log):
        with wait.waiting_context(waiting_for_composition) as board:
            context.board = board
            with compose.tear_down_when_finished(tear_down_args):
                yield
"""


@pytest.fixture(name='prepare_allocation')
def fxt_prepare_allocation(
    compose_args: ComposeArgs,
    tear_down_args: compose.ComposeSubarrayArgs,
    checking_transits_during_allocation: Tuple[builders.Occurrences, builders.MessageBoardBuilder],
    context: Context,
):

    context.checker, builder = checking_transits_during_allocation
    compose.assert_I_can_compose_a_subarray(
        compose_args.subarray_id, compose_args.receptors)
    # with log.device_logging(builder,compose_args.devices_to_log):
    with wait.waiting_context(builder) as board:
        context.board = board
        with compose.tear_down_when_finished(tear_down_args):
            yield


@when(
    "I allocate <nr_of_dishes> dishes to subarray <subarray_id> using the <SB_config> SB configuration"
)
def allocate_2_dishes(
    prepare_allocation, entry_point: oet.EntryPoint, compose_args: ComposeArgs, context: Context
):
    args = compose_args
    entry_point.compose_subarray(args.subarray_id, args.receptors, args.composition)


@then("The subarray is in the condition that allows scan configurations to take place")
def subarray_ready_for_running_scans(compose_args: ComposeArgs, context: Context):
    args = compose_args
    board: builders.MessageBoard = context.board
    checker: builders.Occurrences = context.checker
    wait.wait(context.board, args.time_out, args.live_logging)
    context.state = "composed"
    logs = board.play_log_book(args.filter_logs, args.log_filter_pattern)
    logger.info(f"Log messages during waiting:\n{logs}")
    checking_logs = checker.print_outcome_for(checker.subject_device)
    logger.info(f"Results of checking:\n{checking_logs}")
    #checker.assert_that(checker.subject_device).is_behind_all_on_transit(
    #    "RESOURCING")
    checker.assert_that(checker.subject_device).is_behind_all_on_transit("IDLE")

@pytest.mark.xfail
@pytest.mark.skamid
@scenario(
    "transitions.feature",
    "Configure a scan using a predefined config",
    example_converters=dict(nr_of_dishes=int, subarray_id=int,
                            SB_config=str, scan_config=str),
)
def test_configure():
    pass


# overrides composed subarray fixture args
@pytest.fixture(name='composed_subarray_args')
def fxt_composed_subarray_args(tmp_path, SB_config, nr_of_dishes, subarray_id: int, entry_point):
    if SB_config == "standard":
        composition = sub_comp_fxt.conf_types.CompositionByFile(
            tmp_path, sub_comp_fxt.conf_types.FileCompositionType.standard
        )
    else:
        raise NotImplementedError("configuration type {SB_config} not implemented")
    return sub_comp_fxt.Args(
        subarray_id=subarray_id,
        entry_point=entry_point,
        receptors=list(range(1, nr_of_dishes + 1)),
        composition=composition,
    )


class ScanConfigArgs(NamedTuple):
    subarray_id: int
    receptors: List[int]
    configuration: types.ConfigurationByFile
    devices_to_log: List[log.DeviceLogSpec]
    time_out: int
    live_logging: bool
    filter_logs: bool
    log_filter_pattern: str


@pytest.fixture(name='scan_config_args')
def fxt_scan_config_args(
    tmp_path,
    scan_config: str,
    nr_of_dishes: int,
    subarray_id: int,
    composed_subarray_args: sub_comp_fxt.Args,
) -> ScanConfigArgs:

    receptors = list(range(1, nr_of_dishes + 1))
    devices_to_log = [
        log.DeviceLogSpec(device)
        for device in mvp_names.SubArrays(subarray_id).subtract("cbf domain")
    ]
    # note the compositon.metadata in order to tie the ids togethor
    if scan_config == "standard":
        configuration = types.ConfigurationByFile(
            tmp_path,
            types.FileConfigurationType.standard,
            composed_subarray_args.composition.metadata,
        )
    else:
        raise NotImplementedError(f"{scan_config}")
    return ScanConfigArgs(
        subarray_id,
        receptors,
        configuration,
        devices_to_log,
        time_out=5,
        live_logging=False,
        filter_logs=False,
        log_filter_pattern=r"Transaction\[txn",
    )


# use this fixture if you want to wait for a set of states and to observe another for diagnostic
# purposes
@pytest.fixture(name='waiting_for_configuration')
def fxt_waiting_for_configuration(
    scan_config_args: ScanConfigArgs, base_factory
) -> builders.MessageBoardBuilder:
    args = scan_config_args
    builder = builders.MessageBoardBuilder(base_factory)
    subarray_node = str(mvp_names.Mid.tm.subarray(args.subarray_id))
    builder.set_waiting_on(subarray_node).for_attribute("obsState").to_become_equal_to(
        "READY", master=True
    )
    for device in mvp_names.SubArrays(args.subarray_id).subtract("tm").subtract("cbf domain"):
        builder.set_waiting_on(device).for_attribute("obsState").and_observe()
    return builder


@pytest.fixture(name='scan_transitions')
def fxt_scan_transitions() -> List[Union[str, Tuple[str, str]]]:
    return ["IDLE", ("CONFIGURING", "ahead"), "READY"]


# use this fixture if you want to specifically test and verify the transitions states of one device
# compared to another
@pytest.fixture(name='checking_transits_during_configuration')
def fxt_checking_transits_during_configuration(
    subarray_id: int,
    scan_transitions: List[Union[str, Tuple[str, str]]],
    subarray_internals: List[str],
    base_factory,
) -> Tuple[builders.Occurrences, builders.MessageBoardBuilder]:

    builder = builders.MessageBoardBuilder(base_factory)
    subarray_node = str(mvp_names.Mid.tm.subarray(subarray_id))
    checker = (
        builder.check_that(subarray_node)
        .transits_according_to(scan_transitions)
        .on_attr("obsState")
        .when_transist_occur_on(subarray_internals)
    )
    return checker, builder


@pytest.fixture(name='clear_args')
def fxt_clear_args(
    scan_config_args: ScanConfigArgs, entry_point: oet.EntryPoint
) -> configure.ConFigureSubarrayArgs:
    return configure.ConFigureSubarrayArgs(
        scan_config_args.subarray_id,
        scan_config_args.receptors,
        entry_point=entry_point,
        configuration=scan_config_args.configuration,
    )


# uncomment this if you want to use basic waiting for a subarray (fixture = waiting_for_configuration)
"""
@pytest.fixture(name='prepare_for_configure')
def fxt_prepare_for_configure(
            scan_config_args:ScanConfigArgs,
            clear_args:configure.ConFigureSubarrayArgs,
            waiting_for_configuration:builders.MessageBoardBuilder,
            context:Context):
    builder = waiting_for_configuration
    args = scan_config_args
    configure.assert_I_can_configure_a_subarray(scan_config_args.subarray_id,scan_config_args.receptors))
    with log.device_logging(builder,scan_config_args.devices_to_log):
        with wait.waiting_context(builder) as board:
            context.board = board
            with configure.tear_down_when_finished(clear_args):
                yield
"""


@pytest.fixture(name='prepare_for_configure')
def fxt_prepare_for_configure(
    clear_args: configure.ConFigureSubarrayArgs,
    scan_config_args: ScanConfigArgs,
    checking_transits_during_configuration: Tuple[
        builders.Occurrences, builders.MessageBoardBuilder
    ],
    context: Context,
):

    context.checker, builder = checking_transits_during_configuration
    configure.assert_I_can_configure_a_subarray(
        scan_config_args.subarray_id, scan_config_args.receptors
    )
    # with log.device_logging(builder,scan_config_args.devices_to_log):
    with wait.waiting_context(builder) as board:
        context.board = board
        with configure.tear_down_when_finished(clear_args):
            yield


@given("subarray <subarray_id> that has been allocated <nr_of_dishes> according to <SB_config>")
def allocated_subarray(composed_subarray):
    pass


@when("I configure the subarray to perform a <scan_config> scan")
def configure_subarray(
    prepare_for_configure,
    entry_point: oet.EntryPoint,
    scan_config_args: ScanConfigArgs,
    context: Context,
):
    args = scan_config_args
    entry_point.configure_subarray(args.subarray_id, args.receptors, args.configuration)


@then("the subarray is in the condition to run a scan")
def check_subarray_ready_to_scan(scan_config_args: ScanConfigArgs, context: Context):
    args = scan_config_args
    wait.wait(context.board, args.time_out, args.live_logging)
    context.state = "configured"
    board: builders.MessageBoard = context.board
    checker: builders.Occurrences = context.checker
    logs = board.play_log_book(args.filter_logs, args.log_filter_pattern)
    logger.info(f"Log messages during waiting:\n{logs}")
    checking_logs = checker.print_outcome_for(checker.subject_device)
    logger.info(f"Results of checking transitions:\n{checking_logs}")
    #checker.assert_that(checker.subject_device).is_behind_all_on_transit("CONFIGURING")
    checker.assert_that(checker.subject_device).is_behind_all_on_transit("READY")



