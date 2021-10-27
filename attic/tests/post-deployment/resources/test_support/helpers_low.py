from time import sleep,time
import signal
from numpy import ndarray
import logging
from datetime import date,datetime
import os
from math  import ceil
import pytest
import threading
import signal
from tango import EventType,EventData


#SUT frameworks
from tango import DeviceProxy, DevState, CmdArgType, EventType


LOGGER = logging.getLogger(__name__)

####typical device sets
subarray_devices = [
        'ska_low/tm_subarray_node/1',
        'low-mccs/subarray/01']

def wait_before_test(timeout=1):
    sleep(timeout)

def handle_timeout(par1,par2):
    print("operation timeout")
    raise Exception("operation timeout")

#####MVP asbtraction (tango,kubernetes ect as stateless resources)
class ResourceGroup():

    def __init__(self,resource_names=subarray_devices):
        self.resources = resource_names

    def get(self,attr):
        return [{resource_name : resource(resource_name).get(attr)} for resource_name in self.resources]

class resource:
    device_name = None

    def __init__(self, device_name):
        self.device_name = device_name

    def get(self, attr):
        p = DeviceProxy(self.device_name)
        attrs = p.get_attribute_list()
        if (attr not in attrs): return "attribute not found"
        tp = p._get_attribute_config(attr).data_type
        if (tp == CmdArgType.DevEnum):
            return getattr(p, attr).name
        if (tp == CmdArgType.DevState):
            return str(p.read_attribute(attr).value)
        else:
            value = getattr(p, attr)
            if isinstance(value, ndarray):
                return tuple(value)
            return getattr(p, attr)
    
    def restart(self):
        #current suggested method is through 'init' maybe reset would be better in future
        p = DeviceProxy(self.device_name)
        p.init()

    def assert_attribute(self,attr):
        return ObjectComparison("{}.{}".format(self.device_name,attr),self.get(attr))

class ObjectComparison():
    def __init__(self,object,value):
        self.value = value
        self.object = object

    def equals(self,value):
        try:
            if isinstance(value,list):
                #a list is assumed to mean an or condition, a tuple is assumed to be  an and condition
                assert self.value in value
            else:
                assert self.value == value
        except:
            raise Exception("{} is asserted to be {} but was instead {}".format(self.object,value,self.value))

