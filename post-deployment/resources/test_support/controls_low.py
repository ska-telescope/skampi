import pytest
from datetime import date,datetime
import os
import logging

from resources.test_support.helpers_low import resource, waiter
import resources.test_support.tmc_helpers_low as tmc
from resources.test_support.mappings import device_to_subarrays

LOGGER = logging.getLogger(__name__)

def telescope_is_in_standby():
    LOGGER.info('resource("ska_low/tm_subarray_node/1").get("State")'+ str(resource('ska_low/tm_subarray_node/1').get("State")))
    LOGGER.info('resource("ska_low/tm_leaf_node/mccs_master").get("State")' +
                str(resource('ska_low/tm_leaf_node/mccs_master').get("State")))
    LOGGER.info('resource("low-mccs/control/control").get("State")' +
                str(resource('low-mccs/control/control').get("State")))
    return  [resource('ska_low/tm_subarray_node/1').get("State"),
            resource('ska_low/tm_leaf_node/mccs_master').get("State"),
            resource('low-mccs/control/control').get("State")] == \
            ['OFF','OFF', 'OFF']

def set_telescope_to_running(disable_waiting = False):
    resource('ska_low/tm_subarray_node/1').assert_attribute('State').equals('OFF')
    the_waiter = waiter()
    the_waiter.set_wait_for_starting_up()
    tmc.start_up()
    if not disable_waiting:
        the_waiter.wait(100)
        if the_waiter.timed_out:
            pytest.fail("timed out whilst starting up telescope:\n {}".format(the_waiter.logs))

def set_telescope_to_standby():
    resource('ska_low/tm_subarray_node/1').assert_attribute('State').equals('ON')
    the_waiter = waiter()
    the_waiter.set_wait_for_going_to_standby()
    tmc.set_to_standby()
    #It is observed that CSP and CBF subarrays sometimes take more than 8 sec to change the State to DISABLE
    #therefore timeout is given as 12 sec
    the_waiter.wait(100)
    if the_waiter.timed_out:
        pytest.fail("timed out whilst setting telescope to standby:\n {}".format(the_waiter.logs))

def restart_subarray(id):
    devices = device_to_subarrays.keys()
    filtered_devices = [device for device in devices if device_to_subarrays[device] == id ]
    the_waiter = waiter()
    the_waiter.set_wait_for_going_to_standby()
    exceptions_raised = ""
    for device in filtered_devices:
        try:
            resource(device).restart()
        except Exception as e:
            exceptions_raised += f'\nException raised on reseting {device}:{e}'
    if exceptions_raised != "":
        raise Exception(f'Error in initialising devices:{exceptions_raised}')
    the_waiter.wait()