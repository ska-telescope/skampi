from tango import EventType,DeviceProxy
import asyncio
from time import sleep
from datetime import datetime
from functools import reduce
import threading
from queue import Queue, Empty
import logging


class interfaceStrategy():
    
    def subscribe(self,attr):
        pass

    async def async_subscribe(self,attr):
        pass

    async def async_wait_for_next_event(self,timeout=5):
        pass

    def wait_for_next_event(self,timeout=5):
        pass

    def unsubscribe(self):
        pass

    def query(self):
        pass


class ListenerTimeOut(Exception):
    pass

class HandeableListenerTimeOut(ListenerTimeOut):

    def __init__(self,message,handler):
        self.handler = handler
        super().__init__(message)

class ConsumeImmediately(interfaceStrategy):
    '''
    Implements a listening strategy by enabling the client to consume events immediately upon being publised. This results in a thread
    calling a callback which in turn puts the event in a threading queue that can be waited upon by another thread
    '''

    def __init__(self,device_proxy):
        self.device_proxy = device_proxy
        self.queue = Queue()
        self.current_subscriptions = []
        self.lock = threading.Lock() 
        self.listening = False

    def _cb(self,event):
          with self.lock:
            self.queue.put(event)

    def subscribe(self,attr):
        '''
        Initiates the subscribtion to an attribute on a device by suplying the calbback
        '''
        self.listening = True
        self.current_subscriptions.append({'subscription':self.device_proxy.subscribe_event(
            attr,
            EventType.CHANGE_EVENT,
            self._cb),
            'attr':attr})
                
    async def async_subscribe(self,attr):
        '''
        Initiates the subscribtion to an attribute on a device by suplying the calbback
        done in an asynchronous way
        '''
        self.listening = True
        self.current_subscriptions.append(await self.device_proxy.subscribe_event(
            attr,
            EventType.CHANGE_EVENT,
            self._cb
        ))

    def wait_for_next_event(self,timeout=5):
        '''
        waits for next event by calling get on the queue
        raises ListenerTimeOut when timeout exceeds the timeout par (default 5 seconds)
        returns an empty list if the listening has been canceled whilst or before entering loop
        '''
        if self.listening:
            try:
                start_time = datetime.now()
                event = self.queue.get(timeout=timeout)
                elapsed_time = datetime.now() - start_time
            except Empty:
                raise ListenerTimeOut(f'Timed out after {timeout} seconds waiting for events on attributes'\
                                    f'{[s["attr"] for s in self.current_subscriptions]} for device {self.device_proxy.name()}')
            return [event],elapsed_time
        else:
            return []
    
    async def async_wait_for_next_event(self,timeout=5):
        return self.wait_for_next_event(timeout)
    
    def unsubscribe(self,*attrs):    
        ''' stops the subcription process ''' 
        if attrs == ():
            for current_subscription in self.current_subscriptions: 
                self.device_proxy.unsubscribe_event(current_subscription['subscription'])
            self.listening = False
            self.current_subscriptions = []


    def wait_for_all_events_to_be_handled(self):
        '''allows for a thread to syncronise with another thread handling events withing a queue by joning it
        '''
        self.queue.join()

    def query(self):
        with self.lock:
            if self.queue.empty():
                return None
            else:
                return [self.queue.get_nowait()]