class monitor(object):
    '''
    Montitors an attribte of a given resource and allows a user to block/wait on a specific condition:
    1. the attribite has changed in value (but it can be any value): previous value != current value
    2. the attribute has changed in value and to a specific desired value: previous value = future value but have changed also
    3. the attribute has changed or is already the desired value: previous value = future value
    4. instead of a direct equality a predicate can also be used to performa the comparison
    The value for which it must wait can also be provided by the time at calling the wait or by the time of instantiation
    The former allows for the monitor to be used in a list that waits iteratively, the latter is when it is inline at where it sould wait
    '''
    previous_value = None
    resource = None
    attr = None
    device_name = None
    current_value = None

    def __init__(self, resource, previous_value, attr,future_value=None,predicate=None,require_transition=False):
        self.previous_value = previous_value
        self.resource = resource
        self.attr = attr
        self.require_transition =require_transition
        self.future_value = future_value
        self.device_name = resource.device_name
        self.current_value = previous_value
        self.data_ready = False
        self.predicate = predicate

    def _update(self):
        self.current_value = self.resource.get(self.attr)

    def _conditions_not_met(self):
        #change comparison section (only if require_transition)
        if self.require_transition:
            is_changed_comparison = (self.previous_value != self.current_value)
            if isinstance(is_changed_comparison, ndarray):
                is_changed_comparison = is_changed_comparison.all()
            if is_changed_comparison:
                self.data_ready = True
        else:
            self.data_ready = True
        #comparison with future section (only if future value given)
        #if no future value was given it means you can ignore (or set to true) comparison with a future
        if self.future_value == None:
            is_eq_to_future_comparison = True
        else: 
            if self.predicate == None:
                is_eq_to_future_comparison = (self.current_value == self.future_value)
            else:
                is_eq_to_future_comparison = self.predicate(self.current_value,self.future_value)
            if isinstance(is_eq_to_future_comparison, ndarray):
                is_eq_to_future_comparison= is_eq_to_future_comparison.all()   
        return (not self.data_ready) or (not is_eq_to_future_comparison)

    def _compare(self,desired):
        comparison = (self.current_value == desired)
        if isinstance(comparison,ndarray):
            return comparison.all()
        else:
            return comparison

    def _wait(self, timeout=80,resolution=0.1):
        count_down = timeout
        while (self._conditions_not_met()):
            count_down -= 1
            if (count_down == 0):
                future_shim = ""
                if self.future_value is not None:
                    future_shim = f" to {self.future_value}"
                raise Exception('timed out waiting for {}.{} to change from {}{} in {:f}s (current val = {})'.format(
                    self.resource.device_name,
                    self.attr,
                    self.previous_value,
                    future_shim,
                    timeout*resolution,
                    self.current_value))
            sleep(resolution)
            self._update()
        return count_down

    def get_value_when_changed(self, timeout=50):
        response = self._wait(timeout)
        if (response == "timeout"):
            return "timeout"
        return self.current_value

    def wait_until_conditions_met(self, timeout=50,resolution=0.1):
        return self._wait(timeout)

    def wait_until_value_changed(self, timeout=50,resolution=0.1):
        return self._wait(timeout)
    
    def wait_until_value_changed_to(self,value,timeout=50,resolution=0.1):
        count_down = timeout
        self._update()
        while not self._compare(value):
            count_down -= 1
            if (count_down == 0):
                raise Exception('timed out waiting for {}.{} to change from {} to {} in {:f}s'.format(
                    self.resource.device_name,
                    self.attr,
                    self.current_value,
                    value,
                    timeout*resolution))
            sleep(resolution)
            self._update()
        return count_down

class subscriber:

    def __init__(self, resource,implementation='polling'):
        self.resource = resource
        self.implementation = implementation

    def for_a_change_on(self, attr,changed_to=None,predicate=None):
        if self.implementation == 'polling':
            value_now = self.resource.get(attr)
            return monitor(self.resource, value_now, attr,changed_to,predicate,require_transition=True)
        elif self.implementation == 'tango_events':
            return AttributeWatcher(self.resource,attr,desired=changed_to,predicate=predicate,require_transition=True,start_now=True)

    def to_become(self,attr,changed_to,predicate=None):
        if self.implementation == 'polling':
            value_now = self.resource.get(attr)
            return monitor(self.resource, value_now, attr,changed_to,predicate,require_transition=False)
        elif self.implementation == 'tango_events':
            return AttributeWatcher(self.resource,attr,desired=changed_to,predicate=predicate,require_transition=False,start_now=True)

    def for_any_change_on(self,attr,predicate=None):
        if self.implementation == 'polling':
            value_now = self.resource.get(attr)
            return monitor(self.resource,value_now,attr,require_transition=True)
        elif self.implementation == 'tango_events':
            return AttributeWatcher(self.resource,attr,desired=None,predicate=predicate,require_transition=True,start_now=True)


 
def watch(resource,implementation='polling'):
    return subscriber(resource,implementation)


# this function may become depracated
class state_checker:

    def __init__(self, device, timeout=80, debug=False):
        self.device = device
        self.timeout = timeout
        self.debug = debug

    def to_be(self, *premises):  # a dictionary specifying the rule e.g {"attr" : "obsState", "value" : "IDLE" }
        timeout = self.timeout
        result = "notOK"
        while (timeout != 0):
            if (self.debug): print(timeout)
            premise_correct = False
            result = str(timeout)
            for premise in premises:
                required_attr = premise["value"]
                attr_name = premise["attr"]
                current_attr = self.device.get(attr_name)
                if (current_attr == required_attr):
                    premise_correct = True
                else:
                    premise_correct = False
                    result += str(attr_name) + " not eq " + str(required_attr)
            if (premise_correct):
                return timeout
                # TODO throw timout exception
            else:
                sleep(0.1)
                timeout -= 1
        return "timed out"


