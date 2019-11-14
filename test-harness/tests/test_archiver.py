# -*- coding: utf-8 -*-
"""
Test archiver
"""
from tango import DeviceProxy

def test_init():    
  print("Init test archiver")

def test_archiver():
  config_mngr_devproxy = DeviceProxy("archiving/hdbpp/confmanager01")
  #evt_sub_devproxy = DeviceProxy("archiving/hdbpp/eventsubscriber01")
  result = config_mngr_devproxy.command_inout("AttributeStatus","mid_d0001/elt/master/WindSpeed")
  print(result)
  assert 1

