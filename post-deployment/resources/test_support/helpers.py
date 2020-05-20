from time import sleep,time
import signal
from numpy import ndarray
import logging
from datetime import date,datetime
import os
from math  import ceil
import pytest


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
    
def handlde_timeout(par1,par2):
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
    
    def assert_attribute(self,attr):
        return ObjectComparison("{}.{}".format(self.device_name,attr),self.get(attr))

class ObjectComparison():
    def __init__(self,object,value):
        self.value = value
        self.object = object

    def equals(self,value):
        try:
            assert self.value == value
        except:
            raise Exception("{} is asserted to be {} but was instead {}".format(self.object,value,self.value))


####time keepers based on above resources
class monitor(object):
    previous_value = None
    resource = None
    attr = None
    device_name = None
    current_value = None

    def __init__(self, resource, previous_value, attr,future_value=None,predicate=None):
        self.previous_value = previous_value
        self.resource = resource
        self.attr = attr
        self.future_value = future_value
        self.device_name = resource.device_name
        self.current_value = previous_value
        self.data_ready = False
        self.predicate = predicate

    def _update(self):
        self.current_value = self.resource.get(self.attr)

    def _is_not_changed(self):
        is_changed_comparison = (self.previous_value != self.current_value)
        if isinstance(is_changed_comparison, ndarray):
            is_changed_comparison = is_changed_comparison.all()
        if is_changed_comparison:
            self.data_ready = True
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
        while (self._is_not_changed()):
            count_down -= 1
            if (count_down == 0):
                raise Exception('timed out waiting for {}.{} to change from {} in {:f}s'.format(
                    self.resource.device_name,
                    self.attr,
                    self.current_value,
                    timeout*resolution))
            sleep(resolution)
            self._update()
        return count_down

    def get_value_when_changed(self, timeout=50):
        response = self._wait(timeout)
        if (response == "timeout"):
            return "timeout"
        return self.current_value

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
        return monitor(self.resource, value_now, attr,changed_to,predicate)

 
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
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState",changed_to='IDLE'))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("obsState",changed_to='IDLE'))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).for_a_change_on("obsState",changed_to='IDLE'))
        self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("obsState",changed_to='IDLE'))

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
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State",changed_to='ON')) 
        self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State",changed_to='ON'))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("State",changed_to='ON'))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).for_a_change_on("State",changed_to='ON'))

    def set_wait_for_tearing_down_subarray(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("receptorIDList"))
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State",changed_to='OFF'))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("State",changed_to='OFF'))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).for_a_change_on("State",changed_to='OFF'))
        self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State",changed_to='OFF'))

    def set_wait_for_going_to_standby(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State",changed_to='DISABLE'))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("State",changed_to='DISABLE'))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).for_a_change_on("State",changed_to='DISABLE'))
        # at the moment sdb does not go to standby
        # self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State"))

    def set_wait_for_going_into_scanning(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on('obsState',changed_to='SCANNING'))  
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on('obsState',changed_to='SCANNING'))
        self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on('obsState',changed_to='SCANNING'))      

    def set_wait_for_starting_up(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State",changed_to='OFF'))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("State",changed_to='OFF'))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).for_a_change_on("State",changed_to='OFF'))
        # self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State"))

    def wait(self, timeout=30,resolution=0.1):
        self.logs = ""
        while self.waits:
            wait = self.waits.pop()
            try:
                result = wait.wait_until_value_changed(timeout=timeout,resolution=resolution)
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

#####schedulers and controllers aimed at putting the system in specified state

