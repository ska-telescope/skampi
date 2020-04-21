
import time
import numpy
from tango import AttrQuality, AttrWriteType, DispLevel, DevState, DebugIt  # GreenMode
from tango.server import Device, attribute, command, device_property


class log_consumer(Device):

    message = attribute(
        dtype='str',
        period=100
    )

    def __init__(self, device_class, device_name):
        super().__init__(device_class, device_name)
        self.set_change_event("message", True, False)
        self.attr_message = "init"

    def init_device(self):
        """Initialise device"""
        Device.init_device(self)

    def read_message(self):
        return self.attr_message

    @command(dtype_in=[str])
    def Log(self, input):
        result = ""
        for str0 in input:
            result = result + str0 + "\t"
        self.attr_message = result + "\n"
        #print(self.attr_message)
        self.push_change_event("message", self.attr_message, time.time(), AttrQuality.ATTR_VALID)

if __name__ == "__main__":
    log_consumer.run_server()