from resources.test_support.waiting import Listener,ConsumePeriodically,interfaceStrategy,ConsumeImmediately,ListenerTimeOut
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
    mock.wait_for_next_event.return_value = events,10
    return mock

def generate_async_event(mock,events):
    mock.async_wait_for_next_event.return_value = events,10
    return mock  

def generate_iterative_events(mock,events):
    def next_event(timeout):
        return [events.pop()],10
    mock.wait_for_next_event.side_effect = next_event
    return mock

def generate_iterative_events_async(mock,events):
    async def next_event(timeout):
        return [events.pop()],timeout
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
def test_listen_without_server_side_polling(mock_device_proxy):
    # given
    mock_strategy = set(interfaceStrategy()).get_updated_mock()
    listener = Listener(mock_device_proxy,mock_strategy,override_serverside_polling=False)
    # when I start listening
    listener.listen_for('attribute')
    #then I do not expect to remember the original polling 
    mock_device_proxy.is_attribute_polled.assert_not_called()
    assert_that(listener.original_server_polling).is_equal_to(None)
    #and I do not expect the actual polling to be updated
    mock_device_proxy.poll_attribute.assert_not_called()
    # but I do expect a subscription to be called
    mock_strategy.subscribe.assert_called_once()
    # and when I stop listening
    listener.stop_listening()
    #and I do not expect the actual polling to be updated
    mock_device_proxy.poll_attribute.assert_not_called()

@mock.patch('tango.DeviceProxy.__init__')   
def test_raises_time_out_for_pushing(mock_device_proxy):
    strategy = ConsumeImmediately(mock_device_proxy)
    mock_device_proxy.name.return_value = 'mock_device'
    with pytest.raises(ListenerTimeOut, match=r"Timed out after 0.5 seconds waiting for events on attributes\['test'\] for device mock_device"):
        strategy.subscribe('test')
        strategy.wait_for_next_event(timeout=0.5)

@mock.patch('tango.DeviceProxy.__init__')
def test_raises_time_out_for_pulling(mock_device_proxy):
    strategy = ConsumePeriodically(mock_device_proxy)
    mock_device_proxy.name.return_value = 'mock_device'
    mock_device_proxy.get_events.return_value = []
    with pytest.raises(ListenerTimeOut, match=r"Timed out after 0.5 seconds waiting for events on attributes\['test'\] for device mock_device"):
        strategy.subscribe('test')
        strategy.wait_for_next_event(timeout=0.5)


@mock.patch('tango.DeviceProxy.__init__')   
def test_listen_with_server_side_polling_based_on_strategy(mock_device_proxy):
    #given
    device_reworks = MockReworker(mock_device_proxy)
    strategy_reworks = set(ConsumePeriodically(mock_device_proxy))
    device_reworks.customise_mock_with(is_already_polled,100)
    mock_strategy = strategy_reworks.get_updated_mock()
    mock_strategy.polling = 100
    listener = Listener(mock_device_proxy,mock_strategy, override_serverside_polling=True)
    #when
    listener.listen_for('attribute')
    #then I expect to remember the original polling 
    mock_device_proxy.is_attribute_polled.assert_called_once()
    assert_that(listener.original_server_polling).is_equal_to(100)
    #and I expect the actual polling to be updated
    mock_device_proxy.poll_attribute.assert_called_with('attribute',50)
    assert_that(listener.current_server_side_polling).is_equal_to(50)
    mock_strategy.subscribe.assert_called_once()
    # and when I stop listening
    listener.stop_listening()
    #and I expect the original polling to be restored
    mock_device_proxy.poll_attribute.assert_called_with('attribute',100)

