# -*- coding: utf-8 -*-
"""
Some simple unit tests of the PowerSupply device, exercising the device from
the same host as the tests by using a DeviceTestContext.
"""
from tango import Database, DeviceProxy,EventType # type: ignore
from time import sleep
import pytest
from assertpy import assert_that

@pytest.mark.fast
@pytest.mark.common
def test_init():    
  print("Init test devices")
  timeSleep = 30
  for _ in range(10):
      try:
          print ("Connecting to the databaseds")
          Database()
          break
      except:
          print ("Could not connect to the databaseds. Retry after " + str(timeSleep) + " seconds.")
          sleep(timeSleep)
  print("Connected to the databaseds")

@pytest.mark.fast
@pytest.mark.common
def test_devices():
  db = Database()
  count = 0
  server_list = db.get_server_list()
  i = 0
  while i < len(server_list):
    class_list = db.get_device_class_list(server_list[i])
    j = 0
    while j < len(class_list):
      try:
        if not "dserver" in class_list[j]:
          print("Connecting to '" + class_list[j] + "'...\r\n")
          DeviceProxy(class_list[j])
          count = count + 1
      except Exception as e: 
        print ("Could not connect to the '"+class_list[j]+"' DeviceProxy.\r\n")
        print (e)
      j += 2
    i += 1
  print("Total number of active devices " + str(count) + ".")
  assert count > 25

@pytest.mark.fast
@pytest.mark.skamid
def test_subscribe_to_attribute():
  sdp_subarray = DeviceProxy('mid_sdp/elt/subarray_1')
  id =  sdp_subarray.subscribe_event('State',EventType.CHANGE_EVENT,lambda event:print(event))
  sdp_subarray.unsubscribe_event(id)

@pytest.mark.fast
@pytest.mark.skamid
def test_dish_subscribe():
    dish_001 = DeviceProxy('mid_d0001/elt/master')
    sub_id = dish_001.subscribe_event('State', EventType.CHANGE_EVENT, lambda event:print(event))
    dish_001.unsubscribe_event(sub_id)

@pytest.mark.fast
@pytest.mark.skamid
def test_dish_not_on_at_start():
    assert_that(DeviceProxy('mid_d0001/elt/master').State().name).is_in('STANDBY','OFF')

@pytest.mark.fast
@pytest.mark.skamid
def test_dish_in_idle():
    assert_that(DeviceProxy('mid_d0001/elt/master').observingState.name).is_in('IDLE')
