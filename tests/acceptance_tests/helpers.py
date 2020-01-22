
from tango import DeviceProxy, DevState
from time import sleep

class state_checker:

    def __init__(self,device,timeout=10,debug=False):
        self.device = DeviceProxy(device)
        self.timeout =timeout
        self.debug = debug

    def to_be(self,*premises): # a dictionary specifying the rule e.g {"attr" : "obsState", "value" : "IDLE" }
        timeout = self.timeout
        result = "notOK"
        while (timeout != 0):
            timeout -= 1
            if (self.debug): print(timeout)
            premise_correct = False
            for premise in premises:
                required_attr = premise["value"]
                attr_name = premise["attr"]
                current_attr = self.device.read_attribute(attr_name).value
                if (current_attr == required_attr) :
                    premise_correct = True 
                else :
                     premise_correct = False
            if (premise_correct):
                timeout = 0
                result = "OK"
                #TODO throw timout exception
            else :
                sleep(1)
        return result

def wait_for(device,timeout=10):
    return state_checker(device,timeout)