def wait_for(device, timeout=80):
    return state_checker(device, timeout)


### this is a composite type of waiting based on a set of predefined pre conditions expected to be true
class waiter():
    
    def __init__(self):
        self.waits = []
        self.logs = ""
        self.error_logs = ""
        self.timed_out = False

    def clear_watches(self):
        self.waits = []

    def set_wait_for_ending_SB(self):
        self.waits.append(watch(resource('ska_low/tm_subarray_node/1')).to_become("obsState",changed_to='IDLE'))
        self.waits.append(watch(resource('low-mccs/subarray/01')).to_become("obsState",changed_to='IDLE'))


    def set_wait_for_assign_resources(self):
        self.waits.append(watch(resource('ska_low/tm_subarray_node/1')).to_become("State",changed_to='ON'))
        self.waits.append(watch(resource('low-mccs/control/control')).to_become("State",changed_to='ON'))
        self.waits.append(watch(resource('low-mccs/subarray/01')).to_become("State",changed_to='ON'))
        self.waits.append(watch(resource('low-mccs/subarray/01')).to_become("obsState",changed_to='IDLE'))
        self.waits.append(watch(resource('ska_low/tm_subarray_node/1')).to_become("obsState",changed_to='IDLE'))

     
    def set_wait_for_tearing_down_subarray(self):
        self.waits.append(watch(resource('ska_low/tm_subarray_node/1')).to_become("obsState",changed_to='EMPTY'))


    def set_wait_for_going_to_standby(self):
        self.waits.append(watch(resource('ska_low/tm_subarray_node/1')).to_become("State",changed_to='OFF'))
        self.waits.append(watch(resource('low-mccs/control/control')).to_become("State",changed_to='OFF')) 
        self.waits.append(watch(resource('ska_low/tm_central/central_node')).to_become("State",changed_to='OFF'))

    def set_wait_for_going_into_scanning(self):
        self.waits.append(watch(resource('ska_low/tm_subarray_node/1')).to_become('obsState',changed_to='SCANNING'))  


    def set_wait_for_starting_up(self):
        self.waits.append(watch(resource('ska_low/tm_subarray_node/1')).to_become("State",changed_to='ON'))
        self.waits.append(watch(resource('low-mccs/control/control')).to_become("State",changed_to='ON'))
        self.waits.append(watch(resource('ska_low/tm_central/central_node')).to_become("State",changed_to='ON'))
        
    def set_wait_for_going_into_obsreset(self):
        self.waits.append(watch(resource('ska_low/tm_subarray_node/1')).to_become('obsState',changed_to='IDLE'))

    def wait(self, timeout=30,resolution=0.1):
        self.logs = ""
        while self.waits:
            wait = self.waits.pop()
            if isinstance(wait,AttributeWatcher):
                timeout = timeout*resolution
            try:
                result = wait.wait_until_conditions_met(timeout=timeout,resolution=resolution)
            except:
                self.timed_out = True
                future_value_shim = ""
                timeout_shim = timeout*resolution
                if isinstance(wait,AttributeWatcher):
                    timeout_shim = timeout
                if wait.future_value is not None:
                    future_value_shim = f" to {wait.future_value} (current val={wait.current_value})"
                self.error_logs += "{} timed out whilst waiting for {} to change from {}{} in {:f}s\n".format(
                    wait.device_name,
                    wait.attr,
                    wait.previous_value,
                    future_value_shim,
                    timeout_shim
                )
            else:
                timeout_shim = (timeout - result)*resolution
                if isinstance(wait,AttributeWatcher):
                    timeout_shim = result
                self.logs += "{} changed {} from {} to {} after {:f}s \n".format(
                    wait.device_name,
                    wait.attr,
                    wait.previous_value,
                    wait.current_value,
                    timeout_shim)
        if self.timed_out:
            raise Exception("timed out, the following timeouts occured:\n{} Successfull changes:\n{}".format(
                self.error_logs,
                self.logs
        ))