@mock.patch('tango.DeviceProxy.__init__')   
def test_listen_with_server_side_polling(mock_device_proxy):
    #given
    strategy_reworks = set(interfaceStrategy())
    device_reworks = MockReworker(mock_device_proxy)
    device_reworks.customise_mock_with(is_already_polled,100)
    mock_strategy = strategy_reworks.get_updated_mock()
    listener = Listener(mock_device_proxy,mock_strategy, override_serverside_polling=True)
    #when
    listener.listen_for('attribute')
    #then I expect to remember the original polling 
    mock_device_proxy.is_attribute_polled.assert_called_once()
    assert_that(listener.original_server_polling).is_equal_to(100)
    #and I expect the actual polling to be updated
    mock_device_proxy.poll_attribute.assert_called_with('attribute',100)
    assert_that(listener.current_server_side_polling).is_equal_to(100)
    mock_strategy.subscribe.assert_called_once()
    # and when I stop listening
    listener.stop_listening()
    #and I expect the original polling to be restored
    mock_device_proxy.poll_attribute.assert_called_with('attribute',100)
    

@mock.patch('resources.test_support.waiting.interfaceStrategy') 
@mock.patch('tango.DeviceProxy.__init__') 
def test_listener_can_listen_for_multiple_events(mock_device_proxy,mock_strategy):
    # given
    listener = Listener(mock_device_proxy,mock_strategy)
    # when    
    listener.listen_for('attribute1','attribute2')
    # I will subscribe both attributes
    assert_that(mock_strategy.subscribe.call_count).is_equal_to(2)

@mock.patch('resources.test_support.waiting.datetime')
@mock.patch('tango.DeviceProxy.__init__') 
def test_cons_imm_delivers_elapsed_time(mock_device_proxy,mock_time):
    # given
    mock_time.now.return_value = 10
    s = ConsumeImmediately(mock_device_proxy)
    # when I scubscribe and wait for an event on that subscription
    s.subscribe('attr1')
    s._cb('event')
    events, elapsed_time = s.wait_for_next_event()
    # I expect the elapsed time to be given with the event
    # time is constantly 10 hence elapsedtime should be 0
    assert_that(elapsed_time).is_equal_to(0)

@mock.patch('resources.test_support.waiting.datetime')
@mock.patch('tango.DeviceProxy.__init__') 
def test_consume_per_delivers_elapsed_time(mock_device_proxy,mock_time):
    # given
    mock_time.now.return_value = 10
    s = ConsumePeriodically(mock_device_proxy)
    # when I scubscribe and wait for an event on that subscription
    s.subscribe('attr1')
    mock_device_proxy.get_events.return_value='event1'
    events, elapsed_time = s.wait_for_next_event()
    # I expect the elapsed time to be given with the event
    # time is constantly 10 hence elapsedtime should be 0
    assert_that(elapsed_time).is_equal_to(0)



@mock.patch('tango.DeviceProxy.__init__') 
def test_cons_imm_can_subscribe_multiple_times(mock_device_proxy):
    # given
    s = ConsumeImmediately(mock_device_proxy)
    # when I scubscribe once
    s.subscribe('attr1')
    assert_that(mock_device_proxy.subscribe_event.call_count).is_equal_to(1)
    # when I scubscribe again
    s.subscribe('attr2')
    assert_that(mock_device_proxy.subscribe_event.call_count).is_equal_to(2)
    # when I unsubscribe 
    s.unsubscribe()
    #I expect all events to be unsubscribed
    assert_that(mock_device_proxy.unsubscribe_event.call_count).is_equal_to(2)

@mock.patch('tango.DeviceProxy.__init__') 
def test_consume_per_can_subscribe_multiple_times(mock_device_proxy):
    # given
    s = ConsumePeriodically(mock_device_proxy)
    # when I scubscribe once
    s.subscribe('attr1')
    assert_that(mock_device_proxy.subscribe_event.call_count).is_equal_to(1)
    # when I scubscribe again
    s.subscribe('attr2')
    assert_that(mock_device_proxy.subscribe_event.call_count).is_equal_to(2)
    # when I unsubscribe 
    s.unsubscribe()
    #I expect all events to be unsubscribed
    assert_that(mock_device_proxy.unsubscribe_event.call_count).is_equal_to(2)

