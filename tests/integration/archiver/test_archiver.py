# -*- coding: utf-8 -*-
"""
Test archiver
"""
import sys
import pytest
import logging
from time import sleep
from archiver_helper import ArchiverHelper
from tango import DevFailed, DeviceProxy, GreenMode, AttributeProxy, ApiUtil, DeviceData


@pytest.mark.post_deployment
@pytest.mark.skalow
def test_init_low():
  logging.info("Init test archiver low device")
  archiver_helper = ArchiverHelper(conf_manager="low-eda/cm/01", eventsubscriber="low-eda/es/01")
  archiver_helper.start_archiving()

@pytest.mark.post_deployment
@pytest.mark.skamid
def test_init():
  logging.info("Init test archiver mid")
  archiver_helper = ArchiverHelper()
  archiver_helper.start_archiving()
  
def configure_attribute(attribute, cm, es):
  archiver_helper = ArchiverHelper(cm, es)
  archiver_helper.attribute_add(attribute, 100, 300)
  archiver_helper.start_archiving() 
  slept_for = archiver_helper.wait_for_start(attribute)
  logging.info("Slept for " + str(slept_for) + 's before archiving started.')
  assert "Archiving          : Started" in archiver_helper.conf_manager_attribute_status(attribute)
  assert "Archiving          : Started" in archiver_helper.evt_subscriber_attribute_status(attribute)
  archiver_helper.stop_archiving(attribute)


def test_configure_attribute(cm,es):
  attribute = "sys/tg_test/1/double_scalar"
  sleep_time = 20
  max_retries = 3
  total_slept = 0
  for x in range(0, max_retries):
    try:
      ApiUtil.cleanup()
      configure_attribute(attribute, cm, es)
      break
    except DevFailed as df:
      logging.info("configure_attribute exception: " + str(sys.exc_info()))
      try:
        deviceAdm = DeviceProxy("dserver/hdbppcm-srv/01")
        deviceAdm.RestartServer()
      except:
        logging.info("reset_conf_manager exception: " + str(sys.exc_info()[0]))
      if(x == (max_retries - 1)):
        raise df

    sleep(sleep_time)
    total_slept += 1

  if(total_slept>0):
    logging.info("Slept for " + str(total_slept*sleep_time) + 's for the test configuration!')

@pytest.mark.post_deployment
@pytest.mark.skamid
def test_config_attribute_mid():
  try:
    test_configure_attribute("mid-eda/cm/01", "mid-eda/es/01")
  except Exception as e:
    logging.error(e)
    
@pytest.mark.post_deployment
@pytest.mark.skalow
def test_config_attribute_low():
  try:
    test_configure_attribute("low-eda/cm/01", "low-eda/es/01")
  except Exception as e:
    logging.error(e)