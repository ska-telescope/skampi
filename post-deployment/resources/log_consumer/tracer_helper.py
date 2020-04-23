import sys
import pytest
import logging
import threading
from tango import Database, DeviceProxy, DeviceData, EventType, LogLevel, DevVarStringArray
import time

class TraceHelper:
    def __init__(self):
        self.messages = []
        self.wait_for_msg = ""
        self.last_msg = ""
        self.found = False
        self.lock = threading.Lock()
        self.log_consumer_name = "LogConsumer/log/log01"
        self.logger_dev = DeviceProxy(self.log_consumer_name)
        self.logger_dev.subscribe_event("message", EventType.CHANGE_EVENT, self.handle_event, stateless=True)

    def enable_logging(self, devName, logLevel):
        dev = DeviceProxy(devName)
        dev.add_logging_target("device::" + self.log_consumer_name)
        dev.set_logging_level(int(logLevel))

    def disable_logging(self, devName):
        dev = DeviceProxy(devName)
        dev.remove_logging_target("device::" + self.log_consumer_name)
        dev.set_logging_level(0)

    def handle_event(self, args):
        if (args.attr_value.err):
            logging.info(str(args))
            return

        with self.lock:
            self.messages.append(args)
            self.last_msg = args.attr_value.value
            if(self.wait_for_msg in str(args.attr_value.value)):
                self.found = True
            logging.info(str(args.attr_value.value))

    def get_messages(self):
        """"Return a copy of the current messages."""
        with self.lock:
            return list(self.messages)

    def wait_until_message_received(self, msg, timeout):
        startTime = time.time()
        with self.lock: 
            self.found = False
            self.wait_for_msg = msg
        
        while True:
            if self.found:
                return True
            if(time.time() - startTime > timeout):
                raise Exception("Timeout occurred")
            time.sleep(0.1)
