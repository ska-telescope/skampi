# -*- coding: utf-8 -*-

import sys
import pytest
import logging
from tango import Database, DeviceProxy, DeviceData, EventType, LogLevel, DevVarStringArray
from time import sleep
from resources.log_consumer.tracer_helper import TraceHelper

@pytest.mark.fast
def test_init():    
  logging.info("Init test traces")
  timeSleep = 30
  for x in range(10):
      try:
          logging.info("Connecting to the databaseds")
          db = Database()
          break
      except Exception:
          logging.info("Could not connect to the databaseds. Retry after " + str(timeSleep) + " seconds.")
          sleep(timeSleep)
  logging.info("Connected to the databaseds")

@pytest.mark.fast
@pytest.mark.tracer
def test_tracer():
    tracer = TraceHelper()
    try:
        tracer.enable_logging("sys/tg_test/1", LogLevel.LOG_DEBUG)
        tracer.wait_until_message_received("DataGenerator::generating data", 20)
        assert len(tracer.get_messages()) > 0
    finally:
        tracer.disable_logging("sys/tg_test/1")
