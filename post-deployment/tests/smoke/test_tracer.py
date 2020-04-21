# -*- coding: utf-8 -*-
"""
Some simple unit tests of the PowerSupply device, exercising the device from
the same host as the tests by using a DeviceTestContext.
"""
from tango import Database, DeviceProxy, DeviceData, EventType, LogLevel, DevVarStringArray
from time import sleep
import sys
import pytest
import logging

messages = []

@pytest.mark.fast
def test_init():    
  print("Init test traces")
  timeSleep = 30
  for x in range(10):
      try:
          logging.info("Connecting to the databaseds")
          db = Database()
          break
      except:
          logging.info("Could not connect to the databaseds. Retry after " + str(timeSleep) + " seconds.")
          sleep(timeSleep)
  print("Connected to the databaseds")

@pytest.mark.fast
@pytest.mark.tracer
def test_traces():
    try:
        logger_dev = DeviceProxy("LogConsumer/log/log01")
        logger_dev.subscribe_event("message", EventType.CHANGE_EVENT, HandleEvent, stateless=True)

        test_dev = DeviceProxy("sys/tg_test/1")
        test_admin_dev = DeviceProxy(test_dev.adm_name())

        logging_param = ["sys/tg_test/1", "device::LogConsumer/log/log01"]
        test_admin_dev.AddLoggingTarget(logging_param)
        test_admin_dev.SetLoggingLevel([[5],["sys/tg_test/1"]])

        assert len(messages) > 0

        test_admin_dev.SetLoggingLevel([[0],["sys/tg_test/1"]])
    except:
        logging.info("Unexpected error:", sys.exc_info()[0])

def HandleEvent (args):
    messages.append(args)
