import time

from tango import AttrQuality  # GreenMode
from tango.server import Device, attribute, command


class LogConsumer(Device):
    def __init__(self, device_class, device_name):
        super().__init__(device_class, device_name)
        self.set_change_event("message", True, False)
        self.attr_message = "init"

    def init_device(self):
        """Initialise device"""
        Device.init_device(self)

    @attribute(dtype="str")
    def message(self):
        return self.attr_message

    @command(dtype_in=[str])
    def Log(self, input):
        result = "\t".join(input)
        if self.attr_message != result:
            self.attr_message = result
            self.push_change_event(
                "message",
                self.attr_message,
                time.time(),
                AttrQuality.ATTR_VALID,
            )


if __name__ == "__main__":
    LogConsumer.run_server()
