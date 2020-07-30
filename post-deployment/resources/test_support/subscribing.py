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
from typing import Tuple, List, Callable

TracerMessageType = Tuple[datetime,str]
TracerMessage = namedtuple('TracerMessage',['time','message'])

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

    def __init__(self) -> None:
        self.tracer = Tracer(f"Handler created")

    def handle_event(self,*args):
        self.tracer.message("event handled")

    def handle_timedout(self,
            device: DeviceProxy,
            attr: str,print_header=True) -> str:
        header = ''
        if print_header:
            header = f'\n Device: {device.name} Attribute: {attr}'
        tracer = self.tracer.print_messages()
        return f'{header}{tracer}'


class Subscription():
    '''
    class that ties a subcription to a tango device
    in order to keep record of subcriptions
    '''
    def __init__(self,device: DeviceProxy,
                    subscription: int,
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

    def unsubscribe(self):
        self.device.unsubscribe_event(self.subscription)

EventItemType = Tuple[EventData,Subscription,MessageHandler]
EventItem:EventItemType = namedtuple('EventItem',['event','subscription','handler'])

class EventsPusher():
    '''
    object that pushes events onto a given buffer when called by a push event
    '''
    def __init__(self, queue: "Queue[EventItem]", handler:MessageHandler=None) -> None:
        self.queue = queue
        self.handler = handler

    def push_event(self, event: EventData ) -> None:
        '''
        called by callback to set an event of a single type and attr
        and its corresponding subscription id from a device
        onto a shared buffer
        '''
        item = EventItem(event,self.subscription,self.handler)
        self.queue.put(item)

    def set_subscription(self, subscription: int) -> None:
        '''
        set immediately after an subscription to tie the id to the event when placed
        on a buffer
        '''
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
        super().__init__(args)


class MessageBoard():
    '''
    encapsulates a buffer containing events that gets places by events pushers
    onto it. Also keeps track of subscriptions and allow adding and removing of them 
    '''

    def __init__(self) -> None:
        self.subscriptions = set()
        self.board: "Queue[EventItem]" = Queue()
        self.devicePool = DevicePool()

    def add_subscription(self,
                        device_name: str,
                        attr: str,
                        handler:MessageHandler=None) -> None:
        '''
        adds and dispatches a new subscription based on a device name and attr
        Note this will immediately initiate the pushing of events on the buffer
        '''
        eventsPusher = EventsPusher(self.board,handler)
        device = self.devicePool.get_device(device_name)
        subscription = device.subscribe_event(attr,CHANGE_EVENT ,eventsPusher)
        eventsPusher.set_subscription(subscription)
        self.subscriptions.add(Subscription(device,subscription,attr,handler))

    def remove_all_subcriptions(self) -> None:
        for subscription in self.subscriptions:
            subscription.unsubscribe()
        self.subscriptions = set()

    def remove_subscription(self,subscription: int) -> None:
        subscription.unsubscribe()
        self.subscriptions.remove(subscription)

    def _get_printeable_timedout(self,timeout: float) -> str:
        waits = [
            subscription.handle_timedout() for subscription in self.subscriptions
        ]
        aggregate_waits = reduce(lambda x,y: f'{x}\n{y}',waits)
        message = f'event timed out after {timeout} seconds\n'\
                  f'remaining subscriptions:'\
                  f'{aggregate_waits}'
        return message

    def get_items(self,timeout:float = None) -> EventItem:
        while self.subscriptions:
            try:
                item = self.board.get(timeout=timeout)
            except Empty as e:
                message = self._get_printeable_timedout(timeout)
                exception = EventTimedOut(e,message)
                raise exception
            yield item

HandlingType = Tuple[MessageHandler,Tuple]
Handling = namedtuple('Handling',['handler','args'])

def set_up_messages(spec: List[Tuple[str,str]],
                    handling: Handling) -> MessageBoard:
    '''
    factory for creating a messageboard based on a list of tuples
    mapping devices names to attributes
    '''
    board = MessageBoard()
    for device_name,attr, in spec:
        Handler,args = (handling.handler,handling.args)
        handler = Handler(*args)
        board.add_subscription(device_name,attr,handler)
    return board

class HandleMessageSequence(MessageHandler):
    '''
    handles s set of events and stops the subscription process when
    a maximum nr of events are  recieved
    '''

    def __init__(self,seq: int) -> None:
        super().__init__()
        self.max_seq = seq
        self.events = []
        

    def handle_event(self, event: EventData, id: int, board: MessageBoard) -> None:
        self.events.append(event)
        if len(self.events) >= self.max_seq:
            board.remove_subscription(id)
        super().handle_event()