class ConsumePeriodically(interfaceStrategy):
    '''
    Particular strategy (for use by Listener Object) to consume changed events from an attribute on a device on a periodic basis
    by means of placing published events on a receiving buffer
    The default buffer_size (max nr of events) is 10. This means you need to start consuming the buffer (wait for next event)
    within 10 divided by the expected frequency of attribite change. If the device is set to periodically publish events this can be determined
    by investigating the poll period for the attribute
    '''
    def __init__(self,device_proxy,buffer_size=10,polling=100):
        self.device_proxy = device_proxy
        self.listening = False
        self.buffer_size = buffer_size
        self.current_subscriptions = []
        self.current_subscriptions2 = {}
        self.lock = threading.Lock()
        self.polling=polling

    def subscribe(self,attr):
        '''
        Implementation of subscription strategy on a device by means of setting a buffer size (instead of a callback)
        on the subcription command)
        '''
        current_subscription = {
            'subscription' : self.device_proxy.subscribe_event(
                                attr,
                                EventType.CHANGE_EVENT,
                                self.buffer_size),
            'attribute_being_monitored' : attr
        }
        self.current_subscriptions2[attr] = current_subscription['subscription']
        self.current_subscriptions.append(current_subscription)
        self.set_to_listening()

    async def async_subscribe(self,attr):
        '''
        Implementation of subscription strategy on a device by means of setting a buffer size (instead of a callback)
        on the subcription command)
        This command allows for asnychronous calling by awaiting the results of subscription command
        '''
        current_subscription = {
            'subscription' : await self.device_proxy.subscribe_event(
                                attr,
                                EventType.CHANGE_EVENT,
                                self.buffer_size),
            'attribute_being_monitored' : attr
        }
        self.current_subscriptions2[attr] = current_subscription['subscription']
        self.current_subscriptions.append(current_subscription)
        self.set_to_listening()
    
    def _check_if_timed_out(self,timeout):
        timeleft = int((timeout*1000)/self.polling)
        while True:
            timeleft -= 1
            if timeleft == 0:
                # attributes_being_monitored = [item['attribute_being_monitored'] for item in self.current_subscriptions]
                attributes_being_monitored = list(self.current_subscriptions2.keys())
                raise ListenerTimeOut(f'Timed out after {timeout} seconds waiting for events on attributes'\
                                    f'{attributes_being_monitored} for device {self.device_proxy.name()}')
            yield timeleft

    def _check_all_subscriptions_for_events(self):
        events = []
        for subscription in self.current_subscriptions:
            subscription_id = subscription['subscription']
            events += self.device_proxy.get_events(subscription_id)
        return events

    def is_listening(self):
        with self.lock:
            return self.listening

    def set_to_listening(self):
        with self.lock:
            self.listening = True

    def clear_listening(self):
        with self.lock:
            self.listening = False

    async def async_wait_for_next_event(self,timeout=5):
        '''
        Strategy for waiting for next event by means of polling the event buffer, if the event buffer is empty and the timeleft is still
        within the timeout window, the process will sleep for a period double the polling period of the device itself (e.g. it doesnt waste time
        querying the device faster that its internal polling threads)
        Since this method is an asyncio call it returns to the event loop whilst waiting for the ne next event, thus allowing the user to perform 
        other IO tasks whilst waiting for the next event.
        If the listening flag on the object is changed to false ( by means of a thread or asyncio task) the method will return before the timeout has occured
        '''
        timeout_checker = self._check_if_timed_out(timeout)
        events = []
        start_time = datetime.now()
        while self.is_listening():
            events = self._check_all_subscriptions_for_events()
            if events == []:
                next(timeout_checker)
                await asyncio.sleep(self.polling*2/1000)
            else:
                elapsed_time = datetime.now() - start_time
                return events,elapsed_time
        return []

    def wait_for_next_event(self,timeout=5):
        '''
        Strategy for waiting for next event by means of polling the event buffer, if the event buffer is empty and the timeleft is still
        within the timeout window, the process will sleep for a period double the polling period of the device itself (e.g. it doesnt waste time
        querying the device faster that its internal polling threads)
        Note this method is not asyncio so the thread will be blocked whilst sleeping 
        If the listening flag on the object is changed to false ( by means of a thread or asyncio task) the method will return before the timeout has occured
        '''
        timeout_checker = self._check_if_timed_out(timeout)
        events = []
        start_time = datetime.now()
        while self.is_listening():
            events = self._check_all_subscriptions_for_events()
            if events == []:
                next(timeout_checker)
                sleep(self.polling*2/1000)
            else:
                elapsed_time = datetime.now() - start_time
                return events, elapsed_time
        return events

    def query(self):
        events = self._check_all_subscriptions_for_events()
        if events == []:
            return None
        else:
            return events

    def unsubscribe(self,*attrs):
        '''stops the current subscribing strategy on the device and clears the listening flag (in case of used within a seperate thread)
        '''
        if attrs == ():
            self.clear_listening()
            for current_subscription in self.current_subscriptions: 
                self.device_proxy.unsubscribe_event(current_subscription['subscription'])
        else:
            for attr in attrs:
                for current_subscription in self.current_subscriptions: 
                    if current_subscription['attribute_being_monitored'] == attr:
                        self.device_proxy.unsubscribe_event(current_subscription['subscription'])


