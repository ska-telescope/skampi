
import resources.test_support.subscribing as subscribing
import mock
import logging
from  assertpy import assert_that
from queue import Queue
import pytest
from typing import List
from collections import deque

from resources.test_support.subscribing import DevicePool, EventItem, MessageBoard, MessageHandler, Subscription, SubscriptionId

@mock.patch('resources.test_support.subscribing.EventsPusher')
@mock.patch('resources.test_support.subscribing.DeviceProxy')
def test_subscription(Mock_device,Mock_events_pusher):
    # given a Subscription
    mock_device = Mock_device()
    mock_device.subscribe_event.return_value = 1
    mock_events = [
        mock.Mock(subscribing.EventData),
        mock.Mock(subscribing.EventData)]
    mock_device.get_events.return_value = mock_events
    board = mock.Mock(Queue)
    attr = 'dummy'
    message_board = mock.Mock(MessageBoard)
    message_board.board = board
    handler = subscribing.MessageHandler(message_board)
    s = subscribing.Subscription(mock_device,attr,handler)
    # when I subsribe by callback
    s.subscribe_by_callback(board)
    # I expect a new eventsPusher to have been created
    Mock_events_pusher.assert_called_with(board,handler)
    mock_events_pusher = Mock_events_pusher.return_value
    mock_events_pusher.set_subscription.assert_called_with(s)
    # I expect a new subscription to have been created
    mock_device.subscribe_event.assert_called_with(attr,subscribing.CHANGE_EVENT,mock_events_pusher)
    # when I unsubscribe
    s.unsubscribe()
    # I expected the device to be called with
    mock_device.unsubscribe_event.assert_called_with(1)
    # when I subsribe by polling a buffer
    s.subscribe_buffer(10)
    # I do not expect a new events pusher
    assert_that(Mock_events_pusher.call_count).is_equal_to(1)
    # I expect a new subscriptuon to have been created
    mock_device.subscribe_event.assert_called_with(attr,subscribing.CHANGE_EVENT,10)\
    # when I then poll the subscription
    results = s.poll()
    result_events = [item.event for item in results]
    result_subscriptions = [item.subscription for item in results]
    result_handlers = [item.handler for item in results]
    assert_that(result_events).is_equal_to(mock_events)
    assert_that(result_subscriptions).is_equal_to([s for _ in  range(2)])
    assert_that(result_handlers).is_equal_to([handler for _ in  range(2)])

def test_tracer():
    # given a tracer
    t = subscribing.Tracer()
    # when I put a message
    message1 = 'this is a test'
    t.message(message1)
    message2 = 'this is a second test'
    t.message(message2)
    # and  print out
    messages = t.print_messages()
    assert_that(messages).contains(message1,message2)

def test_message_handler_from_Event_Item():
    # given a message an event_Item
    # with an handler bounded to it
    board = mock.Mock(MessageBoard)
    m = subscribing.MessageHandler(board)
    mock_event = mock.Mock(subscribing.EventData)
    mock_subscription = mock.Mock(subscribing.Subscription)
    item = EventItem(mock_event,mock_subscription,m)
    handler = item.handler
    # when I call its handle
    handler.handle_event(mock_event, mock_subscription)
    messages = handler.tracer.print_messages()
    message1 = 'Handler created'
    message2 = 'Event received:'
    message3 = 'event handling started'
    message4 = 'event handled'
    assert_that(messages).contains(message1,message2,message3,message4)

def test_events_pusher():
    # given an events puhser
    # and a dummy queue
    # and a dummy handler
    room = mock.Mock(MessageBoard)
    handler = subscribing.MessageHandler(room)
    queue =  Queue()
    p = subscribing.EventsPusher(queue,handler)
    subscription = mock.Mock(subscribing.Subscription)
    subscription.describe.return_value = {"dummy_device_name",'dummy_attr',1}
    p.set_subscription(subscription)
    # when I push an event
    mock_event = subscribing.EventData()
    p.push_event(mock_event)
    # I expect an item to be in the queue
    item = queue.get()
    assert_that(item.event).is_equal_to(mock_event)
    assert_that(item.subscription).is_equal_to(subscription)
    assert_that(item.handler).is_equal_to(handler)

@mock.patch('resources.test_support.subscribing.DeviceProxy')
def test_device_pool(Mock_device):
    mock_device = Mock_device()
    # given a devicePool
    pool = DevicePool()
    # when I get a non existing device
    device = pool.get_device('dummy device')
    # I expect this to be a new instantiation
    assert_that(pool.devices).is_length(1)
    assert_that(pool.devices['dummy device']).is_equal_to(mock_device)
    assert_that(device).is_equal_to(mock_device)
    # then when I call the device with the same name
    device2 = pool.get_device('dummy device')
    assert_that(pool.devices).is_length(1)
    assert_that(device2).is_equal_to(mock_device)
    # and when I add a new device
    device3 = pool.get_device('dummy device2')
    assert_that(pool.devices).is_length(2)
    # as this is a singleton it should always be the same
    assert_that(pool.devices['dummy device2']).is_equal_to(mock_device)
    assert_that(device3).is_equal_to(mock_device)

