
import resources.test_support.subscribing as subscribing
import mock
import logging
from  assertpy import assert_that
from queue import Queue
import pytest

from resources.test_support.subscribing import DevicePool, MessageBoard, Subscription

@mock.patch('resources.test_support.subscribing.DeviceProxy') 
def test_subsription(Mock_device):
    # given a Subscription
    mock_device = Mock_device()
    attr = 'dummy'
    handler = subscribing.MessageHandler()
    s = subscribing.Subscription(mock_device,1,attr,handler)
    # when I unsubscribe
    s.unsubscribe()
    # I expected the device to be called with
    mock_device.unsubscribe_event.assert_called_with(1)

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

def test_message_handler():
    # given a message handler
    m = subscribing.MessageHandler()
    # when I call its handle
    m.handle_event('dummy','args')
    messages = m.tracer.print_messages()
    message1 = 'Handler created'
    message2 = 'event handled'
    assert_that(messages).contains(message1,message2)

def test_events_pusher():
    # given an events puhser
    # and a dummy queue
    # and a dummy handler
    handler = subscribing.MessageHandler()
    queue =  Queue()
    p = subscribing.EventsPusher(queue,handler)
    subscription = 1
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

@mock.patch('resources.test_support.subscribing.Subscription')
@mock.patch('resources.test_support.subscribing.EventsPusher')
@mock.patch('resources.test_support.subscribing.DeviceProxy')
def test_add_subscription_to_message_board(Mock_device,Mock_pusher,Mock_subscription):
    # given a new messageboard
    mock_device = Mock_device.return_value
    subscription_id = 1
    mock_device.subscribe_event.return_value = subscription_id
    mock_pusher = Mock_pusher.return_value
    m = subscribing.MessageBoard()
    # when I add a new subscription
    device_name = 'dummy'
    attr = 'dummy'
    eventType = subscribing.CHANGE_EVENT
    handler = subscribing.MessageHandler()
    m.add_subscription(device_name,attr,handler)
    # I expect a new eventspusher to have been created
    Mock_pusher.assert_called_with(m.board,handler)
    mock_pusher.set_subscription.assert_called_with(subscription_id)
    # I expect a subscription to have been created on device
    # with the events pusher object as the callback object
    mock_device.subscribe_event.assert_called_with(attr,eventType,mock_pusher)
    # I expect the subscriptions to be increased by 1
    Mock_subscription.assert_called_with(mock_device,subscription_id,attr,handler)
    mock_subscription  = Mock_subscription.return_value
    assert_that(m.subscriptions).contains(mock_subscription)
    assert_that(m.subscriptions).is_length(1)

@mock.patch('resources.test_support.subscribing.DeviceProxy')
def test_remove_subscription(Mock_device):
    mock_device = Mock_device.return_value
    subscription_id =1
    mock_device.subscribe_event.return_value = subscription_id
    # given a new messageboard
    m = subscribing.MessageBoard()
    # with three subscriptions
    device_name = 'dummy'
    attr1 = 'dummy1'
    attr2 = 'dummy2'
    attr3 = 'dummy3'
    handler1 = subscribing.MessageHandler()
    handler2 = subscribing.MessageHandler()
    handler3 = subscribing.MessageHandler()
    m.add_subscription(device_name,attr1,handler1)
    m.add_subscription(device_name,attr2,handler2)
    m.add_subscription(device_name,attr3,handler3)
    # when I remove one subscription
    last_subscription = next(iter(m.subscriptions))
    m.remove_subscription(last_subscription)
    # I expect the device to have been unsubscribed
    mock_device.unsubscribe_event.assert_called_with(last_subscription.subscription)
    mock_device.unsubscribe_event.assert_called_with(subscription_id)
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

def bind_subscriber_to_device(device: subscribing.DeviceProxy,
                            producer: Producer):
    device.subscribe_event.side_effect = producer.subscribe


@mock.patch('resources.test_support.subscribing.DeviceProxy')
def test_get_pushed_items(Mock_device):
    mock_device = Mock_device.return_value
    p = Producer()
    bind_subscriber_to_device(mock_device,p)
    # given a messageboard
    # for which I have added a subscription
    m = subscribing.MessageBoard()
    device_name = 'dummy'
    attr = 'dummy1'
    handler = subscribing.MessageHandler()
    m.add_subscription(device_name,attr,handler)
    # when a new event occurs
    event1 = mock.Mock(subscribing.EventData)
    p.push(event1)
    # I expect to get the item from the message 
    item = next(m.get_items())
    assert_that(item.event).is_equal_to(event1)
    assert_that(item.subscription).is_equal_to(0)
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
    
    
    








    

