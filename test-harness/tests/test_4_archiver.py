# -*- coding: utf-8 -*-
"""
Test archiver
"""
from tango import DeviceProxy, DevFailed
from time import sleep
import pytest

def test_init():
  print("Init test archiver")

def test_archiver():
  evt_subscriber_device_fqdn = "archiving/hdbpp/eventsubscriber01"
  config_manager_device_fqdn = "archiving/hdbpp/confmanager01"
  conf_manager_proxy = DeviceProxy(config_manager_device_fqdn)
  evt_subscriber_device_proxy = DeviceProxy(evt_subscriber_device_fqdn)
  attribute = "mid_d0001/elt/master/WindSpeed"
  sleep(1)

  # SetAttributeName
  conf_manager_proxy.write_attribute("SetAttributeName", attribute)
  sleep(1)
  # SetArchiver
  conf_manager_proxy.write_attribute("SetArchiver", evt_subscriber_device_fqdn)
  sleep(1)
  # SetStrategy
  conf_manager_proxy.write_attribute("SetStrategy", "ALWAYS")
  sleep(1)
  # SetPollingPeriod
  conf_manager_proxy.write_attribute("SetPollingPeriod", 1000)
  sleep(1)
  # SetEventPeriod
  conf_manager_proxy.write_attribute("SetPeriodEvent", 3000)
  sleep(1)

  try:
    # Add Attribute for archiving
    conf_manager_proxy.command_inout("AttributeAdd")
    sleep(1)
  except DevFailed as df:
    str_df = str(df)
    print("Exception: ", str_df)

  # Check status of Attribute Archiving in Configuration Manager
  result_config_manager = conf_manager_proxy.command_inout("AttributeStatus",attribute)
  # Check status of Attribute Archiving in Event Subscriber
  result_evt_subscriber = evt_subscriber_device_proxy.command_inout("AttributeStatus", attribute)

  assert "Archiving          : Started" in result_config_manager
  assert "Archiving          : Started" in result_evt_subscriber

  try:
    # Remove Attribute for archiving
    conf_manager_proxy.command_inout("AttributeRemove", attribute)
    sleep(1)
  except DevFailed as df:
    str_df = str(df)
    print("Exception: ", str_df)
