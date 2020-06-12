from resources.test_support.waiting import Listener,StrategyListenbyPolling,interfaceStrategy
from tango import EventType
from tango.asyncio import DeviceProxy
import asyncio
import mock
import logging
from time import sleep
from mock import Mock
import pytest
from assertpy import assert_that
import inspect



## useful mocks 

class MockReworker():

    def __init__(self,mock):
        self.mock = mock
    
    def get_updated_mock(self):
        return self.mock
    
    def to(self,job,*args):
        self.mock = job(self.mock,*args)
        return self

    def customise_mock_with(self,job,*args):
        self.mock = job(self.mock,*args)


def set(template):
    mock = Mock(spec=template)
    return MockReworker(mock)


def generate_multiple_events(mock,events):
    mock.wait_for_next_event.return_value = events
    return mock

def generate_async_event(mock,events):
    mock.async_wait_for_next_event.return_value = events
    return mock  

def generate_iterative_events(mock,events):
    def next_event(polling,timeout):
        return [events.pop()]
    mock.wait_for_next_event.side_effect = next_event
    return mock

def generate_iterative_events_async(mock,events):
    async def next_event(polling,timeout):
        return [events.pop()]
    mock.async_wait_for_next_event.side_effect = next_event
    return mock
    

def is_already_polled(mock,polling):
    mock.is_attribute_polled.return_value = True
    mock.get_attribute_poll_period.return_value = polling
    return mock


@pytest.fixture
def mock_strategy_multiple():
    reworks = set(interfaceStrategy()).to(generate_multiple_events,['mock event 1','mock event 2'])
    return reworks.get_updated_mock()

@mock.patch('tango.DeviceProxy.__init__')   
def test_listener_can_start_listening(mock_device_proxy):
    #given
    strategy_reworks = set(interfaceStrategy())
    device_reworks = MockReworker(mock_device_proxy)
    device_reworks.customise_mock_with(is_already_polled,111)
    mock_strategy = strategy_reworks.get_updated_mock()
    listener = Listener(mock_device_proxy,mock_strategy)
    #when
    listener.listen_for('attribute')
    #then I expect to remember the original polling 
    mock_device_proxy.is_attribute_polled.assert_called_once()
    assert_that(listener.original_polling).is_equal_to(111)
    #and I expect the actual polling to be updated
    mock_device_proxy.poll_attribute.assert_called_with('attribute',100)
    assert_that(listener.current_polling).is_equal_to(100)
    mock_strategy.subscribe.assert_called_once()

@mock.patch('tango.DeviceProxy.__init__')   
def test_listener_can_start_async(mock_device_proxy):
    #given
    strategy_reworks = set(interfaceStrategy())
    device_reworks = MockReworker(mock_device_proxy)
    device_reworks.customise_mock_with(is_already_polled,111)
    mock_strategy = strategy_reworks.get_updated_mock()
    listener = Listener(mock_device_proxy,mock_strategy)
    #when 
    assert(inspect.iscoroutinefunction(listener.async_listen_for))
    asyncio.run(listener.async_listen_for('attribute'))
    #then
    mock_device_proxy.is_attribute_polled.assert_called_once()
    assert_that(listener.original_polling).is_equal_to(111)
    #and I expect the actual polling to be updated
    mock_device_proxy.poll_attribute.assert_called_with('attribute',100)
    assert_that(listener.current_polling).is_equal_to(100)
    mock_strategy.async_subscribe.assert_called_once()


@mock.patch('tango.DeviceProxy.__init__')  
def test_listener_can_wait_events(mock_device_proxy):
    strategy_reworks = set(interfaceStrategy()).to(generate_multiple_events,['event1'])
    mock_strategy = strategy_reworks.get_updated_mock()
    listener = Listener(mock_device_proxy,mock_strategy)
    #when
    listener.listen_for('attribute')
    result = listener.wait_for_next_event()
    #then
    assert_that(result).is_equal_to(['event1'])
    #when
    strategy_reworks.customise_mock_with(generate_async_event,['event1'])
    result = asyncio.run(listener.async_wait_for_next_event())
    #then
    assert_that(result).is_equal_to(['event1'])


@mock.patch('tango.DeviceProxy.__init__')  
def test_listener_can_get_events_on(mock_device_proxy):
    test_events = ['event1','event2','event3']
    test_events2 = test_events.copy()
    strategy_reworks = set(interfaceStrategy()).to(generate_iterative_events,test_events)
    mock_strategy = strategy_reworks.get_updated_mock()
    listener = Listener(mock_device_proxy,mock_strategy)
    #when
    for event in listener.get_events_on('attr'):
        assert(listener.listening)
        assert_that(event).is_equal_to(test_events2.pop())
        if len(test_events) == 0:
            listener.stop_listening()

@mock.patch('tango.DeviceProxy.__init__')  
def test_listener_can_get_events_on_async(mock_device_proxy):
    test_events = ['event1','event2','event3']
    test_events2 = test_events.copy()
    strategy_reworks = set(interfaceStrategy()).to(generate_iterative_events_async,test_events)
    mock_strategy = strategy_reworks.get_updated_mock()
    listener = Listener(mock_device_proxy,mock_strategy)
    #when
    async def async_run():
        async for event in listener.async_get_events_on('attr'):
            assert(listener.listening)
            assert_that(event).is_equal_to(test_events2.pop())
            if len(test_events) == 0:
                listener.stop_listening()
    asyncio.run(async_run())


# integration tests with an actual device 
pytest.mark.skip("only run test when test device proxu is deployed")
def test_wait_in_for_loop():
    async def async_run():
        events_received = 0
        device_proxy = await DeviceProxy('sys/tg_test/1')
        strategy = StrategyListenbyPolling(device_proxy)
        listener = Listener(device_proxy,strategy)
        async for event in listener.async_get_events_on('Status',10):
            if events_received == 0:
                await device_proxy.SwitchStates()
                sleep(0.2)
                await device_proxy.SwitchStates()
                sleep(0.2)
                await device_proxy.SwitchStates()
                sleep(0.2)
            events_received +=1
            logging.info(event)
            if events_received > 3:
                listener.stop_listening()
    asyncio.run(async_run())
            


    
