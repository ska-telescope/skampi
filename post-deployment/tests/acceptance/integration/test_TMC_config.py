from tango import DeviceProxy   
from datetime import date,datetime
import os
import pytest
import logging
from resources.test_support.helpers import waiter,watch,resource
from resources.test_support.controls import telescope_is_in_standby
from resources.test_support.state_checking import StateChecker
from resources.test_support.log_helping import DeviceLogging
from resources.test_support.persistance_helping import load_config_from_file,update_scan_config_file,update_resource_config_file
from resources.test_support.sync_decorators import sync_start_up_telescope,sync_assign_resources,sync_configure,sync_end_sb,sync_release_resources,sync_set_to_standby,time_it
from resources.test_support.logging_decorators import log_it
import resources.test_support.tmc_helpers as tmc
import time

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
# @pytest.mark.select
@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
def test_configure_scan():
    
    try:
        # given an interface to TMC to interact with a subarray node and a central node
        fixture = {}
        fixture['state'] = 'Unknown'

        # given a started up telescope
        assert(telescope_is_in_standby())
        LOGGER.info('Staring up the Telescope')
        tmc.start_up()
        fixture['state'] = 'Telescope On'
        
        # and a subarray composed of two resources configured as perTMC_integration/assign_resources.json
        LOGGER.info('Composing the Subarray')
        sdp_block = tmc.compose_sub()
        fixture['state'] = 'Subarray Assigned'

        #then when I configure a subarray to perform a scan as per 'TMC_integration/configure1.json'
        @log_it('TMC_int_configure',devices_to_log,non_default_states_to_check)
        @sync_configure
        @time_it(90)
        def configure_sub(sdp_block):
            #commented because below asserts are already checked in @sync_configure
            # resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
            # resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
            configure1_file = 'resources/test_data/TMC_integration/configure1.json'
            update_scan_config_file(configure1_file, sdp_block)
            config = load_config_from_file(configure1_file)
            LOGGER.info('Configuring a scan for subarray 1')
            fixture['state'] = 'Subarray CONFIGURING'
            SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
            SubarrayNode.Configure(config)
            LOGGER.info('Invoked Configure on Subarray')
        configure_sub(sdp_block)
        fixture['state'] = 'Subarray Configured for SCAN'
    
        #tear down
        LOGGER.info('TMC-configure tests complete: tearing down...')
        tmc.end_sb()
        LOGGER.info('Invoked EndSB on Subarray')
        DishMaster1 = DeviceProxy('mid_d0001/elt/master')
        DishMaster2 = DeviceProxy('mid_d0002/elt/master')
        LOGGER.info('After EndSB pointingState of Dish1:' + str(DishMaster1.pointingState))
        LOGGER.info('After EndSB pointingState of Dish2:' + str(DishMaster2.pointingState))
        
        tmc.release_resources()
        LOGGER.info('Invoked ReleaseResources on Subarray')
        
        tmc.set_to_standby()
        LOGGER.info('Invoked StandBy on Subarray')


    except:        
        LOGGER.info('Tearing down failed test, state = {}'.format(fixture['state']))
        if fixture['state'] == 'Telescope On':
            tmc.set_to_standby()
        elif fixture['state'] == 'Subarray Assigned':
            tmc.release_resources()
            tmc.set_to_standby()
        elif fixture['state'] == 'Subarray Configured for SCAN':
            LOGGER.info('Tearing down in , state = {}'.format(fixture['state']))
            tmc.end_sb()
            tmc.release_resources()
            tmc.set_to_standby()
        elif fixture['state'] == 'Subarray SCANNING':
            raise Exception('unable to teardown subarray from being in SCANNING')
        elif fixture['state'] == 'Subarray CONFIGURING':
            raise Exception('unable to teardown subarray from being in CONFIGURING')
        pytest.fail("unable to complete test without exceptions")
