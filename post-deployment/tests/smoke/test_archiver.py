# -*- coding: utf-8 -*-
"""
Test archiver
"""
import sys
import pytest
import logging
from time import sleep
from resources.test_support.archiver import ArchiverHelper
from tango import DevFailed, DeviceProxy, GreenMode, AttributeProxy, ApiUtil, DeviceData

@pytest.mark.archiver
@pytest.mark.xfail
def test_init():
  print("Init test archiver")
  archiver_helper = ArchiverHelper()
  archiver_helper.start_archiving()

def configure_attribute(attribute):
  archiver_helper = ArchiverHelper()
  archiver_helper.attribute_add(attribute,100,300)
  archiver_helper.start_archiving()
  sleep(0.3) # the polling
  assert "Archiving          : Started" in archiver_helper.conf_manager_attribute_status(attribute)
  assert "Archiving          : Started" in archiver_helper.evt_subscriber_attribute_status(attribute)
  archiver_helper.stop_archiving(attribute)

@pytest.mark.archiver
@pytest.mark.xfail
def test_configure_attribute():
  attribute = "sys/tg_test/1/double_scalar"
  sleep_time = 20
  max_retries = 3
  for x in range(0, max_retries):
    try:
      ApiUtil.cleanup()
      configure_attribute(attribute)
      break
    except DevFailed as df:
      logging.info("configure_attribute exception: " + str(sys.exc_info()))
      if(x == (max_retries - 1)):
        raise df
    
    try:
      deviceAdm = DeviceProxy("dserver/hdbppcm-srv/01")
      deviceAdm.RestartServer()
    except:
      logging.info("reset_conf_manager exception: " + str(sys.exc_info()[0]))
    
    sleep(sleep_time)

@pytest.mark.archiver
@pytest.mark.xfail
def test_archiving_started():
  archiver_helper = ArchiverHelper()
  result_evt_subscriber = archiver_helper.evt_subscriber_attribute_status("mid_d0001/elt/master/WindSpeed")
  assert "Archiving          : Started" in result_evt_subscriber

