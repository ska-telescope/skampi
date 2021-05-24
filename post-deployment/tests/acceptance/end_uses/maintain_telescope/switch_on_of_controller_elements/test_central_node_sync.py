from assertpy import assert_that
from time import sleep

from skallop.subscribing.base import CHANGE_EVENT
from skallop.connectors.configuration import get_device_proxy
from skallop.transactions.atomic import atomic



def test_central_node_sync():
    tmc_central_node = get_device_proxy('ska_low/tm_central/central_node')
    def callback(event):
        state = tmc_central_node.State()
        event_state = event.value
        assert_that(event_state).is_equal_to(state)
    tmc_central_node.subscribe_event('State',CHANGE_EVENT,callback)
    with atomic('ska_low/tm_central/central_node','state','ON',5):
            tmc_central_node.StartUpTelescope() #type: ignore
    sleep(2)
    with atomic('ska_low/tm_central/central_node','state','OFF',5):
            tmc_central_node.StandByTelescope() #type: ignore

        



