from tango import DeviceProxy   
from datetime import date,datetime
import os
import pytest
import logging
from resources.test_support.helpers import waiter,watch,resource
from resources.test_support.state_checking import StateChecker
from resources.test_support.log_helping import DeviceLogging
from resources.test_support.persistance_helping import load_config_from_file,update_scan_config_file,update_resource_config_file
import resources.test_support.tmc_helpers as tmc
from resources.test_support.controls import telescope_is_in_standby
from resources.test_support.sync_decorators import sync_scan

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

def print_logs_to_file(s,d,status='ok'):
    if status=='ok':
        filename_d = 'logs_test_TMC_int_{}.csv'.format(datetime.now().strftime('%d_%m_%Y-%H_%M'))
        filename_s = 'states_test_TMC_int__{}.csv'.format(datetime.now().strftime('%d_%m_%Y-%H_%M'))
    elif status=='error':
        filename_d = 'error_logs_test_TMC_int__{}.csv'.format(datetime.now().strftime('%d_%m_%Y-%H_%M'))
        filename_s = 'error_states_test_TMC_int__{}.csv'.format(datetime.now().strftime('%d_%m_%Y-%H_%M'))
    LOGGER.info("Printing log files to build/{} and build/{}".format(filename_d,filename_s))
    d.implementation.print_log_to_file(filename_d,style='csv')
    s.print_records_to_file(filename_s,style='csv',filtered=False)

#@pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
def test_multi_scan():
    ####loging
    # s = StateChecker(devices_to_log,specific_states=non_default_states_to_check)
    # s.run(threaded=True,resolution=0.1)
    # d = DeviceLogging('DeviceLoggingImplWithDBDirect')
    # d.update_traces(devices_to_log)
    # d.start_tracing()
    ####
    try:
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
        configure_file = 'resources/test_data/TMC_integration/configure1.json'
        tmc.configure_sub(sdp_block, configure_file)
        LOGGER.info('Configuring the Subarray')
        fixture['state'] = 'Subarray Configured for SCAN'
        
        #and for which the subarray has successfully completed a scan durating 6 seconds based on previos configuration
        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
        LOGGER.info('Starting a scan of 6 seconds')
        fixture['state'] = 'Subarray SCANNING'

        @sync_scan(200)
        def scan1():
            SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
            SubarrayNode.Scan('{"id":1}')
            LOGGER.info("Scan 1  is executing on Subarray")
            
        scan1()
        LOGGER.info('Scan1 complete')
        fixture['state'] = 'Subarray Configured for SCAN'

        #then when I load a  new configuration to perform a can as per TMC_integration/configure2.json
        LOGGER.info('Configuring the Subarray')
        fixture['state'] = 'Subarray CONFIGURING'
        configure_file = 'resources/test_data/TMC_integration/configure2.json'
        tmc.configure_sub(sdp_block, configure_file)
        fixture['state'] = 'Subarray Configured for SCAN'
        
        # and run a new scan bsed on that configuration
        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
        LOGGER.info('Starting a scan of 6 seconds')
        fixture['state'] = 'Subarray SCANNING'

        @sync_scan(200)
        def scan2():
            SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
            SubarrayNode.Scan('{"id":2}')
        scan2()
        LOGGER.info('Scan2 complete')
        fixture['state'] = 'Subarray Configured for SCAN'

        #the scanning should complete without any exceptions
        #TODO possibly add some other asserts in here

        #tear down
        LOGGER.info('TMC-multiscan tests complete: tearing down...')
        tmc.end_sb()
        LOGGER.info("Invoked EndSB on Subarray")
        tmc.release_resources()
        LOGGER.info('Invoked ReleaseResources on Subarray')
        tmc.set_to_standby()
        LOGGER.info('Invoked StandBy on Subarray')
        LOGGER.info('Tests complete: tearing down...')

    except:        
        LOGGER.info("Gathering logs")
        # s.stop()
        # d.stop_tracing()
        # print_logs_to_file(s,d,status='error')
        LOGGER.info('Tearing down failed test, state = {}'.format(fixture['state']))
        if fixture['state'] == 'Telescope On':
            tmc.set_to_standby()
        elif fixture['state'] == 'Subarray Assigned':
            tmc.release_resources()
            tmc.set_to_standby()
        elif fixture['state'] == 'Subarray Configured for SCAN':
            tmc.end_sb()
            tmc.release_resources()
            tmc.set_to_standby()
        elif fixture['state'] == 'Subarray SCANNING':
            raise Exception('unable to teardown subarray from being in SCANNING')
        elif fixture['state'] == 'Subarray CONFIGURING':
            raise Exception('unable to teardown subarray from being in CONFIGURING')
        elif fixture['state'] == 'Unknown':
            LOGGER.info('Put telescope back to standby')
            # CentralNode.StandByTelescope()
            tmc.set_to_standby()
        pytest.fail("unable to complete test without exceptions")

    LOGGER.info("Gathering logs")
    # s.stop()
    # d.stop_tracing()
    # print_logs_to_file(s,d,status='ok')