@mock.patch('tango.DeviceProxy.__init__') 
def test_consume_per_can_wait_on_multiple_events(mock_device_proxy):
    # given
    s = ConsumePeriodically(mock_device_proxy)
    def mock_get_events(id):
        return [id,id+1]
    mock_device_proxy.get_events.side_effect = mock_get_events
    # and given I have subscribed once
    mock_device_proxy.subscribe_event.return_value = 1
    s.subscribe('attr1')
    mock_device_proxy.subscribe_event.return_value = 3
    s.subscribe('attr2')
    # when I wait for next event
    result,elapsed_time = s.wait_for_next_event()
    # then both attributes should have been generating events
    assert_that(result).is_equal_to([1,2,3,4])


@mock.patch('resources.test_support.waiting.Queue') 
@mock.patch('tango.DeviceProxy.__init__') 
def test_consume_imm_can_wait_on_multiple_events(mock_device_proxy,mock_queue):
    # given
    s = ConsumeImmediately(mock_device_proxy)
    # and given I have subscribed once
    mock_device_proxy.subscribe_event.return_value = 1
    s.subscribe('attr1')
    mock_device_proxy.subscribe_event.return_value = 3
    s.subscribe('attr2')
    # when I wait for next event
    s.wait_for_next_event()
    # then I need to know that the queue has been called
    mock_queue.return_value.get.assert_called_once()


@mock.patch('tango.DeviceProxy.__init__')   
def test_listen_with_server_side_polling_async(mock_device_proxy):
    #given
    strategy_reworks = set(interfaceStrategy())
    device_reworks = MockReworker(mock_device_proxy)
    device_reworks.customise_mock_with(is_already_polled,100)
    mock_strategy = strategy_reworks.get_updated_mock()
    listener = Listener(mock_device_proxy,mock_strategy, override_serverside_polling=True)
    #when 
    assert(inspect.iscoroutinefunction(listener.async_listen_for))
    asyncio.run(listener.async_listen_for('attribute'))
    #then
    mock_device_proxy.is_attribute_polled.assert_called_once()
    assert_that(listener.original_server_polling).is_equal_to(100)
    #and I expect the actual polling to be updated
    mock_device_proxy.poll_attribute.assert_called_with('attribute',100)
    assert_that(listener.current_server_side_polling).is_equal_to(100)
    mock_strategy.async_subscribe.assert_called_once()


@mock.patch('tango.DeviceProxy.__init__')  
def test_listener_can_wait_events(mock_device_proxy):
    strategy_reworks = set(interfaceStrategy()).to(generate_multiple_events,['event1'])
    mock_strategy = strategy_reworks.get_updated_mock()
    listener = Listener(mock_device_proxy,mock_strategy, override_serverside_polling=True)
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
    listener = Listener(mock_device_proxy,mock_strategy, override_serverside_polling=True)
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
    listener = Listener(mock_device_proxy,mock_strategy, override_serverside_polling=True)
    #when
    async def async_run():
        async for event in listener.async_get_events_on('attr'):
            assert(listener.listening)
            assert_that(event).is_equal_to(test_events2.pop())
            if len(test_events) == 0:
                listener.stop_listening()
    asyncio.run(async_run())

@mock.patch('tango.DeviceProxy.__init__')  
def test_listener_can_get_elapsed_time_async(mock_device_proxy):
    test_events = ['event1','event2','event3']
    strategy_reworks = set(interfaceStrategy()).to(generate_iterative_events_async,test_events)
    mock_strategy = strategy_reworks.get_updated_mock()
    listener = Listener(mock_device_proxy,mock_strategy, override_serverside_polling=True)
    #when
    async def async_run():
        async for event, elapsed_time in listener.async_get_events_on('attr',get_elapsed_time=True, timeout=10):
            assert_that(elapsed_time).is_equal_to(10)
            if len(test_events) == 0:
                listener.stop_listening()
    asyncio.run(async_run())

@mock.patch('tango.DeviceProxy.__init__')  
def test_listener_can_get_elapsed_time(mock_device_proxy):
    test_events = ['event1','event2','event3']
    strategy_reworks = set(interfaceStrategy()).to(generate_iterative_events,test_events)
    mock_strategy = strategy_reworks.get_updated_mock()
    listener = Listener(mock_device_proxy,mock_strategy, override_serverside_polling=True)
    #when
    for event, elapsed_time in listener.get_events_on('attr',get_elapsed_time=True, timeout=10):
        assert_that(elapsed_time).is_equal_to(10)
        if len(test_events) == 0:
            listener.stop_listening()



