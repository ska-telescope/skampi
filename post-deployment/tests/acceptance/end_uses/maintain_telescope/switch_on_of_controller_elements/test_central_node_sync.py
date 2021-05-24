from assertpy import assert_that
from time import sleep

import pytest

from skallop.subscribing.base import CHANGE_EVENT
from skallop.connectors.configuration import get_device_proxy
from skallop.transactions.atomic import atomic



@pytest.mark.skalow
def test_central_node_sync():
    tmc_central_node = get_device_proxy('ska_low/tm_central/central_node')
    def callback(event):
        state = tmc_central_node.State()
        event_state = event.attr_value.value
        assert_that(event_state).is_equal_to(state)

    devices = [
        'ska_low/tm_central/central_node',
        'low-mccs/control/control',
        'low-mccs/station/001',
        'low-mccs/tile/0001'
    ]
    tmc_central_node.subscribe_event('State',CHANGE_EVENT,callback)
    with atomic(devices,'state','ON',5):
            tmc_central_node.StartUpTelescope() #type: ignore
    
    sleep(10)
    with atomic('ska_low/tm_central/central_node','state','OFF',5):
            tmc_central_node.StandByTelescope() #type: ignore

        



