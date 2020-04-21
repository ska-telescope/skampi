import sys
import pytest
import logging
import threading
from tango import Database, DeviceProxy, DeviceData, EventType, LogLevel, DevVarStringArray
import time

class tracer_helper:
    def __init__(self):
        self.messages = []
        self.last_msg = ""
        self.lock = threading.Lock()
        self.log_consumer_name = "log_consumer/log/log01"
        self.logger_dev = DeviceProxy(self.log_consumer_name)
        self.logger_dev.subscribe_event("message", EventType.CHANGE_EVENT, self.handle_event, stateless=True)

    def enable_logging(self, devName, logLevel):
        dev = DeviceProxy(devName)
        dev_admin = DeviceProxy(dev.adm_name())

        logging_param = [devName, "device::" + self.log_consumer_name]
        dev_admin.AddLoggingTarget(logging_param)
        dev_admin.SetLoggingLevel([[int(logLevel)],[devName]])

    def disable_logging(self, devName):
        dev = DeviceProxy(devName)
        dev_admin = DeviceProxy(dev.adm_name())

        logging_param = [devName, "device::" + self.log_consumer_name]
        dev_admin.RemoveLoggingTarget(logging_param)
        dev_admin.SetLoggingLevel([[0], [devName]])

    def handle_event(self, args):
        self.lock.acquire()
        self.messages.append(args)
        self.last_msg = args.attr_value.value
        self.lock.release()
        logging.info(str(args.attr_value.value))

    def get_messages(self):
        return self.messages

    def wait_until_message_received(self, msg, timeout):
        startTime = time.time()
        while True:
            self.lock.acquire()
            if self.last_msg.find(msg) > 0:
                return True
            self.lock.release()
            if(time.time() - startTime > timeout):
                raise Exception("Timeout occurred")
            time.sleep(0.1)
