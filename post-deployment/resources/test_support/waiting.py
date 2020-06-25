from tango import EventType
from tango.asyncio import DeviceProxy
import asyncio
from time import sleep
from datetime import datetime
import threading
from queue import Queue, Empty
import logging

class interfaceStrategy():
    
    def subscribe(self,attr):
        pass

    async def async_subscribe(self,attr):
        pass

    async def async_wait_for_next_event(self,polling=100,timeout=5):
        pass

    def wait_for_next_event(self,polling=100,timeout=5):
        pass

    def unsubscribe(self):
        pass


class ListenerTimeOut(Exception):
    pass

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

    def wait_for_next_event(self,polling=None,timeout=5):
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
    
    async def async_wait_for_next_event(self,polling=None,timeout=5):
        return self.wait_for_next_event(polling,timeout)
    
    def unsubscribe(self):    
        ''' stops the subcription process ''' 
        for current_subscription in self.current_subscriptions: 
            self.device_proxy.unsubscribe_event(current_subscription['subscription'])
        self.listening = False
        self.current_subscriptions = []


    def wait_for_all_events_to_be_handled(self):
        '''allows for a thread to syncronise with another thread handling events withing a queue by joning it
        '''
        self.queue.join()

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
        self.current_subscriptions.append(current_subscription)
        self.set_to_listening()
    
    def _check_if_timed_out(self,timeout):
        timeleft = int((timeout*1000)/self.polling)
        while True:
            timeleft -= 1
            if timeleft == 0:
                attributes_being_monitored = [item['attribute_being_monitored'] for item in self.current_subscriptions]
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

    def unsubscribe(self):
        '''stops the current subscribing strategy on the device and clears the listening flag (in case of used within a seperate thread)
        '''
        self.clear_listening()
        for current_subscription in self.current_subscriptions: 
            self.device_proxy.unsubscribe_event(current_subscription['subscription'])

class Listener():
    '''Object that listens for an attribute on a specific tango device based on a particular
    strategy provided, when instantiated you need to supply it with a device proxy object;
    in addition you can suplly it with a strategy that defines the algorithm for subscribing and obtaining the next event
    (e.g. pushing or by pulling)'''

    def __init__(self,device_proxy,strategy=None,override_serverside_polling=False, client_side_polling=100):
        self.device_proxy = device_proxy
        self.override_serverside_polling = override_serverside_polling
        self.original_server_polling = None
        self.client_side_polling = client_side_polling
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
            # to ensure minimum wait time the server side is set to be twice as fast as the client
            polling = int(self.client_side_polling/2)
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
        events,elapsed_time = await self.strategy.async_wait_for_next_event(self.client_side_polling,timeout)
        if get_elapsed_time:
            return events,elapsed_time
        else:
            return events

    def wait_for_next_event(self,timeout=5,get_elapsed_time=False):
        '''
        blocks (waits) for a next event to arrive; the mechanism for wiatinng depends
        on the strategy provided.
        '''
        events,elapsed_time = self.strategy.wait_for_next_event(self.client_side_polling,timeout)
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
        self.listen_for(attr)
        while self.listening:
            events, elapsed_time = self.wait_for_next_event(timeout,get_elapsed_time=True)
            for event in events:
                if get_elapsed_time:
                    yield event, elapsed_time
                else:
                    yield event         

    def stop_listening(self):
        '''stop the threads and loops waiting for events arsing from the listening process
        A typical example is to call this during a 'for event in listener.get_events()` loop when
        a condition requires you to exit the loop
        '''
        self.listening = False
        self.strategy.unsubscribe()
        if self.override_serverside_polling:
            self._restore_polling()
    