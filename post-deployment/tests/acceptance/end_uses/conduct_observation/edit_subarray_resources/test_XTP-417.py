#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_calc
----------------------------------
Acceptance tests for MVP.
"""
from types import SimpleNamespace
import logging
from pytest_bdd import scenario, given, when, then
import pytest

from ska_ser_skallop.mvp_fixtures.env_handling import ExecEnv
from ska_ser_skallop.mvp_fixtures.base import ExecSettings
from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from ska_ser_skallop.mvp_control.subarray.compose import SBConfig
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.event_waiting import wait
from ska_ser_skallop.mvp_control.describing import mvp_names
from ska_ser_skallop.event_handling import builders
from ska_ser_skallop.mvp_fixtures.context_management import TelescopeContext

logger = logging.getLogger(__name__)


class Context(SimpleNamespace):
    pass


@pytest.fixture(name="context")
def fxt_context():
    return Context()

@pytest.fixture(name="init")
def fxt_init(exec_env: ExecEnv, exec_settings: ExecSettings):
    exec_env.entrypoint = "tmc"
    #exec_settings.log_enabled = True

@pytest.mark.skallop_test
@scenario("1_XR-13_XTP-494.feature", "A1-Test, Sub-array resource allocation")
def test_allocate_resources(init):
    """Assign Resources."""
    

@given("A running telescope for executing observations on a subarray")
def set_to_running(running_telescope: TelescopeContext):
    pass

@when("I allocate 4 dishes to subarray 1")
def allocate(
    tmp_path,
    context,
    sb_config: SBConfig,
    exec_settings: ExecSettings,
    running_telescope: TelescopeContext,
    entry_point: EntryPoint,
):

    subarray_id = 1
    nr_of_dishes = 4
    receptors = list(range(1, int(nr_of_dishes) + 1))

    composition = conf_types.CompositionByFile(tmp_path, conf_types.CompositionType.STANDARD)

    builder = builders.get_message_board_builder()
    checker = (
        builder.check_that(str(mvp_names.Mid.tm.subarray(subarray_id)))
        .transits_according_to(["EMPTY", ("RESOURCING", "ahead"), "IDLE"])
        .on_attr("obsState")
        .when_transit_occur_on(
            mvp_names.SubArrays(subarray_id).subtract("tm").subtract("cbf domain").list
        )
    )

    running_telescope.release_subarray_when_finished(subarray_id, receptors, exec_settings)
    board = running_telescope.push_context_onto_test(wait.waiting_context(builder))
    context.board = board
    context.checker = checker
    exec_settings.touched = True
    entry_point.compose_subarray(
        subarray_id,
        receptors,
        composition,
        sb_config.sbid,
    )

@then("I have a subarray composed of 4 dishes")
def check_subarray_composition(context):
    board: wait.MessageBoardBase = context.board
    try:
        wait.wait(context.board, 8*60, live_logging=True)
    except wait.EWhilstWaiting as exception:
        logs = board.play_log_book()
        logger.info(f"Log messages during waiting:\n{logs}")
        raise exception


@then("the subarray is in the condition that allows scan configurations to take place")
def check_subarry_state(context):
    checker: builders.Occurrences = context.checker
    checking_logs = checker.print_outcome_for(checker.subject_device)
    logger.info(f"Results of checking:\n{checking_logs}")
    checker.assert_that(checker.subject_device).is_ahead_of_all_on_transit("RESOURCING")
    checker.assert_that(checker.subject_device).is_behind_all_on_transit("IDLE")
