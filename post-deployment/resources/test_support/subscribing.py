import sys
from functools import reduce
from datetime import datetime
from tango import device_proxy
sys.path.append('/home/tango/skampi/post-deployment/')
from tango import DeviceProxy,EventType,EventData
CHANGE_EVENT = EventType.CHANGE_EVENT
from queue import Empty, Queue
from time import sleep
from collections import namedtuple
from resources.test_support.waiting import Listener, listen_for
# types
from typing import Tuple, List, Callable, Dict

TracerMessageType = Tuple[datetime,str]
TracerMessage = namedtuple('TracerMessage',['time','message'])
SubscriptionId: Tuple[DeviceProxy, int] = namedtuple('SubscriptionId',['device','id'])

class Tracer():
    ''' 
    class used to record messages at specific events
    '''
    def __init__(self,message:str=None) -> None:
        if message is None:
            self.messages: List[TracerMessage] = []
        else:
            self.messages = []
            self.message(message)

    def message(self, message: str) -> None:
        tracerMessage = TracerMessage(datetime.now(),message)
        self.messages.append(tracerMessage)

    def print_messages(self) -> str:
        str_messages = [f'{x.time.isoformat()}: {x.message}' for x in self.messages]
        reduced = reduce(lambda x,y: f'{x}\n{y}',str_messages)
        return f'\n{reduced}'

class MessageHandler():

    tracer: Tracer

    def __init__(self, board) -> None:
        self.tracer = Tracer(f"Handler created")
        self.board = board
        self.cancel_at_next_event = False

    def _print_event(self,event) -> str:
        device_name = event.device.name()
        attr_name = event.attr_value.name
        attr_value = str(event.attr_value.value)
        time = event.attr_value.time.isoformat()
        self.tracer.message(f'Event received: {device_name}.{attr_name} is recorded to be {attr_value} at {time}')

    def handle_event(self, event: EventData, id: SubscriptionId) -> None:
        if self.cancel_at_next_event:
            self.unsubscribe(id)
        self.tracer.message("event handled")
        self.board.task_done()

    def unsubscribe(self,id):
        self.board.remove_subscription(id)
        self.tracer.message("Subscription removed from message board, no more messages expected")

    def handle_timedout(self,
            device: DeviceProxy,
            attr: str,print_header=True) -> str:
        header = ''
        if print_header:
            header = f'\n Device: {device.name()} Attribute: {attr}'
        tracer = self.tracer.print_messages()
        return f'{header}{tracer}'

    def supress_timeout(self) -> bool:
        return False

    def replay(self) -> str:
        return self.tracer.print_messages()

    def print_event(self, event: EventData) -> str:
        device_name = event.device.name()
        attr_name = event.attr_value.name
        attr_value = str(event.attr_value.value)
        time = event.attr_value.time.isoformat()
        message = f'\n{time:<30}{device_name:<40}{attr_name:<10}{attr_value:<10}'
        return message

class Subscription():
    '''
    class that ties a subcription to a tango device
    in order to keep record of subcriptions
    '''
    def __init__(self,device: DeviceProxy,
                    subscription: SubscriptionId,
                    attr: str,
                    handler: MessageHandler) -> None:
        self.device = device
        self.subscription = subscription
        self.handler = handler
        self.attr = attr

    def handle_timedout(self,*args)-> str:
        return self.handler.handle_timedout(
            self.device,
            self.attr,
            *args)
    
    def supress_timeout(self) -> bool:
        return self.handler.supress_timeout()

    def unsubscribe(self):
        self.device.unsubscribe_event(self.subscription.id)

SubscriptionType = Dict[SubscriptionId, Subscription]
EventItemType = Tuple[EventData,SubscriptionId,MessageHandler]
EventItem:EventItemType = namedtuple('EventItem',['event','subscription','handler'])

