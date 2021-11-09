import pytest
from datetime import date, datetime
import os
import logging
from tango import DeviceProxy
from ska.scripting.domain import Telescope, SubArray

##SUT imports
from ska.scripting.domain import Telescope
from resources.test_support.helpers_low import (
    subarray_devices,
    resource,
    ResourceGroup,
    waiter,
    watch,
)
from resources.test_support.sync_decorators_low import (
    sync_assign_resources,
    sync_configure,
    sync_reset_sa,
    sync_end_sb,
)
import resources.test_support.tmc_helpers_low as tmc
from resources.test_support.mappings import device_to_subarrays
from resources.test_support.mappings_low import device_to_subarray

LOGGER = logging.getLogger(__name__)


def take_subarray(id):
    return pilot(id)


class pilot:
    def __init__(self, id):
        self.SubArray = SubArray(id)
        self.logs = ""
        self.agents = ResourceGroup(resource_names=subarray_devices)
        self.state = "Empty"
        self.rollback_order = {
            "IDLE": self.reset_when_aborted
            #'Ready':self.and_end_sb_when_ready,
            # 'Configuring':restart_subarray,
            # 'Scanning':restart_subarray
        }

    def and_display_state(self):
        print("state at {} is:\n{}".format(datetime.now(), self.agents.get("State")))
        return self

    def and_display_obsState(self):
        print("state at {} is:\n{}".format(datetime.now(), self.agents.get("obsState")))
        return self

    def reset_when_aborted(self):
        @sync_reset_sa
        def reset():
            self.SubArray.reset()

        reset()
        self.state = "IDLE"
        return self

    def and_end_sb_when_ready(self):
        @sync_end_sb
        def end_sb():
            self.SubArray.end()

        end_sb()
        self.state = "Composed"
        return self


def telescope_is_in_standby():
    LOGGER.info(
        'resource("ska_low/tm_subarray_node/1").get("State")'
        + str(resource("ska_low/tm_subarray_node/1").get("State"))
    )
    LOGGER.info(
        'resource("ska_low/tm_leaf_node/mccs_master").get("State")'
        + str(resource("ska_low/tm_leaf_node/mccs_master").get("State"))
    )
    return [
        resource("ska_low/tm_subarray_node/1").get("State"),
        resource("ska_low/tm_leaf_node/mccs_master").get("State"),
    ] == ["OFF", "OFF"]


def set_telescope_to_running(disable_waiting=False):
    resource("ska_low/tm_subarray_node/1").assert_attribute("State").equals("OFF")
    the_waiter = waiter()
    the_waiter.set_wait_for_starting_up()
    Telescope().start_up()
    if not disable_waiting:
        the_waiter.wait(100)
        if the_waiter.timed_out:
            pytest.fail(
                "timed out whilst starting up telescope:\n {}".format(the_waiter.logs)
            )


def set_telescope_to_standby():
    resource("ska_low/tm_subarray_node/1").assert_attribute("State").equals("ON")
    the_waiter = waiter()
    the_waiter.set_wait_for_going_to_standby()
    Telescope().standby()
    # It is observed that CSP and CBF subarrays sometimes take more than 8 sec to change the State to DISABLE
    # therefore timeout is given as 12 sec
    the_waiter.wait(100)
    if the_waiter.timed_out:
        pytest.fail(
            "timed out whilst setting telescope to standby:\n {}".format(
                the_waiter.logs
            )
        )


@sync_assign_resources(100)
def to_be_composed_out_of():
    resource("ska_low/tm_subarray_node/1").assert_attribute("State").equals("ON")
    resource("ska_low/tm_subarray_node/1").assert_attribute("obsState").equals("EMPTY")
    assign_resources_file = (
        "resources/test_data/OET_integration/mccs_assign_resources.json"
    )
    subarray = SubArray(1)
    LOGGER.info("Subarray has been created.")
    subarray.allocate_from_file(cdm_file=assign_resources_file, with_processing=False)
    LOGGER.info("Invoked AssignResources on CentralNodeLow")


@sync_configure
def configure_by_file():
    configure_file = "resources/test_data/OET_integration/mccs_configure.json"
    SubarrayNodeLow = DeviceProxy("ska_low/tm_subarray_node/1")
    subarray = SubArray(1)
    LOGGER.info("Subarray has been created.")
    subarray.configure_from_file(configure_file, 10, with_processing=False)
    LOGGER.info("Subarray obsState is: " + str(SubarrayNodeLow.obsState))
    LOGGER.info("Invoked Configure on Subarray")


def restart_subarray(id):
    devices = device_to_subarrays.keys()
    filtered_devices = [
        device for device in devices if device_to_subarrays[device] == id
    ]
    the_waiter = waiter()
    the_waiter.set_wait_for_going_to_standby()
    exceptions_raised = ""
    for device in filtered_devices:
        try:
            resource(device).restart()
        except Exception as e:
            exceptions_raised += f"\nException raised on reseting {device}:{e}"
    if exceptions_raised != "":
        raise Exception(f"Error in initialising devices:{exceptions_raised}")
    the_waiter.wait()


def restart_subarray_low(id):
    devices = device_to_subarray.keys()
    filtered_devices = [
        device for device in devices if device_to_subarray[device] == id
    ]
    the_waiter = waiter()
    the_waiter.set_wait_for_going_to_standby()
    exceptions_raised = ""
    for device in filtered_devices:
        try:
            resource(device).restart()
        except Exception as e:
            exceptions_raised += f"\nException raised on reseting {device}:{e}"
    if exceptions_raised != "":
        raise Exception(f"Error in initialising devices:{exceptions_raised}")
    the_waiter.wait()
