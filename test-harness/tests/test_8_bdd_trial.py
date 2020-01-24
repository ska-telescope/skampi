# -*- coding: utf-8 -*-
""" A reimplementation of test 2, the telescope startup test, using Behaviour Driven Design (BDD).
"""
import itertools
import logging

from pytest_bdd import scenario, given, when, then
from tango import DevState, Database, DeviceProxy
from time import sleep
from tango import DeviceProxy

@scenario("./1.feature", "startup")
def test_bdd():
  assert 1

@given("tango devices")
def devices_list():
    pass

@when("I invoke the StartUpTelescope command")
def Start_Up():
    centralNode_proxy = DeviceProxy("ska_mid/tm_central/central_node")
    try:
        # execute command on central node
        centralNode_proxy.command_inout("StartUpTelescope")
        sleep(1)
    except DevFailed as df:
        df = "error in execution of command"
        print("Exception: ", df)

@then("Observation state of lower level devices should change")
def assert_state():
    subarray1_proxy = DeviceProxy("ska_mid/tm_subarray_node/1")
    #assert centralNode_proxy.State() == DevState.ON
    assert subarray1_proxy.State() == DevState.OFF