class Listener():
    '''Object that listens for an attribute on a specific tango device based on a particular
    strategy provided, when instantiated you need to supply it with a device proxy object;
    in addition you can suplly it with a strategy that defines the algorithm for subscribing and obtaining the next event
    (e.g. pushing or by pulling)'''

    def __init__(self,device_proxy,strategy=None,override_serverside_polling=False, server_side_polling=None):
        self.device_proxy = device_proxy
        self.default_server_side_polling=100
        self.override_serverside_polling = override_serverside_polling
        self.original_server_polling = None
        self.server_side_polling = server_side_polling
        if strategy is  None:
            self.strategy = ConsumePeriodically(device_proxy)
        else:
            self.strategy = strategy

    def _remember_polling(self,attr):
        self.attribute_being_monitored = attr
        if self.device_proxy.is_attribute_polled(attr):
            self.original_server_polling = self.device_proxy.get_attribute_poll_period(attr)

    def _setup_device_polling(self,attr):
        if self.override_serverside_polling:
            self._remember_polling(attr)
            if self.server_side_polling is None:
                #assumes the selection must be made by software itself
                if isinstance(self.strategy,ConsumePeriodically):
                    client_side_polling = self.strategy.polling
                    # to ensure minimum wait time the server side is set to be twice as fast as the client
                    polling = int(client_side_polling/2)
                else:
                    # selects a default polling on server of 100
                    polling = self.default_server_side_polling
            else:
                polling = self.server_side_polling
            self.device_proxy.poll_attribute(attr,polling)
            self.current_server_side_polling = polling
        
    def _restore_polling(self):
        if self.original_server_polling is not None:
            self.device_proxy.poll_attribute(self.attribute_being_monitored,self.original_server_polling)
        else:
            #TODO reset polling try to disable it entirely otherwise set to very slow
            self.device_proxy.poll_attribute(self.attribute_being_monitored,60000)

    async def async_listen_for(self,attr):
        '''
        starts the listening process by calling the strategy's subcribe method
        this method allows for asyncronous calling
        '''
        self._setup_device_polling(attr)
        await self.strategy.async_subscribe(attr)
        self.listening = True
    
    def listen_for(self,*attrs):
        '''
        starts the listening process by calling the strategy's subcribe method
        '''
        for attr in attrs:
            self._setup_device_polling(attr)
            self.strategy.subscribe(attr)
            self.listening = True

    async def async_wait_for_next_event(self,timeout=5,get_elapsed_time=False):
        '''
        blocks (waits) for a next event to arrive; the mechanism for wiatinng depends
        on the strategy provided.
        this method allows for asyncronous calling by returning to event loop whilst waiting
        '''
        events,elapsed_time = await self.strategy.async_wait_for_next_event(timeout)
        if get_elapsed_time:
            return events,elapsed_time
        else:
            return events

    def wait_for_next_event(self,timeout=5,get_elapsed_time=False):
        '''
        blocks (waits) for a next event to arrive; the mechanism for wiatinng depends
        on the strategy provided.
        '''
        events,elapsed_time = self.strategy.wait_for_next_event(timeout)
        if get_elapsed_time:
            return events,elapsed_time
        else:
            return events

    async def async_get_events_on(self,attr,max_events=None,get_elapsed_time=False,timeout=5):
        '''allows for getting events in a lazy for loop as a generator. If no events are available it will wait
        untill timeout. If more than one events were gotten from a call it will iterate through the results.
        To stop wating for events you need to call `stop_listening()`.
        This method allows for asynchonous waiting (e.g. `async for`)
        '''
        await self.async_listen_for(attr)
        while self.listening:
            events, elapsed_time = await self.async_wait_for_next_event(timeout,get_elapsed_time=True)
            for event in events:
                assert(event is not None)
                if get_elapsed_time:
                    yield event, elapsed_time
                else:
                    yield event         

    def get_events_on(self,attr,max_events=None,get_elapsed_time=False,timeout=5):
        '''allows for getting events in a lazy for loop as a generator. If no events are available it will wait
        untill timeout. If more than one events were gotten from a call it will iterate through the results.
        To stop wating for events you need to call `stop_listening()`.
        '''
        if isinstance(attr,list):
            attr = tuple(attr)
        self.listen_for(attr)
        while self.listening:
            events, elapsed_time = self.wait_for_next_event(timeout,get_elapsed_time=True)
            for event in events:
                if get_elapsed_time:
                    yield event, elapsed_time
                else:
                    yield event         

    def query(self):
        '''query a current listening implementation for any imcoming events
        if present it shall return with a  list of one or more events, else it shall return
        with None
        '''
        return self.strategy.query()
        

    def stop_listening(self):
        '''stop the threads and loops waiting for events arsing from the listening process
        A typical example is to call this during a 'for event in listener.get_events()` loop when
        a condition requires you to exit the loop
        '''
        self.listening = False
        self.strategy.unsubscribe()
        if self.override_serverside_polling:
            self._restore_polling()

class Tracer():

    def __init__(self,message=None):
        if message is None:
            self.messages = []
        else:
            self.messages = [message]

    def message(self,message):
        self.messages.append(message)

    def print_messages(self):
        return reduce(lambda x,y: f'{x}\n{y}',self.messages)

