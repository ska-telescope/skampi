"""
Tests to configure a scan using a predefined config
"""
import logging
from types import SimpleNamespace

import pytest
from pytest_bdd import given, scenario, then, when

from ska_ser_skallop.event_handling import builders
from ska_ser_skallop.mvp_control.describing import mvp_names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from ska_ser_skallop.mvp_control.event_waiting import wait
from ska_ser_skallop.mvp_control.subarray.compose import SBConfig
from ska_ser_skallop.mvp_fixtures.base import ExecSettings
from ska_ser_skallop.mvp_fixtures.context_management import (
    SubarrayContext,
    TelescopeContext,
)
from ska_ser_skallop.mvp_fixtures.env_handling import ExecEnv

logger = logging.getLogger(__name__)


class Context(SimpleNamespace):
    pass


@pytest.fixture(name="context")
def fxt_context():
    return Context()


@given("A running telescope for executing observations on a subarray")
def a_running_telescope(running_telescope: TelescopeContext):
    pass


@given("An OET base API for commanding the telescope")
def set_entry_point(exec_env: ExecEnv):
    exec_env.entrypoint = "oet"


@scenario("oet_configure_scan.feature", "Configure a scan using a predefined config")
def test_configure_subarray():
    """
    Test that we can configure a scan using a predefined configuration.

        Scenario: Configure a scan using a predefined config
            Given subarray <subarray_id> that has been allocated
                <nr_of_dishes> according to <SB_config>
            When I configure the subarray to perform a <scan_config>
                scan
            Then the subarray is in the condition to run a scan
    """


@given(
    "subarray <subarray_id> that has been allocated <nr_of_dishes> according to "
    "<SB_config>",
    target_fixture="subarray",
)
def allocate_subarray(
    nr_of_dishes,
    subarray_id,
    SB_config,
    running_telescope: TelescopeContext,
    sb_config: SBConfig,
    tmp_path,
    exec_settings,
) -> SubarrayContext:

    subarray_id = int(subarray_id)
    nr_of_dishes = int(nr_of_dishes)
    receptors = list(range(1, int(nr_of_dishes) + 1))

    if SB_config == "standard":
        composition = conf_types.CompositionByFile(
            tmp_path, conf_types.CompositionType.STANDARD
        )
    else:
        raise NotImplementedError(f"Unknown configuration {SB_config}")

    return running_telescope.allocate_a_subarray(
        subarray_id,
        receptors,
        sb_config,
        exec_settings,
        composition=composition,
    )


@when("I configure the subarray to perform a <scan_config> scan")
def configure(
    scan_config,
    tmp_path,
    subarray: SubarrayContext,
    exec_settings: ExecSettings,
    entry_point: EntryPoint,
    sb_config: SBConfig,
    context,
):

    duration = 2
    if scan_config == "standard":
        configuration = conf_types.ScanConfigurationByFile(
            tmp_path,
            conf_types.ScanConfigurationType.STANDARD,
        )
    else:
        raise NotImplementedError(f"{scan_config}")

    builder = builders.get_message_board_builder()
    checker = (
        builder.check_that(str(mvp_names.Mid.tm.subarray(subarray.id)))
        .transits_according_to(["IDLE", ("CONFIGURING", "ahead"), "READY"])
        .on_attr("obsState")
        .when_transit_occur_on(
            mvp_names.SubArrays(subarray.id).subtract("tm").subtract("cbf domain").list
        )
    )
    subarray.clear_configuration_when_finished(exec_settings)
    board = subarray.push_context_onto_test(wait.waiting_context(builder))
    context.board = board
    context.checker = checker
    exec_settings.touched = True
    entry_point.configure_subarray(
        subarray.id,
        subarray.receptors,
        configuration,
        sb_config.sbid,
        duration,
    )


@then("the subarray is in the condition to run a scan")
def check_ready_for_scan_config(context):
    checker: builders.Occurrences = context.checker
    board: wait.MessageBoardBase = context.board
    try:
        wait.wait(context.board, 25, live_logging=False)
    except wait.EWhilstWaiting as exception:
        logs = board.play_log_book()
        logger.info(f"Log messages during waiting:\n{logs}")
        raise exception
    checking_logs = checker.print_outcome_for(checker.subject_device)
    logger.info(f"Results of checking:\n{checking_logs}")
    checker.assert_that(checker.subject_device).is_behind_all_on_transit("READY")
