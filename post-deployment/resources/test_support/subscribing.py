
import sys
from functools import reduce
from datetime import datetime
from tango import DeviceProxy,EventType,EventData,DeviceAttribute
from contextlib import contextmanager
from ska.base.control_model import ObsState
from datetime import datetime
from queue import Empty, Queue
from time import sleep
from collections import namedtuple
from concurrent import futures
import threading
import re
import enum
# types
from typing import Tuple, List, Set


TracerMessageType = Tuple[datetime,str]
TracerMessage = namedtuple('TracerMessage',['time','message'])
SubscriptionId: Tuple[DeviceProxy, int] = namedtuple('SubscriptionId',['device','id'])

CHANGE_EVENT = EventType.CHANGE_EVENT
sys.path.append('/home/tango/skampi/post-deployment/')


## helpers for reading an event
class PointingState(enum.IntEnum):
    """
    Pointing state of the dish
    """
    READY = 0
    SLEW = 1
    TRACK = 2
    SCAN = 3

def get_attr_value_as_str(attr: DeviceAttribute) -> str:
    if attr.name == 'obsState' :
        return str(ObsState(attr.value))
    if attr.name == 'obsstate' :
        return str(ObsState(attr.value))
    if attr.name == 'dishpointingstate':
        return str(PointingState(attr.value))
    if attr.name == 'dishPointingstate':
        return str(PointingState(attr.value)) 
    if attr.name == 'pointingstate':
        return str(PointingState(attr.value)) 
    if attr.name == 'pointingState': 
        return str(PointingState(attr.value)) 
    if attr.name == 'dishPointingState':
        return str(PointingState(attr.value)) 
    else:
        return str(attr.value)
    #TODO add extractions for other types of attributes

def get_device_name(event: EventData) -> str:
    return event.device.name()
    
def get_attr_name(event: EventData) -> str:
    if event.attr_value is None:
        return  re.search(r"\w*(?<=$)", event.attr_name).group(0) 
    return event.attr_value.name

def get_attr_value_str(event: EventData) -> str:
    if event.attr_value is None:
        if event.err:
            return str(event.errors)
    else:
        return get_attr_value_as_str(event.attr_value)

def get_date_lodged(event: EventData,init_date: datetime = datetime.now()) -> datetime:
    if event.attr_value is None:
        return init_date
    return event.attr_value.time.todatetime()

def get_date_lodged_isoformat(event: EventData,init_date: datetime = datetime.now()) ->str:
    if event.attr_value is None:
        return init_date.isoformat()
    return event.attr_value.time.isoformat()

def describe_event(event: EventData,init_date: datetime = datetime.now()) -> Tuple[str,str,str,str]:
    device_name = get_device_name(event)
    attr = get_attr_name(event)
    date = get_date_lodged_isoformat(event,init_date)
    value = get_attr_value_str(event)
    return device_name,attr,value,date

def upack_event(event: EventData,init_date: datetime = datetime.now()) -> Tuple[str,str,str,datetime]:
    device_name = get_device_name(event)
    attr = get_attr_name(event)
    date = get_date_lodged(event,init_date)
    value = get_attr_value_str(event)
    return device_name,attr,value,date





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
        self.tracer = Tracer(f"Handler created: {self.describe_self()}")
        self.board = board
        self.cancel_at_next_event = False
        self.cancelled_by_base_class= False
        self.current_subscription = None
        self.second_event_received = False
        self.first_event_received = False
        self.annotate_print_out = ''

    def describe_self(self) -> str:
        return ''

    def _get_attr_value_as_str(self, attr: DeviceAttribute) -> str:
        return get_attr_value_as_str(attr)

    def _get_attr_value_as_int(self, attr: DeviceAttribute) -> int:
        #TODO
        pass

    def _get_attr_value_as_list(self, attr: DeviceAttribute) -> List:
        #TODO
        pass

    def _describe_event(self,event: EventData) -> Tuple[str,str,str,str]:
        return describe_event(event)

    def _print_event(self,event: EventData) -> str:
        device_name,attr_name,attr_value,time = self._describe_event(event)
        self.tracer.message(f'Event received: {device_name}.{attr_name} is recorded to be {attr_value} at {time}')

    def _pre_handling(self, event: EventData, subscription: object):
        self.tracer.message("event handling started")
        self._update_event_handler_state()
        self._print_event(event)
        if self.cancel_at_next_event:
            self.unsubscribe(subscription)
            self.cancelled_by_base_class = True

    def _update_event_handler_state(self):
        if not self.first_event_received:
            self.first_event_received = True
        else:
            if not self.second_event_received:
                self.second_event_received = True

    def _post_handling(self):
        self.tracer.message("event handled")
        self.board.task_done()
        

    @contextmanager
    def handle_context(self,event: EventData, subscription: object) -> None:
        self._pre_handling(event,subscription)
        yield
        self._post_handling()

    def handle_event(self,event: EventData, subscription: object,*args) -> None:
        with self.handle_context(event,subscription):
            pass

    def load_event(self,event: EventData, subscription: object) -> None:
        self.current_event = event
        self.current_subscription = subscription

    def unsubscribe_all(self):
        self.board.remove_all_subcriptions()
        self.tracer.message(f"All subscriptions removed from message board by handler, no more messages expected")

    def unsubscribe(self,subscription: object):
        if self.cancelled_by_base_class:
            return
        else:
            self.board.remove_subscription(subscription)
            device_name,attr,id = subscription.describe()
            self.tracer.message(f"Subscription {device_name}.{attr}:{id} removed from message board, no more messages expected")

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

    def print_event(self,event: EventData,ignore_first=False) -> str:
        if ignore_first:
            if not self.second_event_received:
                return ''
        device_name,attr_name,attr_value,time = upack_event(event)
        message = f'{device_name:<40}{attr_name:<20}{attr_value:<10}{self.annotate_print_out}'
        self.board.log(message,time)
        return message


