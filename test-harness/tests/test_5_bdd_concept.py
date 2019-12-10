# -*- coding: utf-8 -*-
"""
A reimplementation of some of the basic tests in this directory, implemented using a bdd (Behaviour Driven Design) style. Currently, this is done by copy-paste of parts of the tests; it could reasonably be refactored to call the other functions more directly. However, I (vla22) wanted to partition the existing functions in a particular way, to fit better with the BDD style.
"""

from tango import Database, DeviceProxy
from time import sleep
from pytest_bdd import given, when, then

@given("A set of tango devices")
def list_devices():
    db = Database()
    server_list = db.get_server_list()

@when("I check the number of running devices")
def check_list():
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

@then("The number of active devices should be more than 50"
    assert count > 50