class EventsPusher():
    '''
    object that pushes events onto a given buffer when called by a push event
    '''
    def __init__(self, queue: "Queue[EventItem]", handler:MessageHandler=None) -> None:
        self.queue = queue
        self.handler = handler
        self.first_event = None
        self.subscription = None
        self.stash = []

    def event_pushed_unidempotently(self) -> bool:
        # this means an event has been pushed but the ojbect has not been fully
        # defined
        return self.subscription is None

    def events_stashed_from_idempotent_calls(self) -> bool:
        return self.stash

    def stash_event(self, event: EventData) -> None:
        self.stash.append(event)

    def clean_stashed_events(self, subscription: SubscriptionId) -> None:
        for event in self.stash:
            item = EventItem(event,subscription,self.handler)
            self.queue.put(item)

    def push_event(self, event: EventData ) -> None:
        '''
        called by callback to set an event of a single type and attr
        and its corresponding subscription id from a device
        onto a shared buffer
        '''
        if self.event_pushed_unidempotently():
            # always keep record of the first event for diagnostic purposes
            self.first_event = event
            self.stash_event(event)
        else:
            item = EventItem(event,self.subscription,self.handler)
            self.queue.put(item)

    def set_subscription(self, subscription: SubscriptionId) -> None:
        '''
        set immediately after an subscription to tie the id to the event when placed
        on a buffer
        '''
        # in cases an 
        if self.events_stashed_from_idempotent_calls:
            self.clean_stashed_events(subscription) 
        self.subscription = subscription


class DevicePool():
    '''
    class that ensure the same device proxy is used
    for multiple subscriptions
    '''
    def __init__(self) -> None:
        self.devices = {}

    def get_device(self,device_name) -> DeviceProxy:
        if device_name in self.devices.keys():
            return self.devices[device_name]
        else:
            device = DeviceProxy(device_name)
            self.devices[device_name] = device
            return device  

class EventTimedOut(Empty):

    def __init__(self,exception: Empty, message: str) -> None:
        args = (message,exception.args)
        super(EventTimedOut,self).__init__(args)


class MessageBoard():
    '''
    encapsulates a buffer containing events that gets places by events pushers
    onto it. Also keeps track of subscriptions and allow adding and removing of them 
    '''

    def __init__(self) -> None:
        self.subscriptions: SubscriptionType = {}
        self.board: "Queue[EventItem]" = Queue()
        self.devicePool = DevicePool()
        self.archived_subscriptions = {}

    def add_subscription(self,
                        device_name: str,
                        attr: str,
                        handler:MessageHandler=None) -> Subscription:
        '''
        adds and dispatches a new subscription based on a device name and attr
        Note this will immediately initiate the pushing of events on the buffer
        '''
        eventsPusher = EventsPusher(self.board,handler)
        device = self.devicePool.get_device(device_name)
        id = device.subscribe_event(attr,CHANGE_EVENT ,eventsPusher)
        subscription_id = SubscriptionId(device,id)
        eventsPusher.set_subscription(subscription_id)
        new_subscription = Subscription(device,subscription_id,attr,handler)
        self.subscriptions[subscription_id] = new_subscription
        return new_subscription

    def remove_all_subcriptions(self) -> None:
        for id,subscription in self.subscriptions.items():
            subscription.unsubscribe()
            self.archived_subscriptions[id] = subscription
        self.subscriptions = {}

    def remove_subscription(self,subscription_id: SubscriptionId) -> None:
        subscription = self.subscriptions.pop(subscription_id)
        subscription.unsubscribe()
        self.archived_subscriptions[subscription_id] = subscription

    def _get_printeable_timedout(self,timeout: float) -> str:
        waits = [
            subscription.handle_timedout() for subscription in self.subscriptions.values()
        ]
        aggregate_waits = reduce(lambda x,y: f'{x}\n{y}',waits)
        message = f'event timed out after {timeout} seconds\n'\
                  f'remaining subscriptions:'\
                  f'{aggregate_waits}'
        return message

    def replay_subscription(self,id: SubscriptionId) -> str:
        subscription = self.archived_subscriptions[id]
        device = subscription.device
        attr = subscription.attr
        handler_logs = subscription.handler.replay()
        return f'subscription[{device}:{attr}]{handler_logs}\n' 


    def replay_subscriptions(self) -> str:
        logs = [self.replay_subscription(id) for id in self.archived_subscriptions.keys()]
        reduced = reduce(lambda x,y: f'{x}\n{y}',logs)
        return f'\n\n{reduced}'

    def get_items(self,timeout:float = None) -> EventItem:
        while self.subscriptions:
            try:
                item = self.board.get(timeout=timeout)
            except Empty as e:
                if all(s.supress_timeout() for s in self.subscriptions.values()):
                    self.remove_all_subcriptions()
                    return StopIteration()
                else:
                    message = self._get_printeable_timedout(timeout)
                    self.remove_all_subcriptions()
                    exception = EventTimedOut(e,message)
                    raise exception
            yield item

    def task_done(self):
        self.board.task_done()
            

HandlingType = Tuple[MessageHandler,Tuple]
Handling = namedtuple('Handling',['handler','args'])



