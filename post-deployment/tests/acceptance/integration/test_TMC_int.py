from tango import DeviceProxy   
import logging
from resources.test_support.helpers import waiter,watch,resource
from resources.test_support.persistance_helping import load_config_from_file

LOGGER = logging.getLogger(__name__)

def test_multi_scan():

    # given an interface to TMC to interact with a subarray node and a central node
    CentralNode = DeviceProxy('ska_mid/tm_central/central_node')  
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')  
    # given a started up telescope
    LOGGER.info('stating up telescope')
    CentralNode.StartUpTelescope()

    # and a subarray composed of two resources confired as perTMC_integration/assign_resources.json
    the_waiter = waiter()
    the_waiter.set_wait_for_assign_resources()
    LOGGER.info('assigning two dishes to subarray 1')
    assign_resources_file = 'resources/test_data/TMC_integration/assign_resources.json'
    config = load_config_from_file(assign_resources_file)
    SubarrayNode.AssignResources(config)
    the_waiter.wait()

    #and for which the subarray is configured to perform a scan as per 'TMC_integration/configure1.json'
    the_watch = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on('obsState')
    configure1_file = 'resources/test_data/TMC_integration/configure1.json'
    config = load_config_from_file(configure1_file)
    LOGGER.info('Configuring a scan for subarray 1')
    SubarrayNode.Configure(config)
    the_watch.wait_until_value_changed_to('READY')
    
    #and for which the subarray has successfully completed a scan durating 10 seconds based on previos configuration
    LOGGER.info('Staring a scan of 10 seconds')
    SubarrayNode.Scan('{"id":1}')
    the_watch.wait_until_value_changed_to('READY')
    LOGGER.info('Scan complete')

    #then when I load a  new configuration to perform a can as per TMC_integration/configure2.json
    configure2_file = 'resources/test_data/TMC_integration/configure2.json'
    config = load_config_from_file(configure2_file)
    LOGGER.info('Doing a new configuration for a scan on subarray 1 (testing part)')
    SubarrayNode.Configure(config)
    the_watch.wait_until_value_changed_to('READY')
    
    # and run a new scan bsed on that configruation
    LOGGER.info('Staring new scan of 10 seconds based on  new config (testing part)')
    SubarrayNode.Scan('{"id":1}')
    #200 = 200*0.1 = 20 seconds timeout assuming scan takes 10 seconds
    the_watch.wait_until_value_changed_to('READY',timeout=200)

    #the scanning should complete without any exceptions
    #TODO possible add some other asserts in here

    #tear down
    LOGGER.info('Tests complete: tearing down...')
    the_waiter.clear_watches()
    the_waiter.set_wait_for_ending_SB()
    LOGGER.info('Ending SB (take subarry back to IDLE)')
    SubarrayNode.EndSB()
    the_waiter.wait()

    the_waiter.clear_watches()
    the_waiter.set_wait_for_tearing_down_subarray()
    LOGGER.info('Releasing Resources (take subarry back to OFF)')
    CentralNode.ReleaseResources('{"subarrayID":1,"releaseALL":true,"receptorIDList":[]}')
    the_waiter.wait()

    the_waiter.clear_watches()
    the_waiter.set_wait_for_going_to_standby()
    LOGGER.info('Put telescope back to standby')
    CentralNode.StandByTelescope()
    the_waiter.wait()