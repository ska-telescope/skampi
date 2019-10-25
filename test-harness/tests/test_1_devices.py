# -*- coding: utf-8 -*-
"""
Some simple unit tests of the PowerSupply device, exercising the device from
the same host as the tests by using a DeviceTestContext.
"""
from tango import Database, DeviceProxy
from time import sleep

def test_init():    
  print("Init test devices")

def test_devices():
  db = Database()
  count = 0
  server_list = db.get_server_list();
  i = 0
  while i < len(server_list):
    class_list = db.get_device_class_list(server_list[i])
    j = 0
    while j < len(class_list):
      try:
        if not "dserver" in class_list[j]:
          print("Connecting to '" + class_list[j] + "'...\r\n")
          dev = DeviceProxy(class_list[j])
          count = count + 1
      except Exception as e: 
        print ("Could not connect to the '"+class_list[j]+"' DeviceProxy.\r\n")
        print (e)
      j += 2
    i += 1
  print("Total number of active devices " + str(count) + ".")
  assert count > 50

