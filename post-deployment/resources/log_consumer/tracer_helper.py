import sys
import pytest
import logging
import threading
import time
import socket
from tango import Database, DeviceProxy, DeviceData, EventType, LogLevel, DevVarStringArray

class TraceHelper:
    __instance = None

    def __new__(cls):
        if TraceHelper.__instance is None:
            TraceHelper.__instance = object.__new__(cls)
        return TraceHelper.__instance

    def __init__(self):
        if(not hasattr(TraceHelper.__instance, "lock")):
            TraceHelper.__instance.messages = []
            TraceHelper.__instance.wait_for_msg = ""
            TraceHelper.__instance.last_msg = ""
            TraceHelper.__instance.found = False
            TraceHelper.__instance.lock = threading.Lock()
            TraceHelper.__instance.log_consumer_name = "LogConsumer/log/log01"
            TraceHelper.__instance.logger_dev = DeviceProxy(TraceHelper.__instance.log_consumer_name)
            TraceHelper.__instance.logger_dev.subscribe_event("message", EventType.CHANGE_EVENT, TraceHelper.__instance.handle_event, stateless=True)

    def enable_logging(self, devName, logLevel):
        dev = DeviceProxy(devName)
        dev.add_logging_target("device::" + self.log_consumer_name)
        try:
            if(hasattr(dev, "loggingTargets")):
                logging.info("adding syslog::"+socket.gethostname())
                dev.loggingTargets = ["syslog::" + socket.gethostname()]
            #dev.add_logging_target("syslog::" + socket.gethostname())
        except Exception as ex_obj:
            logging.error("Exception in configure command:" + str(ex_obj))

        dev.set_logging_level(int(logLevel))

    def disable_logging(self, devName):
        dev = DeviceProxy(devName)
        dev.remove_logging_target("device::" + self.log_consumer_name)
        try:
            if(hasattr(dev, "loggingTargets")):
                dev.loggingTargets = []
        except Exception as ex_obj:
            logging.error("Exception in configure command:" + str(ex_obj))
        
        dev.set_logging_level(0)

    def handle_event(self, args):
        if (args.err):
            logging.error(str(args))
            return

        with self.lock:
            self.messages.append(args)
            self.last_msg = args.attr_value.value
            if(self.wait_for_msg in str(args.attr_value.value)):
                self.found = True
            logging.info(str(args.attr_value.value))

    def reset_messages(self):
        with self.lock:
            self.messages = []

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
            with self.lock: 
                if self.found:
                    return True
            if(time.time() - startTime > timeout):
                raise Exception("Timeout occurred")
            time.sleep(0.1)
