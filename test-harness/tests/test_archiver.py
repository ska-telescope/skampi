# -*- coding: utf-8 -*-
"""
Test archiver
"""
from tango import DeviceProxy, DevFailed
import json

def test_init():    
  print("Init test archiver")

def test_archiver():
  evt_subscriber_device_fqdn = "archiving/hdbpp/eventsubscriber01"
  config_manager_device_fqdn = "archiving/hdbpp/confmanager01"
  conf_manager_proxy = DeviceProxy(config_manager_device_fqdn)
  evt_subscriber_device_proxy = DeviceProxy(evt_subscriber_device_fqdn)
  attribute = "mid_d0001/elt/master/WindSpeed"
  # SetAttributeName
  conf_manager_proxy.write_attribute("SetAttributeName", attribute)
  # SetArchiver
  conf_manager_proxy.write_attribute("SetArchiver", evt_subscriber_device_fqdn)
  # SetStrategy
  conf_manager_proxy.write_attribute("SetStrategy", "ALWAYS")
  # SetPollingPeriod
  conf_manager_proxy.write_attribute("SetPollingPeriod", 1000)
  # SetEventPeriod
  conf_manager_proxy.write_attribute("SetPeriodEvent", 3000)
  try:
    # Add Attribute for archiving
    conf_manager_proxy.command_inout("AttributeAdd")
  except DevFailed as df:
    str_df = str(df)
    if "reason = Already archived" in str_df:
      # Start Attribute archiving
      conf_manager_proxy.command_inout("AttributeStart", attribute)

  print("ArchiverList", conf_manager_proxy.read_attribute("ArchiverList"))
  print("AttributeList", evt_subscriber_device_proxy.read_attribute("AttributeList"))
  # Check status of Attribute Archiving in Configuration Manager
  result_config_manager = conf_manager_proxy.command_inout("AttributeStatus",attribute)

  # Check status of Attribute Archiving in Event Subscriber
  result_evt_subscriber = evt_subscriber_device_proxy.command_inout("AttributeStatus", attribute)

  assert "Archiving          : Started" in result_config_manager
  assert "Archiving          : Started" in result_evt_subscriber
  conf_manager_proxy.command_inout("AttributeRemove", attribute)


