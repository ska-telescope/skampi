from resources.test_support.sync_decorators import sync_start_up_telescope,sync_assign_resources,sync_configure,sync_end_sb,sync_release_resources,sync_set_to_standby,time_it
from resources.test_support.logging_decorators import log_it
from tango import DeviceProxy   
from resources.test_support.helpers import waiter,watch,resource
from resources.test_support.controls import set_telescope_to_standby,telescope_is_in_standby
from resources.test_support.persistance_helping import load_config_from_file,update_scan_config_file,update_resource_config_file

import logging

LOGGER = logging.getLogger(__name__)


@sync_start_up_telescope
def start_up():
    CentralNode = DeviceProxy('ska_mid/tm_central/central_node')   
    CentralNode.StartUpTelescope()

@sync_assign_resources(2,150)
def compose_sub():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('OFF')
    assign_resources_file = 'resources/test_data/TMC_integration/assign_resources1.json'
    sdp_block = update_resource_config_file(assign_resources_file)
    LOGGER.info("_______sdp_block________" + str(sdp_block))
    config = load_config_from_file(assign_resources_file)
    CentralNode = DeviceProxy('ska_mid/tm_central/central_node')
    CentralNode.AssignResources(config)
    LOGGER.info('Invoked AssignResources on CentralNode')
    return sdp_block

@sync_end_sb
def end_sb():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
    SubarrayNode.EndSB()
    LOGGER.info('Invoked EndSB on Subarray')

@sync_release_resources
def release_resources():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
    CentralNode = DeviceProxy('ska_mid/tm_central/central_node')
    CentralNode.ReleaseResources('{"subarrayID":1,"releaseALL":true,"receptorIDList":[]}')
    LOGGER.info('Invoked ReleaseResources on Subarray')


@sync_set_to_standby
def set_to_standby():
    CentralNode = DeviceProxy('ska_mid/tm_central/central_node')
    CentralNode.StandByTelescope()
    LOGGER.info('Standby the Telescope')

@sync_configure
def configure_sub(sdp_block, configure_file):
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
    update_scan_config_file(configure_file, sdp_block)
    config = load_config_from_file(configure_file)
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
    SubarrayNode.Configure(config)
    LOGGER.info('Invoked Configure on Subarray')