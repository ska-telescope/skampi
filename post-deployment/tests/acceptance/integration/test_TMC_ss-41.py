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

# @pytest.mark.skipif(DISABLE_TESTS_UNDER_DEVELOPMENT, reason="disabaled by local env")
def test_multi_scan():
    ####loging
    # s = StateChecker(devices_to_log,specific_states=non_default_states_to_check)
    # s.run(threaded=True,resolution=0.1)
    # d = DeviceLogging('DeviceLoggingImplWithDBDirect')
    # d.update_traces(devices_to_log)
    # d.start_tracing()
    ####
    try:
        # given an interface to TMC to interact with a subarray node and a central node
        CentralNode = DeviceProxy('ska_mid/tm_central/central_node')   
        SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')     
        fixture = {}
        fixture['state'] = 'Unknown'

        # given a started up telescope
        # resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('DISABLE')
        # the_waiter = waiter()
        # the_waiter.set_wait_for_starting_up()
        # LOGGER.info('starting up telescope')
        # fixture['state'] = 'Telescope Standby'
        # CentralNode.StartUpTelescope()
        # the_waiter.wait()
        assert (telescope_is_in_standby())
        LOGGER.info('Staring up the Telescope')
        tmc.start_up()
        fixture['state'] = 'Telescope On'

        # and a subarray composed of two resources configured as perTMC_integration/assign_resources.json
        # resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('OFF')
        # the_waiter.clear_watches()
        # the_waiter.set_wait_for_assign_resources()
        # LOGGER.info('assigning two dishes to subarray 1')
        # assign_resources_file = 'resources/test_data/TMC_integration/assign_resources1.json'
        # sdp_block = update_resource_config_file(assign_resources_file)
        # config = load_config_from_file(assign_resources_file)
        # CentralNode.AssignResources(config)
        # the_waiter.wait()
        LOGGER.info('Composing the Subarray')
        sdp_block = tmc.compose_sub()
        fixture['state'] = 'Subarray Assigned'

        #and for which the subarray is configured to perform a scan as per 'TMC_integration/configure1.json'
        # resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
        # the_watch = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on('obsState')
        # configure1_file = 'resources/test_data/TMC_integration/configure1.json'
        # update_scan_config_file(configure1_file, sdp_block)
        # config = load_config_from_file(configure1_file)
        # LOGGER.info('Configuring a scan for subarray 1')
        # # fixture['state'] = 'Subarray CONFIGURING'
        # SubarrayNode.Configure(config)
        # # the_watch.wait_until_value_changed_to('CONFIGURING')
        # the_watch.wait_until_value_changed_to('READY',timeout=200)
        LOGGER.info('Configuring the Subarray')
        fixture['state'] = 'Subarray CONFIGURING'
        configure_file = 'resources/test_data/TMC_integration/configure1.json'
        tmc.configure_sub(sdp_block, configure_file)
        fixture['state'] = 'Subarray Configured for SCAN'
        
        #and for which the subarray has successfully completed a scan durating 10 seconds based on previos configuration
        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
        LOGGER.info('Starting a scan of 10 seconds')
        fixture['state'] = 'Subarray SCANNING'

        @sync_scan(200)
        def scan1():
            SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
            SubarrayNode.Scan('{"id":1}')

        scan1()
        LOGGER.info('Scan1 complete')
        fixture['state'] = 'Subarray Configured for SCAN'


        # SubarrayNode.Scan('{"id":1}')
        # the_watch.wait_until_value_changed_to('SCANNING')
        # fixture['state'] = 'Subarray SCANNING'
        # #200 = 200*0.1 = 20 seconds timeout assuming scan takes 10 seconds
        # the_watch.wait_until_value_changed_to('READY',timeout=200)
        # LOGGER.info('Scan complete')
        # fixture['state'] = 'Subarray Configured for SCAN'

        #then when I load a  new configuration to perform a can as per TMC_integration/configure2.json
        # resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
        # configure2_file = 'resources/test_data/TMC_integration/configure2.json'
        # update_scan_config_file(configure2_file, sdp_block)
        # config = load_config_from_file(configure2_file)
        # LOGGER.info('Doing a new configuration for a scan on subarray 1 (testing part)')
        # SubarrayNode.Configure(config)
        # # the_watch.wait_until_value_changed_to('CONFIGURING')
        # # fixture['state'] = 'Subarray CONFIGURING'
        # the_watch.wait_until_value_changed_to('READY',timeout=200)

        LOGGER.info('Configuring the Subarray')
        fixture['state'] = 'Subarray CONFIGURING'
        configure_file = 'resources/test_data/TMC_integration/configure2.json'
        tmc.configure_sub(sdp_block, configure_file)
        fixture['state'] = 'Subarray Configured for SCAN'
        
        # and run a new scan bsed on that configruation
        # resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
        # LOGGER.info('Staring new scan of 10 seconds based on  new config (testing part)')
        # SubarrayNode.Scan('{"id":1}')
        # the_watch.wait_until_value_changed_to('SCANNING')
        # fixture['state'] = 'Subarray SCANNING'
        # #200 = 200*0.1 = 20 seconds timeout assuming scan takes 10 seconds
        # the_watch.wait_until_value_changed_to('READY',timeout=200)

        resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
        LOGGER.info('Starting a scan of 10 seconds')
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
        LOGGER.info('Tests complete: tearing down...')
        tmc.end_sb()
        tmc.release_resources()
        tmc.set_to_standby()
        # LOGGER.info('Tests complete: tearing down...')
        # resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
        # the_waiter.clear_watches()
        # the_waiter.set_wait_for_ending_SB()
        # LOGGER.info('Ending SB (take subarry back to IDLE)')
        # SubarrayNode.EndSB()
        # the_waiter.wait()
        #
        # the_waiter.clear_watches()
        # the_waiter.set_wait_for_tearing_down_subarray()
        # LOGGER.info('Releasing Resources (take subarray back to OFF)')
        # resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
        # CentralNode.ReleaseResources('{"subarrayID":1,"releaseALL":true,"receptorIDList":[]}')
        # the_waiter.wait()
        #
        # the_waiter.clear_watches()
        # the_waiter.set_wait_for_going_to_standby()
        # resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('OFF')
        # LOGGER.info('Put telescope back to standby')
        # CentralNode.StandByTelescope()
        # the_waiter.wait()
   
    except:        
        LOGGER.info("Gathering logs")
        # s.stop()
        # d.stop_tracing()
        # print_logs_to_file(s,d,status='error')
        LOGGER.info('Tearing down failed test, state = {}'.format(fixture['state']))
        if fixture['state'] == 'Telescope On':
            tmc.set_to_standby()
            # LOGGER.info('Put telescope back to standby')
            # the_waiter.clear_watches()
            # the_waiter.set_wait_for_going_to_standby()
            # resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('OFF')
            # LOGGER.info('Put telescope back to standby')
            # CentralNode.StandByTelescope()
            # the_waiter.wait()
        elif fixture['state'] == 'Subarray Assigned':
            tmc.release_resources()
            tmc.set_to_standby()
            # the_waiter.clear_watches()
            # the_waiter.set_wait_for_tearing_down_subarray()
            # LOGGER.info('Releasing Resources (take subarry back to OFF)')
            # resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
            # CentralNode.ReleaseResources('{"subarrayID":1,"releaseALL":true,"receptorIDList":[]}')
            # the_waiter.wait()
        elif fixture['state'] == 'Subarray Configured for SCAN':
            tmc.end_sb()
            tmc.release_resources()
            tmc.set_to_standby()
            # the_waiter.clear_watches()
            # the_waiter.set_wait_for_ending_SB()
            # LOGGER.info('Ending SB (take subarry back to IDLE)')
            # SubarrayNode.EndSB()
            # the_waiter.wait()
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
