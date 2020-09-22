from tango import DeviceProxy   
from datetime import date,datetime
from time import sleep
import os
import pytest
import logging
from resources.test_support.helpers import waiter,watch,resource
from resources.test_support.state_checking import StateChecker
from resources.test_support.log_helping import DeviceLogging
from resources.test_support.logging_decorators import log_states
from resources.test_support.persistance_helping import load_config_from_file,update_scan_config_file,update_resource_config_file
import resources.test_support.tmc_helpers as tmc
from resources.test_support.controls import telescope_is_in_standby
from resources.test_support.sync_decorators import sync_scanning

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
#@pytest.mark.skip(reason="Fails randomly")
@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
def test_multi_scan():

    ####
    try:
        the_waiter = waiter()
        fixture = {}
        fixture['state'] = 'Unknown'

        # given a started up telescope
        LOGGER.info('Checking if Telescope is in StandBy')
        assert (telescope_is_in_standby())
        LOGGER.info('Telescope is in StandBy')
        tmc.start_up()
        LOGGER.info('Staring up the Telescope')
        fixture['state'] = 'Telescope On'

        # and a subarray composed of two resources configured as perTMC_integration/assign_resources1.json
        sdp_block = tmc.compose_sub()
        LOGGER.info('Composing the Subarray')
        fixture['state'] = 'Subarray Assigned'

        #and for which the subarray is configured to perform a scan as per 'TMC_integration/configure1.json'
        fixture['state'] = 'Subarray CONFIGURING'
        configure_file = 'resources/test_data/TMC_integration/configure2.json'
        tmc.configure_sub(sdp_block, configure_file)
        LOGGER.info('Configuring the Subarray')
        fixture['state'] = 'Subarray Configured for SCAN'
        
        #and for which the subarray has successfully completed a scan durating 6 seconds based on previos configuration
        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
        LOGGER.info('Starting a scan of 6 seconds')

        with log_states('TMC_ss-41-scan1',devices_to_log,non_default_states_to_check):
            with sync_scanning(200):
                SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
                SubarrayNode.Scan('{"id":1}')
                fixture['state'] = 'Subarray SCANNING'
                LOGGER.info("Subarray obsState is: " + str(SubarrayNode.obsState))
                LOGGER.info("Scan 1  is executing on Subarray")

        LOGGER.info('Scan1 complete')
        fixture['state'] = 'Subarray Configured for SCAN'

        #then when I load a  new configuration to perform a can as per TMC_integration/configure2.json
        LOGGER.info('Configuring the Subarray')
        fixture['state'] = 'Subarray CONFIGURING'
        configure_file = 'resources/test_data/TMC_integration/configure1.json'
        tmc.configure_sub(sdp_block, configure_file)
        LOGGER.info('Configuring the Subarray')
        fixture['state'] = 'Subarray Configured for SCAN'
        
        # and run a new scan bsed on that configuration
        resource('mid_csp/elt/subarray_01').assert_attribute('obsState').equals('READY')
        resource('mid_csp_cbf/sub_elt/subarray_01').assert_attribute('obsState').equals('READY')
        resource('mid_sdp/elt/subarray_1').assert_attribute('obsState').equals('READY')
        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
        LOGGER.info('Starting a scan of 6 seconds')

        with log_states('TMC_ss-41-scan2',devices_to_log,non_default_states_to_check):
            with sync_scanning(200):
                LOGGER.info('Check obsstate again before starting 2nd scan')
                resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
                resource('mid_csp/elt/subarray_01').assert_attribute('obsState').equals('READY')
                resource('mid_csp_cbf/sub_elt/subarray_01').assert_attribute('obsState').equals('READY')
                resource('mid_sdp/elt/subarray_1').assert_attribute('obsState').equals('READY')
        
                SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
                SubarrayNode.Scan('{"id":1}')
                fixture['state'] = 'Subarray SCANNING'
                LOGGER.info("Subarray obsState is: " + str(SubarrayNode.obsState))
        LOGGER.info('Scan2 complete')
        fixture['state'] = 'Subarray Configured for SCAN'

        #the scanning should complete without any exceptions
        #TODO possibly add some other asserts in here

        #tear down
        LOGGER.info('TMC-multiscan tests complete: tearing down...')
        tmc.end_sb()
        the_waiter.wait()
        LOGGER.info("Invoked EndSB on Subarray")
        tmc.release_resources()
        the_waiter.wait()
        LOGGER.info('Invoked ReleaseResources on Subarray')
        tmc.set_to_standby()
        LOGGER.info('Invoked StandBy on Subarray')
        the_waiter.wait()
        LOGGER.info('Invoked StandBy on Subarray')
        LOGGER.info('Tests complete: tearing down...')

    except Exception as e:     
        logging.info(f'Exception raised: {e.args}')  
        LOGGER.info("Gathering logs")
        LOGGER.info('Tearing down failed test, state = {}'.format(fixture['state']))
        if fixture['state'] == 'Telescope On':
            tmc.set_to_standby()
            the_waiter.wait()
        elif fixture['state'] == 'Subarray Assigned':
            tmc.release_resources()
            the_waiter.wait()
            tmc.set_to_standby()
            the_waiter.wait()
        elif fixture['state'] == 'Subarray Configured for SCAN':
            tmc.end_sb()
            the_waiter.wait()
            tmc.release_resources()
            the_waiter.wait()
            tmc.set_to_standby()
            the_waiter.wait()
        elif fixture['state'] == 'Subarray SCANNING':
            if resource('ska_mid/tm_subarray_node/1').get('obsState') == 'SCANNING':
                raise Exception('unable to teardown subarray from being in SCANNING')
            else:
                #sleep arbitrary number here to handle possible failures in un-idempotentcy
                sleep(3)
                tmc.end_sb()
                the_waiter.wait()
                tmc.release_resources()
                the_waiter.wait()
                tmc.set_to_standby()
                the_waiter.wait()
                raise e
        elif fixture['state'] == 'Subarray CONFIGURING':
            raise Exception('unable to teardown subarray from being in CONFIGURING')
        elif fixture['state'] == 'Unknown':
            LOGGER.info('Put telescope back to standby')
            tmc.set_to_standby()
            the_waiter.wait()
        pytest.fail("unable to complete test without exceptions")

