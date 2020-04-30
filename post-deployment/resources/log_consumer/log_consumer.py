
import time
import numpy
import socketserver
import threading
from tango import AttrQuality, AttrWriteType, DispLevel, DevState, DebugIt  # GreenMode
from tango.server import Device, attribute, command, device_property

class SyslogUDPHandler(socketserver.BaseRequestHandler):

    def __init__(self):
        self.messages = []
        self.lock = threading.Lock()

    def handle(self):
        data = bytes.decode(self.request[0].strip())
        socket = self.request[1]
        print( "%s : " % self.client_address[0], str(data))
        with self.lock:
            self.messages.append(str(data))

    def flush_messages(self):
        """"Return a copy of the current messages."""
        with self.lock:
            res = list(self.messages)
            self.messages = []
            return res

class LogConsumer(Device):

    def __init__(self, device_class, device_name):
        super().__init__(device_class, device_name)
        self.lock = threading.Lock()
        self.set_change_event("message", True, False)
        self.attr_message = "init"
        self.handler = SyslogUDPHandler()
        self.udpServer = socketserver.UDPServer(("0.0.0.0", 514), self.handler)
        self.udpThread = threading.Thread(target=self.udpServer.serve_forever)
        self.udpThread.daemon = True
        self.udpThread.start()
        
    def init_device(self):
        """Initialise device"""
        Device.init_device(self)

    @attribute(dtype='str')
    def message(self):
        return self.attr_message

    @command(dtype_in=[str])
    def Log(self, input):
        result = "\t".join(input) 
        if(self.attr_message != result):
            self.attr_message = result
            self.push_change_event("message", self.attr_message, time.time(), AttrQuality.ATTR_VALID)

    @command(polling_period=100)
    def check_syslog_messages(self):
        with self.lock:
            messages = self.handler.flush_messages()
            for msg in messages:
                self.attr_message = msg
                self.push_change_event("message", self.attr_message, time.time(), AttrQuality.ATTR_VALID)

if __name__ == "__main__":
    LogConsumer.run_server()