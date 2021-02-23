import pytest
from datetime import date,datetime
import os
import logging

##SUT imports
from ska.scripting.domain import Telescope, SubArray
from ska.cdm.schemas import CODEC as cdm_CODEC
from ska.cdm.messages.central_node.assign_resources import AssignResourcesRequest

##local depencies
from resources.test_support.helpers import subarray_devices,resource,ResourceGroup,waiter,watch
from resources.test_support.persistance_helping import update_scan_config_file,update_resource_config_file
from resources.test_support.sync_decorators import sync_assign_resources,sync_configure_oet,time_it,\
    sync_release_resources,sync_end_sb,sync_scan_oet,sync_restart_sa
from resources.test_support.mappings import device_to_subarrays

LOGGER = logging.getLogger(__name__)

def take_subarray(id):
    return pilot(id)

class pilot():
    
    def __init__(self, id):
        self.SubArray = SubArray(id)
        self.logs = ""
        self.agents = ResourceGroup(resource_names=subarray_devices)
        self.state = "Empty"
        self.rollback_order = {
            'Composed': self.and_release_all_resources,
            'Ready':self.and_end_sb_when_ready,
           # 'Configuring':restart_subarray,
           # 'Scanning':restart_subarray
        }

    def and_display_state(self):
        print("state at {} is:\n{}".format(datetime.now(),self.agents.get('State')))
        return self

    def and_display_obsState(self):
        print("state at {} is:\n{}".format(datetime.now(),self.agents.get('obsState')))
        return self
    
    ##the following methods are implemented versions of what gets tested 
    ##unless a specic version  is tested they should be exactly the same
    
    def to_be_composed_out_of(self, dishes, file = 'resources/test_data/OET_integration/example_allocate.json'):
        ##Reference tests/acceptance/mvp/test_XR-13_A1.py
        @sync_assign_resources(dishes,200)
        def assign():
            sdp_block = update_resource_config_file(file)
            resource_request: AssignResourcesRequest = cdm_CODEC.load_from_file(AssignResourcesRequest, file)
            resource_request.dish.receptor_ids = [str(x).zfill(4) for x in range(1, dishes + 1)]
            self.SubArray.allocate_from_cdm(resource_request)
            return sdp_block
        sdp_block = assign()
        self.state = "Composed"
        LOGGER.info("_________Sdp block from composed function_______" + str(self) +str(sdp_block))
        return self, sdp_block


    def and_configure_scan_by_file(self, sdp_block, file = 'resources/test_data/OET_integration/configure2.json'):
        ##Reference tests/acceptance/mvp/test_XR-13_A2-Test.py
        @sync_configure_oet
        @time_it(120)
        def config(file, sdp_block):
            update_scan_config_file(file, sdp_block)
            LOGGER.info("___________Input file in configure_oet_____________" + str(file))
            self.state = "Configuring"
            self.SubArray.configure_from_file(file, 6, with_processing = False)
        LOGGER.info("___________SDP block from configure_oet_____________" + str(sdp_block))
        config(file, sdp_block)
        self.state = "Ready"
        return self


    def and_run_a_scan(self):
        ##Reference tests/acceptance/mvp/test_XR-13_A3-Test.py
        ##note this is a different sync decorator as test since test performs the command as non blocking
        #@sync_scan_oet
        def scan():
            self.SubArray.scan()
        scan()
        self.state = "Ready"
        return self
    
    def and_release_all_resources(self):
        @sync_release_resources
        def de_allocate():
            self.SubArray.deallocate()
        de_allocate()
        self.state = "Empty"
        return self

    def and_end_sb_when_ready(self):
        @sync_end_sb
        def end_sb():
            self.SubArray.end()
        end_sb()
        self.state = "Composed"
        return self
    
    def restart_when_aborted(self):
        @sync_restart_sa
        def restart():
            self.SubArray.restart()
        restart()
        self.state = "EMPTY"
        return self
    

    def roll_back(self):
        if self.state !='Empty':
            self.rollback_order[self.state]()
            

    def reset(self):
        while self.state != 'Empty':
            self.rollback_order[self.state]()


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


def set_telescope_to_standby():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
    the_waiter = waiter()
    the_waiter.set_wait_for_going_to_standby()
    Telescope().standby()
    #It is observed that CSP and CBF subarrays sometimes take more than 8 sec to change the State to DISABLE
    #therefore timeout is given as 12 sec
    the_waiter.wait(120)
    if the_waiter.timed_out:
        pytest.fail("timed out whilst setting telescope to standby:\n {}".format(the_waiter.logs))

def set_telescope_to_running(disable_waiting = False):
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('OFF')
    the_waiter = waiter()
    the_waiter.set_wait_for_starting_up()
    Telescope().start_up()
    if not disable_waiting:
        the_waiter.wait(100)
        if the_waiter.timed_out:
            pytest.fail("timed out whilst starting up telescope:\n {}".format(the_waiter.logs))

def telescope_is_in_standby():
    # LOGGER.info('resource("ska_mid/tm_subarray_node/1").get("State")'+ str(resource('ska_mid/tm_subarray_node/1').get("State")))
    # LOGGER.info('resource("mid_csp/elt/subarray_01").get("State")' +
    #             str(resource('mid_csp/elt/subarray_01').get("State")))
    # LOGGER.info('resource("mid_csp_cbf/sub_elt/subarray_01").get("State")' +
    #             str(resource('mid_csp_cbf/sub_elt/subarray_01').get("State")))

    return  [resource('ska_mid/tm_subarray_node/1').get("State"),
            resource('mid_csp/elt/subarray_01').get("State"),
            resource('mid_csp_cbf/sub_elt/subarray_01').get("State")] == \
            ['OFF','OFF','OFF']

## currently this function is not used in any testcase
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