EventItemType = Tuple[EventData,SubscriptionId,MessageHandler]

class EventItem():

    event: EventData
    subscription: object
    handler: MessageHandler

    def __init__(self,event: EventData, subscription: object, handler: MessageHandler) -> None:
        self.event = event
        self.subscription = subscription
        self.handler = handler
        self.init_date = datetime.now()

    def get_date_lodged(self) -> datetime:
        return self.event.attr_value.time.todatetime()

    def get_date_init(self) -> datetime:
        return self.init_date

    def get_device_name(self) -> str:
        return self.event.device.name()
        
    def get_attr_name(self) -> str:
        if self.event.attr_value is None:
            return  re.search(r"\w*(?<=$)", self.event.attr_name).group(0) 
        return self.event.attr_value.name

    def get_attr_value_str(self) -> str:
        if self.event.attr_value is None:
            if self.event.err:
                return str(self.event.errors)
        else:
            return get_attr_value_as_str(self.event.attr_value)

    def get_date_lodged_isoformat(self) ->str:
        if self.event.attr_value is None:
            return self.init_date.isoformat()
        return self.event.attr_value.time.isoformat()

    def describe(self) -> Tuple[str,str,str,str]:
        return describe_event(self.event,self.init_date)


class EventsPusher():
    '''
    object that pushes events onto a given buffer when called by a push event
    '''
    def __init__(self, queue: "Queue[EventItem]", handler:object=None) -> None:
        self.queue = queue
        self.handler = handler
        self.first_event = None
        self.subscription = None
        self.stash = []
        self.tracer = Tracer()

    def event_pushed_unidempotently(self) -> bool:
        # this means an event has been pushed but the ojbect has not been fully
        # defined
        return self.subscription is None

    def events_stashed_from_idempotent_calls(self) -> bool:
        return self.stash

    def stash_event(self, event: EventData) -> None:
        self.stash.append(event)

    def clean_stashed_events(self, subscription: object) -> None:
        for event in self.stash:
            item = EventItem(event,subscription,self.handler)
            self.queue.put(item)
            self.tracer.message(f'event from stashed events placed on buffer')

    def push_event(self, event: EventData ) -> None:
        '''
        called by callback to set an event of a single type and attr
        and its corresponding subscription id from a device
        onto a shared buffer
        '''

        if event.attr_value is None:
            self.tracer.message(f'event pushed without a Device attribute {event}')
        else:
            self.tracer.message(f'new event received: {event.attr_value.name} '
                            f'is {get_attr_value_as_str(event.attr_value)} on device '
                            f'{event.device.name()}')
        if self.event_pushed_unidempotently():
            # always keep record of the first event for diagnostic purposes
            self.tracer.message(f'event pushed idempotently will be stashed until subscription known')
            self.first_event = event
            self.stash_event(event)
        else:
            item = EventItem(event,self.subscription,self.handler)
            self.tracer.message(f'new event placed on buffer')
            self.queue.put(item)

    def set_subscription(self, subscription: object) -> None:
        '''
        set immediately after an subscription to tie the id to the event when placed
        on a buffer
        '''
        # in cases an 
        if self.events_stashed_from_idempotent_calls:
            self.clean_stashed_events(subscription) 
        self.subscription = subscription
        device_name,attr,id = subscription.describe()
        self.tracer.message(f'subscription {device_name}.{attr}:{id} set on pusher')

