
import logging
import os

from resources.test_support.sync_decorators import sync_start_up_telescope,sync_assign_resources,sync_configure,sync_end_sb,sync_release_resources,sync_set_to_standby,time_it,sync_abort,sync_restart,sync_obsreset, sync_configuring, sync_resetting
from tango import DeviceProxy   
from resources.test_support.helpers import waiter,watch,resource
from resources.test_support.controls import set_telescope_to_standby,telescope_is_in_standby
from resources.test_support.persistance_helping import load_config_from_file,update_scan_config_file,update_resource_config_file
from ska_ser_skallop.bdd_test_data_manager.data_manager import download_test_data

LOGGER = logging.getLogger(__name__)


@sync_start_up_telescope
def start_up():
    CentralNode = DeviceProxy('ska_mid/tm_central/central_node')
    LOGGER.info("Before Sending TelescopeOn command on CentralNode state :" + str(CentralNode.telescopeState))
    CentralNode.TelescopeOn()

@sync_assign_resources(2,300)
def compose_sub():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('EMPTY')
    assign_resources_file = download_test_data(
        "mid_assign_resources_v1.json", "skampi-test-data/tmc-integration/assign-resources")
    sdp_block = update_resource_config_file(assign_resources_file)
    LOGGER.info("_______sdp_block________" + str(sdp_block))
    config = load_config_from_file(assign_resources_file)
    os.remove(assign_resources_file)
    CentralNode = DeviceProxy('ska_mid/tm_central/central_node')
    CentralNode.AssignResources(config)
    the_waiter = waiter()
    the_waiter.wait()
    LOGGER.info('Invoked AssignResources on CentralNode')
    return sdp_block

@sync_end_sb
def end_sb():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
    resource('mid_csp/elt/subarray_01').assert_attribute('obsState').equals('READY')
    resource('mid_sdp/elt/subarray_1').assert_attribute('obsState').equals('READY')
    LOGGER.info('Before invoking End Command all the devices obsstate is ready')
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
    SubarrayNode.End()
    LOGGER.info('Invoked End on Subarray')

@sync_release_resources
def release_resources():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
    CentralNode = DeviceProxy('ska_mid/tm_central/central_node')
    CentralNode.ReleaseResources('{"interface":"https://schema.skao.int/ska-tmc-releaseresources/2.0","transaction_id":"txn-....-00001","subarray_id":1,"release_all":true,"receptor_ids":[]}')
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
    LOGGER.info('After Release Resource SubarrayNode State and ObsState:' + str(SubarrayNode.State()) + str(SubarrayNode.ObsState))
    LOGGER.info('Invoked ReleaseResources on Subarray')


@sync_set_to_standby
def set_to_standby():
    CentralNode = DeviceProxy('ska_mid/tm_central/central_node')
    CentralNode.TelescopeOff()
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
    LOGGER.info('After Standby SubarrayNode State and ObsState:' + str(SubarrayNode.State()) + str(SubarrayNode.ObsState))
    LOGGER.info('After Standby CentralNode State:' + str(CentralNode.telescopeState))
    LOGGER.info('Standby the Telescope')

@sync_configure
def configure_sub(sdp_block, configure_file):
    #resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
    update_scan_config_file(configure_file, sdp_block)
    config = load_config_from_file(configure_file)
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
    SubarrayNode.Configure(config)
    LOGGER.info("Subarray obsState is: " + str(SubarrayNode.obsState))
    LOGGER.info('Invoked Configure on Subarray')

@sync_configuring
def configuring_sub(sdp_block, configure_file):
    update_scan_config_file(configure_file, sdp_block)
    config = load_config_from_file(configure_file)
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
    SubarrayNode.Configure(config)
    LOGGER.info("Subarray obsState is: " + str(SubarrayNode.obsState))
    LOGGER.info('Invoked Configure on Subarray')

@sync_abort
def abort():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
    SubarrayNode.Abort()
    LOGGER.info("Subarray obsState is: " + str(SubarrayNode.obsState))
    LOGGER.info('Invoked Abort on Subarray')

@sync_restart
def restart():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('ABORTED')
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
    SubarrayNode.restart()
    LOGGER.info("Subarray obsState is: " + str(SubarrayNode.obsState))
    LOGGER.info('Invoked restart on Subarray')

@sync_obsreset
def obsreset():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('ABORTED')
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
    SubarrayNode.ObsReset()
    LOGGER.info("Subarray obsState is: " + str(SubarrayNode.obsState))
    LOGGER.info('Invoked Obsreset on Subarray')

@sync_resetting(200)
def sub_resetting():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
    resource('ska_mid/tm_subarray_node/1').assert_attribute('obsState').equals('ABORTED')
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')
    LOGGER.info("Subarray obsState before ObsReset: " + str(SubarrayNode.obsState))
    SubarrayNode.ObsReset()
    LOGGER.info('Invoked Obsreset on Subarray')
    LOGGER.info("Subarray obsState is: " + str(SubarrayNode.obsState))
    