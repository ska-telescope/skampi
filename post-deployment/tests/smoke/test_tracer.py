# -*- coding: utf-8 -*-

import sys
import pytest
import logging
from tango import Database, DeviceProxy, DeviceData, EventType, LogLevel, DevVarStringArray
from time import sleep
from resources.log_consumer.tracer_helper import TraceHelper
from assertpy import assert_that

import os

VAR = os.environ.get('DISABLE_TEST_TRACER')
if (VAR == "True"):
    disable_archive_tests = True
else:
    disable_archive_tests = False
#by default these tests are disabled


@pytest.mark.skipif(disable_archive_tests,reason="disabaled by local env")
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



@pytest.mark.skipif(disable_archive_tests,reason="disabaled by local env")
@pytest.mark.fast
@pytest.mark.tracer
def test_tracer():
    tracer = TraceHelper()
    try:
        tracer.enable_logging("sys/tg_test/1", LogLevel.LOG_DEBUG)
        tracer.wait_until_message_received("DataGenerator::generating data", 20)
        n_msg = len(tracer.get_messages())
        assert n_msg > 0
    finally:
        tracer.disable_logging("sys/tg_test/1")
    
    # test that we didn't get any additional messages after disabling the logging
    sleep(1)
    assert n_msg == len(tracer.get_messages())

@pytest.mark.skipif(disable_archive_tests,reason="disabaled by local env")
@pytest.mark.slow
@pytest.mark.tracer
def test_tracer_update():
    logging.info("instantiating TracerHelper")
    tracer = TraceHelper()
    try:
        logging.info("enable logging on sys/tg_test/1")
        tracer.enable_logging("sys/tg_test/1", LogLevel.LOG_DEBUG)
        tracer.wait_until_message_received("DataGenerator::generating data", 20)
    finally:
        tracer.disable_logging("sys/tg_test/1")
        logging.info("disabled logging on sys/tg_test/1")
    old_messages = tracer.get_messages()
    tracer = TraceHelper()
    tracer.reset_messages()
    logging.info("enable logging on ska_mid/tm_central/central_node")
    tracer.enable_logging("ska_mid/tm_central/central_node", LogLevel.LOG_DEBUG)
    sleep(1)
    new_messages = tracer.get_messages()
    try:
        logging.info("new messages")
        for new_message in new_messages:
            logging.info("date: %s message: %s",new_message.reception_date,new_message.attr_value.value)
            logging.info("old messages")
            for old_message in old_messages:
                logging.info("date: %s message: %s",old_message.reception_date,old_message.attr_value.value)
                assert_that(new_message).is_not_equal_to(old_message)
    finally:
        tracer.disable_logging("ska_mid/tm_central/central_node")
        logging.info("disabled logging on ska_mid/tm_central/central_node")        
    
        