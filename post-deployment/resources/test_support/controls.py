import pytest
from datetime import date,datetime
import os

##SUT imports
from oet.domain import SKAMid, SubArray, ResourceAllocation, Dish

##local depencies
from resources.test_support.mappings import device_to_container
from resources.test_support.helpers import subarray_devices,resource,ResourceGroup,waiter,watch
from resources.test_support.persistance_helping import update_file,update_scan_config_file,update_resource_config_file
from resources.test_support.sync_decorators import sync_assign_resources,sync_configure_oet,time_it,\
    sync_release_resources,sync_release_resources,sync_end_sb

def take_subarray(id):
    return pilot(id)

class pilot():
    
    def __init__(self, id):
        self.SubArray = SubArray(id)
        self.logs = ""
        self.agents = ResourceGroup(resource_names=subarray_devices)

    def and_display_state(self):
        print("state at {} is:\n{}".format(datetime.now(),self.agents.get('State')))
        return self

    def and_display_obsState(self):
        print("state at {} is:\n{}".format(datetime.now(),self.agents.get('obsState')))
        return self
    
    @sync_assign_resources(4)
    def to_be_composed_out_of(self, dishes, file = 'resources/test_data/OET_integration/example_allocate.json'):
        update_resource_config_file(file)
        multi_dish_allocation = ResourceAllocation(dishes=[Dish(x) for x in range(1, dishes + 1)])
        self.SubArray.allocate_from_file(file, multi_dish_allocation)
        return self

    @sync_configure_oet
    @time_it(120)
    def and_configure_scan_by_file(self,file = 'resources/test_data/TMC_integration/configure1.json'):
        update_scan_config_file(file)
        SubArray(1).configure_from_file(file, 2, with_processing = False)
        return self

    @sync_release_resources
    def and_release_all_resources(self):
        self.SubArray.deallocate()
        return self

    @sync_end_sb
    def and_end_sb_when_ready(self):
        self.SubArray.end_sb()
        return self


def restart_subarray(id):
    pass

def set_telescope_to_standby():
    the_waiter = waiter()
    the_waiter.set_wait_for_going_to_standby()
    SKAMid().standby()
    the_waiter.wait()
    if the_waiter.timed_out:
        pytest.fail("timed out whilst setting telescope to standby:\n {}".format(the_waiter.logs))

def set_telescope_to_running(disable_waiting = False):
    the_waiter = waiter()
    the_waiter.set_wait_for_starting_up()
    SKAMid().start_up()
    if not disable_waiting:
        the_waiter.wait()
        if the_waiter.timed_out:
            pytest.fail("timed out whilst starting up telescope:\n {}".format(the_waiter.logs))

def telescope_is_in_standby():
    return  [resource('ska_mid/tm_subarray_node/1').get("State"),
            resource('mid_csp/elt/subarray_01').get("State"),
            resource('mid_csp_cbf/sub_elt/subarray_01').get("State")] == \
            ['DISABLE' for n in range(3)]


def run_a_config_test():
    assert(telescope_is_in_standby)
    set_telescope_to_running()
    try:
        take_subarray(1).to_be_composed_out_of(4).and_configure_scan_by_file()
    except:
        if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "IDLE"):
            #this means there must have been an error
            if (resource('ska_mid/tm_subarray_node/1').get('State') == "ON"):
                print("tearing down composed subarray (IDLE)")
                take_subarray(1).and_release_all_resources() 
            set_telescope_to_standby()
            raise Exception("failure in configuring subarry not configured, resources are released and put in standby")
        if (resource('ska_mid/tm_subarray_node/1').get('obsState') == "CONFIGURING"):
            print("Subarray is still in configuring! Please restart MVP manualy to complete tear down")
            restart_subarray(1)
            #raise exception since we are unable to continue with tear down
            raise Exception("failure in configuring subarry, unable to reset the system")
    take_subarray(1).and_end_sb_when_ready().and_release_all_resources()
    set_telescope_to_standby()  
        
def run_a_config_test_series(size):
    for i in range(size):
        print('test run{}'.format(i))
        run_a_config_test()