class Subscription():
    '''
    class that ties a subcription to a tango device
    in order to keep record of subcriptions
    '''
    def __init__(self,device: DeviceProxy,
                    attr: str,
                    handler: MessageHandler,
                    master: bool = False) -> None:
        self.device = device
        self.id = None
        self.handler = handler
        self.attr = attr
        self.polled = False
        self.tracer = Tracer()
        self.master = master
        self.eventsPusher = None

    def handle_timedout(self,*args)-> str:
        return self.handler.handle_timedout(
            self.device,
            self.attr,
            *args)

    def describe(self) -> Tuple[str,str,int]:
        device_name = self.device.name()
        attr = self.attr
        id = self.id
        return device_name,attr,id
    
    def poll(self) -> List[EventItem]:
        assert self.polled
        events = self.device.get_events(self.id)
        return [EventItem(event,self,self.handler) for event in events]

    def supress_timeout(self) -> bool:
        return self.handler.supress_timeout()

    def unsubscribe(self):
        assert self.id is not None
        try:
            self.device.unsubscribe_event(self.id)
        except KeyError:
            self.tracer.message(f'NOTE: subscription with id {self.id} is aready unsubscribed on {self.device} for attr {self.attr}')
            return
        self.tracer.message(f'subscription with id {self.id} removed from {self.device} for attr {self.attr}')

    def subscribe_by_callback(self, board: Queue) -> None:
        eventsPusher = EventsPusher(board,self.handler)
        self.id = self.device.subscribe_event(self.attr,CHANGE_EVENT ,eventsPusher)
        self.tracer.message(f'new subcription with id {self.id} created on {self.device} for attr {self.attr} with callback')
        eventsPusher.set_subscription(self)
        self.eventsPusher = eventsPusher

    def subscribe_buffer(self, buffersize=100) -> None:
        self.id = self.device.subscribe_event(self.attr,CHANGE_EVENT ,buffersize)
        self.tracer.message(f'new subcription with id {self.id} created on {self.device} for attr {self.attr} with callback')
        self.polled = True


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

LogMessage: Tuple[datetime,str] = namedtuple('LogMessage',['time','log'])

class LogBook():

    def __init__(self):
        
        self.messages: List[Tuple[LogMessage]] = []
        self.logbook_lock = threading.Lock()

    def log(self, message: str,timestamp: datetime = None):
        with self.logbook_lock:
            if timestamp is None:
                timestamp = datetime.now()
            logMessage = LogMessage(timestamp,message)
            self.messages.append(logMessage)

    def read(self) -> str:
        self.messages.sort(key=lambda log: log.time)
        logs = [f'{m.time.isoformat():<30}{m.log}' for m in self.messages]
        return reduce(lambda x,y: f'{x}\n{y}',logs)


