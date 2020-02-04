
from tango import DeviceProxy, DevState, CmdArgType, EventType
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish
from time import sleep
from numpy import ndarray 

obsState = {"IDLE" : 0}

class resource:

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

class monitor:

    def __init__(self,resource,previous_value,attr):
        self.previous_value = previous_value
        self.resource = resource
        self.attr = attr
        self.current_value = self.resource.get(self.attr)

    def _update(self):
        self.current_value = self.resource.get(self.attr)

    def _is_not_changed(self):
        comparison = (self.previous_value == self.current_value)
        if isinstance(comparison,ndarray):
            return comparison.all()
        else: return comparison

    def _wait(self,timeout=10):
        timeout = timeout
        while ( self._is_not_changed()):
            timeout -=1
            if (timeout == 0) : return "timeout"
            sleep(2)
            self._update()
        return "changed"


    def get_value_when_changed(self,timeout=10):
        response = self._wait(timeout)
        if (response == "timeout"):
            return "timeout"
        return self.current_value
    
    def wait_until_value_changed(self,timeout=10):
        self._wait(timeout)





class subscriber:

    def __init__(self,resource):
        self.resource = resource

    def for_a_change_on(self,attr):
        value_now = self.resource.get(attr)
        return monitor(self.resource,value_now,attr)

def watch(resource):
    return subscriber(resource)

class state_checker:

    def __init__(self,device,timeout=10,debug=False):
        self.device = device
        self.timeout =timeout
        self.debug = debug

    def to_be(self,*premises): # a dictionary specifying the rule e.g {"attr" : "obsState", "value" : "IDLE" }
        timeout = self.timeout
        result = "notOK"
        while (timeout != 0):
            timeout -= 1
            if (self.debug): print(timeout)
            premise_correct = False
            result=""
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
                timeout = 0
                result = "OK"
                #TODO throw timout exception
            else :
                sleep(1)
        return result

def wait_for(device,timeout=10):
    return state_checker(device,timeout)