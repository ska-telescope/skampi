from typing import Iterator
import pytest
from tango import DeviceProxy,EventType # type: ignore
from queue import Queue
from assertpy import assert_that


@pytest.fixture()
def csp_master():
    return DeviceProxy('mid_csp_cbf/sub_elt/master')

@pytest.fixture()
def central_node():
    return DeviceProxy('ska_mid/tm_central/central_node')

class EventsHandler():

    def __init__(self, queue:Queue):
        self.queue = queue

    def push_event(self,Event):
        self.queue.put_nowait(Event)

@pytest.fixture()
def startup_command_dispatched_with_running_subscription(central_node,csp_master)->Iterator[Queue]:
    queue = Queue()
    handler = EventsHandler(queue)
    try:
        id = csp_master.subscribe_event("State",EventType.CHANGE_EVENT,handler)
    except  Exception as e:
        if e.args[0].desc == 'The polling (necessary to send events) for the attribute state is not started':
            csp_master.poll_attribute("State",200)
            id = csp_master.subscribe_event("State",EventType.CHANGE_EVENT,handler)
        else: raise e
    try:
        event = queue.get(timeout=1)
        assert(f'{event.attr_value.value}' == "STANDBY")
        central_node.StartUpTelescope()
        yield queue
    finally:
        csp_master.unsubscribe_event(id)
        central_node.StandbyTelescope()

@pytest.mark.xfail
def test_SKB_17_atomic_switch_on(startup_command_dispatched_with_running_subscription,csp_master:DeviceProxy):
    # given a telescope that has been commanded to startup
    # and a running subscription
    queue:Queue = startup_command_dispatched_with_running_subscription
    # when I wait for a change event on the subsription to csp master
    event = queue.get(timeout=10)
    pushed_value = f'{event.attr_value.value}'
    # and the change event says the value is equal to ON
    assert_that(pushed_value).is_equal_to("ON")
    # then I expect to also get the same results when I query the event value directly (e.g. = ON)
    get_value = f'{csp_master.State()}'
    assert_that(get_value).is_equal_to(pushed_value)