# integration tests with an actual device 
@pytest.mark.skip("only run test when test device proxy is deployed")
def test_wait_in_for_loop():
    async def async_run():
        events_received = 0
        device_proxy = await DeviceProxy('sys/tg_test/1')
        strategy = ConsumePeriodically(device_proxy)
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

# integration tests with an actual device 
@pytest.mark.skip("only run test when test device proxy is deployed")
def test_wait_in_for_loop_pushing():
    async def async_run():
        events_received = 0
        device_proxy = await DeviceProxy('sys/tg_test/1')
        strategy = ConsumeImmediately(device_proxy)
        listener = Listener(device_proxy,strategy)
        async for event in listener.async_get_events_on('Status',10):
            if events_received == 0:
                await device_proxy.SwitchStates()
                sleep(0.2)
                await device_proxy.SwitchStates()
                sleep(0.2)
                await device_proxy.SwitchStates()
                sleep(0.8)
            events_received +=1
            logging.info(event)
            if events_received == 3:
                listener.stop_listening()
    asyncio.run(async_run())

@mock.patch('tango.DeviceProxy.__init__')  
def test_query_events_periodic(mock_device_proxy):
    # given a listener that consumes events periodically
    strategy = ConsumePeriodically(mock_device_proxy)
    # and a fake device that emulates a subscription action plus
    # returns events of none and 'test_event' in sequence
    mock_device_proxy.subscribe_event.return_value = 1
    mock_device_proxy.get_events.side_effect = [[],['test_event']]
    spy_strategy = Mock(interfaceStrategy)
    # and a spy that listens to query and subscribe of my strategy
    spy_strategy.query.side_effect =  strategy.query
    spy_strategy.subscribe.side_effect = strategy.subscribe
    listener = Listener(mock_device_proxy,spy_strategy)
    # when I start listening for a fake attribute on the fake device
    listener.listen_for('dummy_attribute')
    # and then I query the listener the first time
    event = listener.query()
    # I expect it to return my query with a None
    assert_that(spy_strategy.query.call_count).is_equal_to(1)
    assert_that(event).is_none()
    # when I query again
    event = listener.query()
    # I expect it to return with the event test_event
    assert_that(spy_strategy.query.call_count).is_equal_to(2)
    assert_that(event).is_equal_to(['test_event'])

class Producer():

    def subscribe(self,callback):
        self.callback = callback

    def push(self, event):
        self.callback(event)


@mock.patch('tango.DeviceProxy.__init__')  
def test_query_events_immediate(mock_device_proxy):
    # given a listener that consumes events immediately
    strategy = ConsumeImmediately(mock_device_proxy)
    # and a fake device that emulates a subscription action 
    # that registers a call back on a mock producer

    mock_producer = Producer()
    def mock_subscribe(*args):
        callback = args[2]
        mock_producer.subscribe(callback)
        return 1

    mock_device_proxy.subscribe_event.side_effect = mock_subscribe
    spy_strategy = Mock(interfaceStrategy)
    # and a spy that listens to query and subscribe of my strategy
    spy_strategy.query.side_effect =  strategy.query
    spy_strategy.subscribe.side_effect = strategy.subscribe
    listener = Listener(mock_device_proxy,spy_strategy)
    # when I start listening for a fake attribute on the fake device
    listener.listen_for('dummy_attribute')
    # and then I query the listener the first time
    event = listener.query()
    # I expect it to return my query with a None
    assert_that(spy_strategy.query.call_count).is_equal_to(1)
    assert_that(event).is_none()
    # if a event is generated on the mock producer
    mock_producer.push('test_event')
    # when I query again
    event = listener.query()
    # I expect it to return with the event test_event
    assert_that(spy_strategy.query.call_count).is_equal_to(2)
    assert_that(event).is_equal_to(['test_event'])
            


    
