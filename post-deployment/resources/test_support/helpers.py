import sys

sys.path.append('/app')

from tango import DeviceProxy, DevState, CmdArgType, EventType
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from time import sleep
from numpy import ndarray 
import logging

LOGGER = logging.getLogger(__name__)

obsState = {"IDLE" : 0}


def map_dish_nr_to_device_name(dish_nr):
    digits = str(10000+dish_nr)[1::]
    return "mid_d"+digits+"/elt/master"

class resource:

    device_name = None

    def __init__(self,device_name):
        self.device_name = device_name
    
    def get(self,attr):
        p = DeviceProxy(self.device_name)
        attrs = p.get_attribute_list()
        if (attr not in attrs) : return "attribute not found"
        tp = p._get_attribute_config(attr).data_type
        if (tp == CmdArgType.DevEnum):
            return getattr(p,attr).name
        if (tp == CmdArgType.DevState):
            return str(p.read_attribute(attr).value)
        else:
            value = getattr(p,attr)
            if isinstance(value,ndarray):
                return tuple(value)
            return getattr(p,attr)

class monitor(object):

    previous_value = None
    resource = None
    attr = None
    device_name = None
    current_value = None

    def __init__(self,resource,previous_value,attr):
        self.previous_value = previous_value
        self.resource = resource
        self.attr = attr
        self.device_name = resource.device_name
        self.current_value = self.resource.get(self.attr)

    def _update(self):
        self.current_value = self.resource.get(self.attr)

    def _is_not_changed(self):
        comparison = (self.previous_value == self.current_value)
        if isinstance(comparison,ndarray):
            return comparison.all()
        else: return comparison

    def _wait(self,timeout=50):
        timeout = timeout
        while ( self._is_not_changed()):
            timeout -=1
            if (timeout == 0) : return "timeout"
            sleep(0.1)
            self._update()
        return timeout


    def get_value_when_changed(self,timeout=50):
        response = self._wait(timeout)
        if (response == "timeout"):
            return "timeout"
        return self.current_value
    
    def wait_until_value_changed(self,timeout=50):
        return self._wait(timeout)





class subscriber:

    def __init__(self,resource):
        self.resource = resource

    def for_a_change_on(self,attr):
        value_now = self.resource.get(attr)
        return monitor(self.resource,value_now,attr)

def watch(resource):
    return subscriber(resource)
#this function may become depracated
class state_checker:

    def __init__(self,device,timeout=10,debug=False):
        self.device = device
        self.timeout =timeout
        self.debug = debug

    def to_be(self,*premises): # a dictionary specifying the rule e.g {"attr" : "obsState", "value" : "IDLE" }
        timeout = self.timeout
        result = "notOK"
        while (timeout != 0):
            if (self.debug): print(timeout)
            premise_correct = False
            result=str(timeout)
            for premise in premises:
                required_attr = premise["value"]
                attr_name = premise["attr"]
                current_attr = self.device.get(attr_name)
                if (current_attr == required_attr) :
                    premise_correct = True 
                else :
                     premise_correct = False
                     result += str(attr_name)+" not eq "+str(required_attr)
            if (premise_correct):
                return timeout
                #TODO throw timout exception
            else :
                sleep(0.1)
                timeout -= 1
        return "timed out"

def wait_for(device,timeout=50):
    return state_checker(device,timeout)

def take_subarray(id):
    return pilot(id)

class pilot():

    def __init__(self,id):
        self.SubArray = SubArray(id)
    
    def to_be_composed_out_of(self,dishes):
        the_waiter = waiter()
        the_waiter.set_wait_for_assign_resources()

        result = self.SubArray.allocate(ResourceAllocation(dishes=[Dish(x) for x in range(1,dishes+1)]))

        the_waiter.wait()
        LOGGER.info(the_waiter.logs)
        return result



def restart_subarray(id):
    pass

class waiter():

    def __init__(self):
        self.waits = []
        self.logs =""
    
    def set_wait_for_assign_resources(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State"))
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("receptorIDList"))
        #self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).for_a_change_on("State"))

    def set_wait_for_tearing_down_subarray(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("receptorIDList"))
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State"))

    def set_wait_for_going_to_standby(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).for_a_change_on("State"))
        #at the moment sdb does not go to standby
        #self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State"))

    def set_wait_for_starting_up(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp/elt/subarray_01')).for_a_change_on("State"))
        self.waits.append(watch(resource('mid_csp_cbf/sub_elt/subarray_01')).for_a_change_on("State"))
        #self.waits.append(watch(resource('mid_sdp/elt/subarray_1')).for_a_change_on("State"))
        
    def set_wait_for_ending_SB(self):
        self.waits.append(watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on("obsState"))

    def wait(self,timeout = 50):
        self.logs = ""
        while self.waits:
            wait =self.waits.pop()
            result = wait.wait_until_value_changed(timeout)
            if result == "timeout":
                self.logs += wait.device_name + " timed out whilst waiting for " +wait.attr + " to change from " + str(wait.previous_value) + " in 5 seconds;"
            else:
                self.logs += wait.device_name + " changed " +str(wait.attr) + " from " + str(wait.previous_value) + " to " + str(wait.current_value) + " after " + str(timeout - result) +" tries ;"

    
