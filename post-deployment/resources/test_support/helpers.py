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

obsState = {"IDLE": 0}

####typical device sets
subarray_devices = [
        'ska_mid/tm_subarray_node/1',
        'mid_csp/elt/subarray_01',
        'mid_csp_cbf/sub_elt/subarray_01',
        'mid_sdp/elt/subarray_1']


def map_dish_nr_to_device_name(dish_nr):
    digits = str(10000 + dish_nr)[1::]
    return "mid_d" + digits + "/elt/master"
    
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


####time keepers based on above resources
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
        if (future_value==None) and (require_transition == None):
            raise Exception('can not wait for a condition that doesnt require transition and no desired value')
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

    def __init__(self, resource):
        self.resource = resource

    def for_a_change_on(self, attr,changed_to=None,predicate=None):
        value_now = self.resource.get(attr)
        return monitor(self.resource, value_now, attr,changed_to,predicate,require_transition=True)

    def to_become(self,attr,changed_to,predicate=None):
        value_now = self.resource.get(attr)
        return monitor(self.resource, value_now, attr,changed_to,predicate,require_transition=False)

    def for_any_change_on(self,attr,predicate=None):
        value_now = self.resource.get(attr)
        return monitor(self,resource,value_now,attr,require_transition=True)


 
def watch(resource):
    return subscriber(resource)


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
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).to_become("obsState",changed_to='IDLE'))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).to_become("obsState",changed_to='IDLE'))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).to_become("obsState",changed_to='IDLE'))
        self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).to_become("obsState",changed_to='IDLE'))

    def set_wait_for_assign_resources(self,nr_of_receptors=None):
        ### the following is a hack to wait for items taht are not worked into the state variable
        if nr_of_receptors is not None:
            def predicate_sum(current,expected):
                return (sum(current) == sum(expected))
            def predicate_set_eq(current,expected):
                if current is None:
                    return False
                else:
                    return (set(current) == set(expected))
            IDlist_ones = tuple([1 for i in range(0,nr_of_receptors)])
            IDlist_inc = tuple([i for i in range(1,nr_of_receptors+1)])
            self.waits.append(watch(resource('ska_mid/tm_subarray_node/1'))
                .for_a_change_on(
                    "receptorIDList",
                    changed_to=IDlist_inc,
                    predicate=predicate_set_eq))
            self.waits.append(watch(resource('mid_csp/elt/subarray_01'))
                .for_a_change_on(
                    "assignedReceptors",
                    changed_to=IDlist_inc,
                    predicate=predicate_set_eq))
            self.waits.append(watch(resource('mid_csp/elt/master'))
                .for_a_change_on("receptorMembership",
                    changed_to=IDlist_ones,
                    predicate=predicate_sum))
        else:
            self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("receptorIDList"))
            self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("assignedReceptors"))
            self.waits.append(watch(resource('mid_csp/elt/master')).for_a_change_on("receptorMembership"))
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).to_become("State",changed_to='ON')) 
        self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).to_become("State",changed_to='ON'))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).to_become("State",changed_to='ON'))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).to_become("State",changed_to='ON'))

    def set_wait_for_tearing_down_subarray(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("receptorIDList"))
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).to_become("State",changed_to='OFF'))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).to_become("State",changed_to='OFF'))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).to_become("State",changed_to='OFF'))
        self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).to_become("State",changed_to='OFF'))

    def set_wait_for_going_to_standby(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).to_become("State",changed_to='DISABLE'))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).to_become("State",changed_to='DISABLE'))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).to_become("State",changed_to='DISABLE'))
        # at the moment sdb does not go to standby
        # self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State"))

    def set_wait_for_going_into_scanning(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).to_become('obsState',changed_to='SCANNING'))  
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).to_become('obsState',changed_to='SCANNING'))
        self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).to_become('obsState',changed_to='SCANNING'))      

    def set_wait_for_starting_up(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).to_become("State",changed_to='OFF'))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).to_become("State",changed_to='OFF'))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).to_become("State",changed_to='OFF'))
        # self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State"))

    def wait(self, timeout=30,resolution=0.1):
        self.logs = ""
        while self.waits:
            wait = self.waits.pop()
            try:
                result = wait.wait_until_conditions_met(timeout=timeout,resolution=resolution)
            except:
                self.timed_out = True
                shim = ""
                if wait.future_value is not None:
                    shim = f" to {wait.future_value} (current val={wait.current_value})"
                self.error_logs += "{} timed out whilst waiting for {} to change from {}{} in {:f}s\n".format(
                    wait.device_name,
                    wait.attr,
                    wait.previous_value,
                    shim,
                    timeout*resolution
                )
            else:
                self.logs += "{} changed {} from {} to {} after {:f}s \n".format(
                    wait.device_name,
                    wait.attr,
                    wait.previous_value,
                    wait.current_value,
                    timeout - result*resolution)
        if self.timed_out:
            raise Exception("timed out, the following timeouts occured:\n{} Successfull changes:\n{}".format(
                self.error_logs,
                self.logs
        ))

#####Waiters based on tango DevicProxy's abilitu to subscribe to events


class AttributeWatcher():
    '''listens to events in a device and enables waiting until a predicate is true or publish to a subscriber'''

    def __init__(self,resource,attribute,desired=None,predicate=None,start_now=True,polling = 100):
        self.device_proxy = DeviceProxy(resource.device_name)
        self.desired = desired
        self.polling = polling
        self.attribute = attribute
        self.result_available = threading.Event()
        self.current_subscription = None
        self.original_polling = None
        self.value_at_start_up = None
        self.waiting=False
        if predicate is None:
            self.predicate = self._default_predicate
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
        self.device_proxy.poll_attribute(self.polling)
        self.current_subscription = self.device_proxy.subscribe_event(
            self.attribute,
            EventType.CHANGE_EVENT,
            self._cb)

    ##this method will be called by a thread
    def _cb(self,event):
        self.current_value = event.attr_value()
        if self.value_at_start_up is None:
            #this implies it is the first event and is always treated as the value when subscription started
            self.value_at_start = self.current_value
        elif self.desired is None:
            self.result_available.set()
        elif self.predicate(self.current_value,self.desired):
            self.result_available.set()


    def _handle_timeout(self,remaining_seconds):
        raise Exception(f'Timed out waiting for an change on {self.device_proxy.name()}.{self.attribute} \
    to change from {self.value_at_start} to {self.desired} (current value is {self.current_value}')

    def _wait(self,timeout):
        signal.signal(signal.SIGALRM, handle_timeout)
        self.result_available.wait()
        signal.signal(0)
        self.stop_listening()

    def stop_listening(self):
        if self.original_polling is not None:
            self.device_proxy.poll_attribute(self.original_polling)
        self.device_proxy.unsubscribe_event(self.current_subscription)

    def wait_until_value_changed_to(self,desired,timeout=2):
        self.desired = desired
        self.waiting = True
        self._wait(timeout)

    def wait_until_value_changed(self,timeout=2):
        self._waiting = True
        self._wait(timeout)





        


    