class HandeableEvent():

    def __init__(self,handler,event,elapsed_time,listener):
        self.handler = handler
        self.event = event
        self.listener = listener
        self.elapsed_time = elapsed_time

    def handle(self,*args,supply_elapsed_time=False,):
        if supply_elapsed_time:
            args = (self.event,self.listener,self.elapsed_time)+args
        else:
            args = (self.event,self.listener)+args
        if callable(self.handler):
            # e.g. it is a function or a class
            self.handler(*args)
        else:
            self.handler.handle_event(*args)

class Timer():

    def __init__(self,timeout,resolution,context=None):
        self.resolution = resolution
        self.time = 0
        self.timeout =timeout
        self.context = context

    def tick(self):
        self.time += self.resolution

    def sleep_tick(self):
        sleep(self.resolution)
        self.tick()

    async def async_tick(self):
        await asyncio.sleep(self.resolution)
        self.tick()

    def reset(self):
        self.time = 0

    def time_up(self):
        return self.time >= self.timeout

    def time_not_up(self):
        return not self.time_up()

class GatheringTimeout(Exception):

    def __init__(self,time,gatherer):
        self.time = time
        self.gatherer = gatherer
        super().__init__(f'Timed out out gathering events after {self.time} seconds')

def heads(dictionary):
    return tuple(dictionary.keys())

class Gatherer():

    def __init__(self):
        self.listeners = {}
        self.active_listeners = {}
        
    def _new_binding(self,handler,*attr):
        binding = {}
        attrs = {}
        for attribute in attr:
            attrs[attribute] = {'handler':handler,'timer':None}
        binding['attrs'] = attrs
        binding['tracer'] = Tracer(f'new binding: {attr} to {handler}')
        return binding
    
    def _update_binding(self,binding,handler,*attr):
        attrs = binding['attrs']
        tracer = binding['tracer']
        for attribute in attr:
            attrs[attribute] = {'handler':handler,'timer':None}
        tracer.message(f'binded {attr} to {handler}')
        

    def bind(self,listener,handler,*attr):
        binding = self.listeners.get(listener)
        if binding is None:
            self.listeners[listener] = self._new_binding(handler,*attr)
        else:
            self._update_binding(binding,handler,*attr)

    def start_listening(self):
        exceptions = []
        for the_listener,binding in self.listeners.items():
            the_tracer = binding['tracer']
            the_attrs = heads(binding['attrs'])
            try:
                the_listener.listen_for(the_attrs)
                self.active_listeners[the_listener] = None
            except Exception as e:
                exceptions.append(e)
            the_tracer.message(f'started listening at {datetime.now()}')
        # if exceptions: raise Exception(f'{exceptions}')
            
    def _time_events(self,timeout,resolution):
        for the_listener,binding in self.listeners.items():
            for attr in binding['attrs'].values():
                the_handler = attr['handler']
                context = {
                    'handler':the_handler,
                    'listener':the_listener }
                attr['timer'] = Timer(timeout,resolution,context)

    def _tick_attrs(self,attrs):
        for attr in attrs.values():
            timer = attr['timer']
            timer.tick()
            if timer.time_up:
                attr['timeout'] = True

    def get_events(self,timeout,resolution=0.001):
        timer = Timer(timeout,resolution)
        self._time_events(timeout,resolution)
        sleepy = False
        while True:
            empty_run = True
            # the run
            for the_listener,binding in self.listeners.items():
                the_tracer = binding['tracer']
                the_attrs = binding['attrs']
                if sleepy:
                    self._tick_attrs(the_attrs)
                events = the_listener.query()
                if events is not None:
                    empty_run = False
                    for event in events:
                        attr = event.attr_name
                        the_handler = the_attrs[attr]['handler']
                        the_timer = the_attrs[attr]['timer']
                        the_timer.reset()
                        assert(the_handler is not None)
                        the_tracer.message(f'yielding event {event} for {attr}'
                                           f' to be handled by {the_handler}'
                                           f' at {datetime.now()}')
                        yield HandeableEvent(the_handler,event,timer.time,the_listener) 
                if not the_listener.listening:
                    self.active_listeners.pop(the_listener)
            # end of the run
            # if all listeners have been stopped get out
            if not self.active_listeners:
                return
            # if no events were picked up in the run then sleep
            if empty_run:
                if timer.time_up():
                    raise GatheringTimeout(timer.timeout,self)
                else:
                    timer.sleep_tick()
                    sleepy= True
            else:
                # reset the counter and run again without sleeping
                sleepy = False
                timer.reset()     

# factories

class ListenFor():

    def __init__(self,devicename: str) -> None:
        self.devicename = devicename

    def by_immediate_consumption(self,*args) -> Listener:
        device_proxy = DeviceProxy(self.devicename)
        strategy = ConsumeImmediately(device_proxy)
        listener = Listener(device_proxy,strategy,*args)
        return listener

    

def listen_for(devicename: str):
    return ListenFor(devicename)
