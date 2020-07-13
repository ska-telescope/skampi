from resources.test_support.waiting import Listener,ConsumePeriodically,\
    interfaceStrategy,ConsumeImmediately,ListenerTimeOut, Gatherer,\
    HandeableEvent
from tango import EventData
from tango.asyncio import DeviceProxy
import tango
import asyncio
import mock
import logging
from time import sleep
from mock import Mock,call
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


@pytest.fixture()
def fixture_for_two_listeners_immediate():
    return build_me_a_gatherer(2,ConsumeImmediately)

def build_me_a_gatherer(nr_of_devices, Strategy):

    class Binder():

        def __init__(self,producer):
            self.producer = producer

        def bind_subscription(self,*args):
            callback = args[2]
            self.producer.subscribe(callback)


    output = {}
    # setup a series of mock_instantiations to be delivered
    # for each call
    for device_nr in range(nr_of_devices):
        the_mock = Mock(tango.DeviceProxy)     
        the_strategy = Strategy(the_mock)
        strategy_spy = Mock(Strategy)
        # bind the spy to real implementations
        strategy_spy.query.side_effect = the_strategy.query
        strategy_spy.subscribe.side_effect = the_strategy.subscribe
        p = Producer()
        # change the effect of subscription to bind to a mock 
        # producer 
        the_mock.producer = p
        binder = Binder(p)
        the_mock.subscribe_event.side_effect = binder.bind_subscription
        the_listener = Listener(the_mock,strategy_spy)
        output[f'producer{device_nr+1}'] = p
        output[f'mock_device_proxy_instance{device_nr+1}'] = the_mock
        output[f'listener{device_nr+1}'] = the_listener
        output[f'strategy{device_nr+1}'] = strategy_spy
    return output

def get_mock_event(event,attr):
    event = Mock(EventData,name=event)
    event.attr_name = attr
    event.event = event
    return event

def test_listen_as_a_group(fixture_for_two_listeners_immediate):
    # given 2 event listeners listening for events
    # coming from two mock devices that emulate
    # a subscription and two producers that create independant events
    the_fixture = fixture_for_two_listeners_immediate

    p1 = the_fixture['producer1']
    p2 = the_fixture['producer2']

    mock_events = []
    for i in range(4):
        event = get_mock_event(f'event{i}','attr')
        mock_events.append(event)

    def push_new_events(i):
        if i == 4:
            return
        elif (i % 2) == 0:
            p1.push(mock_events[i])
        else:
            p2.push(mock_events[i])
    # then when
    gatherer = Gatherer()
    listener1 = the_fixture['listener1']
    listener2 = the_fixture['listener2']
    handler1 = Mock(name='handler1')
    handler2 = Mock(name='handler2')
    gatherer.bind(listener1,handler1,'attr')
    gatherer.bind(listener2,handler2,'attr')
    gatherer.start_listening()
    start_event = get_mock_event('event_start','attr')
    p1.push(start_event)
    for i,handeable_event in enumerate(gatherer.get_events(1)):
        handeable_event.handle()
        push_new_events(i)

    # I expect handler 1 to have been called two times with
    #  event1 and event2 
    # and handler 2 to have been called two times with event 3 and
    # event 4
    handler1.assert_has_calls([
        call(start_event),
        call(mock_events[0]),
        call(mock_events[2]),

    ])
    handler2.assert_has_calls([
        call(mock_events[1]),
        call(mock_events[3])
    ])
    for listener,binding in gatherer.listeners.items():
        logging.debug(f'messages on {listener}:\n'
                     f'{binding["tracer"].print_messages()}')

def test_listen_as_a_group_multiple_attr(fixture_for_two_listeners_immediate):
    # given 2 event listeners listening for events
    # coming from two mock devices that emulate
    # a subscription and two producers that create independant events
    the_fixture = fixture_for_two_listeners_immediate

    p1 = the_fixture['producer1']
    p2 = the_fixture['producer2']

    mock_events = []
    for i in range(4):
        event = get_mock_event(f'event{i}',f'attr{i}')
        mock_events.append(event)

    def push_new_events(i):
        if i == 4:
            return
        elif (i % 2) == 0:
            p1.push(mock_events[i])
        else:
            p2.push(mock_events[i])
    # then when
    gatherer = Gatherer()
    listener1 = the_fixture['listener1']
    listener2 = the_fixture['listener2']
    handler0 = Mock(name='handler0')
    handler1 = Mock(name='handler1')
    handler2 = Mock(name='handler2')
    gatherer.bind(listener1,handler0,'attr_start')
    gatherer.bind(listener1,handler1,
        'attr0',
        'attr2')
    gatherer.bind(listener2,handler2,
        'attr1',
        'attr3'
    )
    gatherer.start_listening()
    start_event = get_mock_event('event_start','attr_start')
    p1.push(start_event)
    for i,handeable_event in enumerate(gatherer.get_events(1)):
        handeable_event.handle()
        push_new_events(i)

    # I expect handler 1 to have been called two times with
    #  event1 and event2 
    # and handler 2 to have been called two times with event 3 and
    # event 4
    handler0.assert_has_calls([
        call(start_event)
    ])
    handler1.assert_has_calls([
        call(mock_events[0]),
        call(mock_events[2]),

    ])
    handler2.assert_has_calls([
        call(mock_events[1]),
        call(mock_events[3])
    ])
    for listener,binding in gatherer.listeners.items():
        logging.debug(f'messages on {listener}:\n'
                     f'{binding["tracer"].print_messages()}')
  
def test_handeable_event():
    #given a handeable_event
    handler = Mock(name='handler')
    event = Mock(name='event')
    elapsed_time = Mock(name='elapsed_time')
    h = HandeableEvent(
        handler,
        event,
        elapsed_time
    )
    # when I call the handleable event without elapsed_time
    h.handle()
    handler.assert_called_with(event)
    # when I call the handleable event with elapsed_time
    h.handle(supply_elapsed_time=True)
    handler.assert_called_with(event,elapsed_time)
    # when I call the handler with extra args
    h.handle('arg1','arg2')
    handler.assert_called_with(event,'arg1','arg2')
    # when I call the handler with extra args and with elapsed_time
    h.handle('arg1','arg2',supply_elapsed_time=True)
    handler.assert_called_with(event,elapsed_time,'arg1','arg2')

    class FakeHandler():
        def handle_event(self,*args,**kwargs):
            handler(*args,**kwargs)

    handler_object = FakeHandler()
    h = HandeableEvent(
        handler_object,
        event,
        elapsed_time
    )
    # when I call the handeable event without elapsed_time
    h.handle()
    handler.assert_called_with(event)
    # when I call the handleable event with elapsed_time
    h.handle(supply_elapsed_time=True)
    handler.assert_called_with(event,elapsed_time)
    # when I call the handler with extra args
    h.handle('arg1','arg2')
    handler.assert_called_with(event,'arg1','arg2')
    # when I call the handler with extra args and with elapsed_time
    h.handle('arg1','arg2',supply_elapsed_time=True)
    handler.assert_called_with(event,elapsed_time,'arg1','arg2')