@mock.patch('resources.test_support.subscribing.EventsPusher')
@mock.patch('resources.test_support.subscribing.DeviceProxy')
def test_add_subscription_to_message_board(Mock_device,Mock_pusher):
    # given a new messageboard
    mock_device = Mock_device.return_value
    id = 1
    mock_device.subscribe_event.return_value = id
    mock_pusher = Mock_pusher.return_value
    m = subscribing.MessageBoard()
    # when I add a new subscription
    device_name = 'dummy'
    attr = 'dummy'
    eventType = subscribing.CHANGE_EVENT
    handler = subscribing.MessageHandler(m)
    s = m.add_subscription(device_name,attr,handler)#
    # I expect a new eventspusher to have been created
    Mock_pusher.assert_called_with(m.board,handler)
    mock_pusher.set_subscription.assert_called_with(s)
    # I expect a subscription to have been created on device
    # with the events pusher object as the callback object
    mock_device.subscribe_event.assert_called_with(attr,eventType,mock_pusher)
    # I expect the subscriptions to be increased by 1
    assert_that(m.subscriptions).is_length(1)

@mock.patch('resources.test_support.subscribing.DeviceProxy')
def test_remove_subscription(Mock_device):
    mock_device = Mock_device.return_value
    mock_device.subscribe_event.side_effect = [0,1,2]
    # given a new messageboard
    m = subscribing.MessageBoard()
    # with three subscriptions
    device_name = 'dummy'
    attr1 = 'dummy1'
    attr2 = 'dummy2'
    attr3 = 'dummy3'
    handler1 = subscribing.MessageHandler(m)
    handler2 = subscribing.MessageHandler(m)
    handler3 = subscribing.MessageHandler(m)
    s1 = m.add_subscription(device_name,attr1,handler1)
    # I expect s to have been subcscribe to device
    assert_that(s1.id).is_equal_to(0)
    s2 = m.add_subscription(device_name,attr2,handler2)
    # I expect s to have been subcscribe to device
    assert_that(s2.id).is_equal_to(1)
    # when I remove one subscription
    s3 = m.add_subscription(device_name,attr3,handler3)
    # I expect s to have been subcscribe to device
    assert_that(s3.id).is_equal_to(2)
    m.remove_subscription(s3)
    # I expect the device to have been unsubscribed
    mock_device.unsubscribe_event.assert_called_with(2)
    # and the nr of subscriptions to be 1 less
    assert_that(m.subscriptions).is_length(2)
    # when I remove all subscriptions
    m.remove_all_subcriptions()
    # I expect all the subscriptions to have been undone
    assert_that(mock_device.unsubscribe_event.call_count).is_equal_to(3)
    assert_that(m.subscriptions).is_empty()

class Producer():

    def subscribe(self, attr: str,
                    eventType: subscribing.EventType,
                    eventpusher: subscribing.EventsPusher) -> int:
        self.pusher = eventpusher
        return 0

    def push(self, event: subscribing.EventData):
        self.pusher.push_event(event)

class PolledProducer():

    def __init__(self) -> None:
        self.return_buffer = deque()

    def subscribe(self, attr: str,
                    eventType: subscribing.EventType,
                    buffer: int) -> int:
        return 0

    def get_events(self,id: int) -> List:
        if self.return_buffer:
            return self.return_buffer.pop()
        else:
            return []

    def push(self, event: subscribing.EventData):
        self.return_buffer.append([event])

def bind_subscriber_to_device(device: subscribing.DeviceProxy,
                            producer: Producer):
    device.subscribe_event.side_effect = producer.subscribe

def bind_subscriber_to_polled_device(device: subscribing.DeviceProxy,
                            producer: PolledProducer):
    device.subscribe_event.side_effect = producer.subscribe
    device.get_events.side_effect = producer.get_events

@mock.patch('resources.test_support.subscribing.DeviceProxy')
def test_get_pushed_items_polled(Mock_device):
    mock_device = Mock_device.return_value
    p = PolledProducer()
    bind_subscriber_to_polled_device(mock_device,p)
    # given a messageboard
    # for which I have added a subscription based on polling
    m = subscribing.MessageBoard()
    device_name = 'dummy'
    attr = 'dummy1'
    handler = subscribing.MessageHandler(m)
    subscription = m.add_subscription(device_name,attr,handler,polling = True)
    # when a new event occurs
    event1 = mock.Mock(subscribing.EventData)
    p.push(event1)
    # I expect to get the item from the message
    item = next(m.get_items())
    assert_that(item.event).is_equal_to(event1)
    assert_that(item.subscription).is_equal_to(subscription)
    assert_that(item.handler).is_equal_to(handler)
    # And when I push it again I expect to get another
    event2 = mock.Mock(subscribing.EventData)
    p.push(event2)
    item = next(m.get_items())
    assert_that(item.event).is_equal_to(event2)
    # thereafter I expect a timeout waiting for event
    with pytest.raises(subscribing.EventTimedOut):
        next(m.get_items(0.1))
    # if I remove all the subscription
    m.remove_all_subcriptions()
    # I expect iteration to stop
    with pytest.raises(StopIteration):
        next(m.get_items())












