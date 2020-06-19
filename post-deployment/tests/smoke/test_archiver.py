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
  sleep(3) # the polling

def configure_attribute(attribute):
  archiver_helper = ArchiverHelper()

  is_already_archived = False
  attr_list = archiver_helper.attribute_list()
  if attr_list is not None:
    for already_archived in attr_list:
      #logging.info("Comparing: " + str(attribute) + " and " + str(already_archived).lower())
      if attribute in str(already_archived).lower():
        is_already_archived = True
        #logging.info("is_already_archived: True")
        break

  if not is_already_archived:
    # fail if attribute is not ready to be archived
    try:
      att = AttributeProxy(attribute)
      att.read()
    except DevFailed as df:
      logging.error("Attribute to be configured not online! Failing...")
      raise df
  
    archiver_helper.attribute_add(attribute)
  
  archiver_helper.start_archiving()
  sleep(3) # the polling
  result_config_manager = archiver_helper.conf_manager_attribute_status(attribute)
  result_evt_subscriber = archiver_helper.evt_subscriber_attribute_status(attribute)
  
  assert "Archiving          : Started" in result_config_manager
  assert "Archiving          : Started" in result_evt_subscriber

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
  evt_subscriber_device_fqdn = "archiving/hdbpp/eventsubscriber01"
  evt_subscriber_device_proxy = DeviceProxy(evt_subscriber_device_fqdn)

  attribute = "mid_d0001/elt/master/WindSpeed"
  
  result_evt_subscriber = evt_subscriber_device_proxy.AttributeStatus(attribute)
  
  assert "Archiving          : Started" in result_evt_subscriber

