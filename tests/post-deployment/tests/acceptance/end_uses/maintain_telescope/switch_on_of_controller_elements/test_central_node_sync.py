from assertpy import assert_that
from time import sleep
import logging
from contextlib import ExitStack, contextmanager

import pytest

from ska_ser_skallop.subscribing.base import CHANGE_EVENT
from ska_ser_skallop.connectors.configuration import get_device_proxy
from ska_ser_skallop.transactions.atomic import atomic
from ska_ser_skallop.event_handling import builders
from ska_ser_skallop.mvp_control.event_waiting import wait
from ska_ser_skallop.mvp_fixtures.context_management import StackableContext

logger = logging.getLogger(__name__)


@pytest.fixture(name = 'context')
def fxt_context():
    with ExitStack() as stack:
        yield StackableContext(stack)

@contextmanager
def start_up_telescope(tmc_central_node):
    tmc_central_node.StartUpTelescope() #type: ignore
    yield
    with atomic('ska_low/tm_central/central_node','state','OFF',5):
            tmc_central_node.StandByTelescope() #type: ignore


@pytest.mark.quarantine
@pytest.mark.skalow
def test_central_node_sync(context: StackableContext):
    tmc_central_node = get_device_proxy('ska_low/tm_central/central_node')
    def callback(event):
        state = tmc_central_node.State()
        event_state = event.attr_value.value
        assert_that(event_state).is_equal_to(state)

    devices = [
        'ska_low/tm_central/central_node',
        'low-mccs/control/control',
        'low-mccs/station/001',
        'low-mccs/station/002',
        'low-mccs/tile/0001',
        'low-mccs/tile/0002',
        'low-mccs/tile/0003',
        'low-mccs/tile/0004',
        'ska_low/tm_subarray_node/1',
        'ska_low/tm_leaf_node/mccs_master',
        'ska_low/tm_leaf_node/mccs_subarray01',
        'low-mccs/antenna/000001',
        'low-mccs/antenna/000002',
        'low-mccs/antenna/000003',
        'low-mccs/antenna/000004',
    ]
    tmc_central_node.subscribe_event('State',CHANGE_EVENT,callback)

    builder = builders.get_message_board_builder()
    checker = (
        builder.check_that('ska_low/tm_central/central_node')
        .transits_according_to(["ON"])
        .on_attr("state")
        .when_transit_occur_on(devices)
    )
    with wait.wait_for(builder):
        context.push_context_onto_test(
            start_up_telescope(tmc_central_node)
        )
    checking_logs = checker.print_outcome_for(checker.subject_device)
    logger.info(f"Results of checking:\n{checking_logs}")
    checker.assert_that('ska_low/tm_central/central_node').is_behind_all_on_transit("ON")