class MessageBoard():
    '''
    encapsulates a buffer containing events that gets places by events pushers
    onto it. Also keeps track of subscriptions and allow adding and removing of them 
    '''

    def __init__(self) -> None:
        self.subscriptions: Set[Subscription] = set()
        self.board: "Queue[EventItem]" = Queue()
        self.devicePool = DevicePool()
        self.archived_subscriptions: Set[Subscription] = set()
        self.polling = threading.Event()
        self.tracer = Tracer()
        self.logbook = []
        self.logBook = LogBook()

    def log(self,message: str,time: datetime = None) -> None:
        self.logBook.log(message,time)

    def play_log_book(self) -> str:
        return self.logBook.read()

    def add_subscription(self,
                        device_name: str,
                        attr: str,
                        handler:MessageHandler,
                        polling: bool = False) -> Subscription:
        '''
        adds and dispatches a new subscription based on a device name and attr
        Note this will immediately initiate the pushing of events on the buffer
        '''
        device = self.devicePool.get_device(device_name)
        new_subscription = Subscription(device,attr,handler)
        if polling:
            new_subscription.subscribe_buffer()
            device_name,attr,id = new_subscription.describe()
            self.tracer.message(f'new subscription {device_name}.{attr}:{id} added as polled')
        else:
            new_subscription.subscribe_by_callback(self.board)
            device_name,attr,id = new_subscription.describe()
            self.tracer.message(f'new subscription {device_name}.{attr}:{id} added as polled')
        assert new_subscription not in self.subscriptions
        self.subscriptions.add(new_subscription)
        return new_subscription

    def remove_all_subcriptions(self) -> None:
        while self.subscriptions:
            subscription = self.subscriptions.pop()
            subscription.unsubscribe()
            self.archived_subscriptions.add(subscription)
        self.tracer.message(f'all subscriptions (len = {len(self.archived_subscriptions)}) removed and archived')

    def remove_subscription(self,subscription: Subscription) -> None:
        subscription.unsubscribe()
        self.archived_subscriptions.add(subscription)
        self.subscriptions.remove(subscription)
        device_name,attr,id = subscription.describe()
        self.tracer.message(f'subscription {device_name}.{attr}:{id} removed and archived')
        

    def _get_printeable_timedout(self,timeout: float) -> str:
        waits = [
            subscription.handle_timedout() for subscription in self.subscriptions
        ]
        aggregate_waits = reduce(lambda x,y: f'{x}\n{y}',waits)
        message = f'event timed out after {timeout} seconds\n'\
                  f'remaining subscriptions:'\
                  f'{aggregate_waits}'
        return message

    def gather_from_subscribed_buffers(self,polled_subscriptions: List) -> None:
        while self.polling.isSet():
            gathered_binned = [s.poll() for s in polled_subscriptions]
            gathered = reduce(lambda x,y: x+y,gathered_binned)
            gathered.sort(key= lambda item: item.get_date_lodged())
            if gathered:
                for item in gathered:
                    self.board.put(item)
                return
            else:
                sleep(0.05)

    def replay_subscription(self,subscription: Subscription)  -> str:
        device = subscription.device
        attr = subscription.attr
        handler_logs = subscription.handler.replay()
        internal_logs = subscription.tracer.print_messages()
        internal_events_pusher_logs = ''
        if subscription.eventsPusher:
            internal_events_pusher_logs = f'\nEvents Pusher Logs:{subscription.eventsPusher.tracer.print_messages()}'
        return f'subscription[{device}:{attr}]{handler_logs}\n'\
               f'internal subscription logs:'\
               f'{internal_logs}'\
               f'{internal_events_pusher_logs}'


    def replay_subscriptions(self) -> str:
        reduced_archived_logs =''
        reduced_active_subscription_logs = ''
        if self.archived_subscriptions:
            archived_logs = [self.replay_subscription(s) for s in self.archived_subscriptions]
            if archived_logs:
                reduced_archived_logs = reduce(lambda x,y: f'{x}\n{y}',archived_logs)
            else:
                reduced_archived_logs = "no archived messages lodged"
            reduced_archived_logs = f'archived subscriptions ({len(self.subscriptions)}):{reduced_archived_logs}'
        if self.subscriptions:
            active_subscription_logs = [self.replay_subscription(s) for s in self.subscriptions]
            if active_subscription_logs:
                reduced_active_subscription_logs = reduce(lambda x,y: f'{x}\n{y}',active_subscription_logs)
            else:
                reduced_active_subscription_logs = "no active messages lodged"
            reduced_active_subscription_logs = f'active subscriptions ({len(self.subscriptions)}):{reduced_active_subscription_logs}'
        return f'\n\n{reduced_active_subscription_logs}{reduced_archived_logs}'

    def replay_self(self) -> str:
        header = 'logs from Messageboard'
        return f'{header}{self.tracer.print_messages()}'


    @contextmanager
    def _concurrent_if_polling(self):
        polled_subscriptions = [s for s in self.subscriptions if s.polled]
        if polled_subscriptions:
            executor = futures.ThreadPoolExecutor(max_workers=1)
            self.polling.set()
            self.tracer.message(f'gathering task submitted concurrently to poll {len(polled_subscriptions)} subscriptions')
            gathering_task = executor.submit(self.gather_from_subscribed_buffers,polled_subscriptions)
            try:
                yield
            finally:
                self.polling.clear()
                gathering_task.result()
                self.tracer.message(f'gathering task finished')
        else:
            yield

    def get_items(self,timeout:float = None) -> EventItem:
        while self.subscriptions:
            try:
                with self._concurrent_if_polling():
                    item = self.board.get(timeout=timeout)
            except Empty as e:
                if all(s.supress_timeout() for s in self.subscriptions):
                    self.tracer.message(f'iteration stopped by surpressed timeout; {len(self.subscriptions)} subscriptions'
                                        f' will be cancelled')
                    self.remove_all_subcriptions()
                    return StopIteration()
                else:
                    message = self._get_printeable_timedout(timeout)
                    self.remove_all_subcriptions()
                    exception = EventTimedOut(e,message)
                    raise exception 
            device_name,attr,value,date = item.describe()
            self.tracer.message(f'yielding new event item {device_name}.{attr}::{value}@{date}')
            yield item

    def task_done(self):
        self.board.task_done()
            