class AttributeWatcher():
    '''listens to events in a device and enables waiting until a predicate is true or publish to a subscriber
    It allows in essence for the ability to wait for three types of conditions:
    1. The attribute value has become or was already from the start the desired future value 
    2. The attribute value has changed from its original value into any new value
    3. The attribute value as transitioned into the desired future value (this means it must have changed from the original)
    These different conditions upon which to wait is specified by the constructure params. However the typical use case is to use 
    the "watch.for_a... factory methods to instantiate the watcher (see subscriber).
    This is also the same type of watch as implemented by the monitor class except that this one uses the tango device subscribe 
    mechanism as opposed to a simple polling implemented by the other.
    Thus the key mechanism is a call back with the appropriate event pushed by the device, the event in turns gets evaluated against the required 
    conditions to determine whether a threading  event should be set (in case of all conditions being met.) This allows a wait method to hook on the event by calling 
    the wait method (see python threading event)
    '''
    
    def __init__(self,resource,attribute,desired=None,predicate=None,require_transition=False,start_now=True,polling = 100):
        self.device_proxy = DeviceProxy(resource.device_name)
        self.device_name = resource.device_name
        self.future_value = desired
        self.polling = polling
        self.attribute = attribute
        self.attr = attribute
        self.previous_value = None
        self.current_value = None
        self.is_changed = False
        self.require_transition = require_transition
        self.result_available = threading.Event()
        self.current_subscription = None
        self.original_polling = None
        self.waiting=False
        if predicate is None:
            self.predicate = self._default_predicate
        else:
            self.predicate = predicate
        if start_now:
            self.start_listening()


    def _default_predicate(self,current_value,desired):
        comparison = (current_value == desired)
        if isinstance(comparison,ndarray):
            return comparison.all()
        else:
            return comparison


    def start_listening(self):
        if self.device_proxy.is_attribute_polled(self.attribute):
            #must be reset to original when finished
            self.original_polling = self.device_proxy.get_attribute_poll_period
        self.device_proxy.poll_attribute(self.attribute,self.polling)
        self.current_subscription = self.device_proxy.subscribe_event(
            self.attribute,
            EventType.CHANGE_EVENT,
            self._cb)

    #this method will be called by a thread
    def _cb(self,event):
        self.current_value = str(event.attr_value.value)
        if self.previous_value is None:
            #this implies it is the first event and is always treated as the value when subscription started
            self.previous_value = self.current_value
            self.start_time = event.reception_date.totime()
        if not self.is_changed:
            self.is_changed = (self.current_value != self.previous_value)
        if self.future_value is None:
            # this means that it is only evaluating a change and not the end result of the evaluation
            if self.is_changed:
                self.elapsed_time= event.reception_date.totime() - self.start_time
                self.result_available.set()
        elif self.predicate(self.current_value,self.future_value):
            if self.require_transition:
                if self.is_changed:
                    self.elapsed_time=event.reception_date.totime() - self.start_time
                    self.result_available.set()
            else:
                self.elapsed_time=event.reception_date.totime() - self.start_time
                self.result_available.set()


    def _handle_timeout(self,remaining_seconds,test):
        self.stop_listening()
        raise Exception(f'Timed out waiting for an change on {self.device_proxy.name()}.{self.attribute} \
    to change from {self.previous_value} to {self.desired} in {self.timeout}s (current value is {self.current_value}')

    def _wait(self,timeout):
        self.timeout = timeout
        signal.signal(signal.SIGALRM, self._handle_timeout)
        signal.alarm(timeout)
        self.result_available.wait()
        signal.signal(0)
        self.stop_listening()

    def stop_listening(self):
        if self.original_polling is not None:
            self.device_proxy.poll_attribute(self.original_polling)
        self.device_proxy.unsubscribe_event(self.current_subscription)

    def wait_until_value_changed_to(self,desired,timeout=2,resolution=None):
        self.desired = desired
        self.waiting = True
        self._wait(int(timeout))
        return self.elapsed_time

    def wait_until_conditions_met(self,timeout=2,resolution=None):
        self._waiting = True
        self._wait(int(timeout))
        return self.elapsed_time
