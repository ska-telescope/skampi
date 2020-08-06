from tango import DeviceProxy   
from datetime import date,datetime
import pytest
import os
import logging
from resources.test_support.helpers import waiter,watch,resource
from resources.test_support.controls import telescope_is_in_standby
from resources.test_support.state_checking import StateChecker
from resources.test_support.log_helping import DeviceLogging
from resources.test_support.persistance_helping import load_config_from_file,update_scan_config_file,update_resource_config_file
from resources.test_support.sync_decorators import sync_start_up_telescope,sync_assign_resources,sync_configure,sync_end_sb,sync_release_resources,sync_set_to_standby,time_it
from resources.test_support.logging_decorators import log_it
import resources.test_support.tmc_helpers as tmc

DEV_TEST_TOGGLE = os.environ.get('DISABLE_DEV_TESTS')
if DEV_TEST_TOGGLE == "False":
    DISABLE_TESTS_UNDER_DEVELOPMENT = False
else:
    DISABLE_TESTS_UNDER_DEVELOPMENT = True

devices_to_log = [
    'ska_mid/tm_subarray_node/1',
    'mid_csp/elt/subarray_01',
    'mid_csp_cbf/sub_elt/subarray_01',
    'mid_sdp/elt/subarray_1',
    'mid_d0001/elt/master',
    'mid_d0002/elt/master',
    'mid_d0003/elt/master',
    'mid_d0004/elt/master']
non_default_states_to_check = {
    'mid_d0001/elt/master' : 'pointingState',
    'mid_d0002/elt/master' : 'pointingState',
    'mid_d0003/elt/master' : 'pointingState',
    'mid_d0004/elt/master' : 'pointingState'}

LOGGER = logging.getLogger(__name__)
@pytest.mark.select
#@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
def test_assign_resources():
    
    try:
        # given an interface to TMC to interact with a subarray node and a central node
        fixture = {}
        fixture['state'] = 'Unknown'

        # given a started up telescope
        assert(telescope_is_in_standby())
        LOGGER.info('Staring up the Telescope')
        tmc.start_up()
        fixture['state'] = 'Telescope On'
        
        # then when I assign a subarray composed of two resources configured as perTMC_integration/assign_resources.json
        @log_it('TMC_int_comp',devices_to_log,non_default_states_to_check)
        @sync_assign_resources(2,150)
        def compose_sub():
            resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
            resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('EMPTY')
            assign_resources_file = 'resources/test_data/TMC_integration/assign_resources1.json'
            update_resource_config_file(assign_resources_file)
            config = load_config_from_file(assign_resources_file)
            CentralNode = DeviceProxy('ska_mid/tm_central/central_node')
            CentralNode.AssignResources(config)
            LOGGER.info('Invoked AssignResources on CentralNode')
        compose_sub()
   
        #tear down
        LOGGER.info('Tests complete: tearing down...')
        tmc.release_resources()
        tmc.set_to_standby()
   
    except:        
        LOGGER.info('Tearing down failed test, state = {}'.format(fixture['state']))
        if fixture['state'] == 'Telescope On':
            tmc.set_to_standby()
        elif fixture['state'] == 'Subarray Assigned':
            tmc.release_resources()
            tmc.set_to_standby()
        raise

