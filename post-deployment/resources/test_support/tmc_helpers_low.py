import os
import logging

from resources.test_support.sync_decorators_low import sync_start_up_telescope,sync_assign_resources,sync_configure, sync_scan, sync_end, sync_abort, sync_obsreset, sync_release_resources,sync_set_to_standby,time_it,sync_restart
from tango import DeviceProxy   
from resources.test_support.helpers_low import waiter,watch,resource
from resources.test_support.persistance_helping import load_config_from_file,update_scan_config_file,update_resource_config_file
from ska_ser_skallop.bdd_test_data_manager.data_manager import download_test_data

LOGGER = logging.getLogger(__name__)



@sync_start_up_telescope
def start_up():
    CentralNodeLow = DeviceProxy('ska_low/tm_central/central_node')
    LOGGER.info("Before Sending StartupTelescope command on CentralNodeLow state :" + str(CentralNodeLow.State()))   
    CentralNodeLow.StartUpTelescope()

@sync_assign_resources(300)
def compose_sub():
    resource('ska_low/tm_subarray_node/1').assert_attribute('State').equals('ON')
    resource('ska_low/tm_subarray_node/1').assert_attribute('obsState').equals('EMPTY')
    assign_resources_file = download_test_data(
        "low_assign_resources_v1.json", "skampi-test-data/tmc-integration/assign-resources")
    config = load_config_from_file(assign_resources_file)
    os.remove(assign_resources_file)
    CentralNodeLow = DeviceProxy('ska_low/tm_central/central_node')
    CentralNodeLow.AssignResources(config)
    the_waiter = waiter()
    the_waiter.wait()
    LOGGER.info('Invoked AssignResources on CentralNodeLow')

@sync_end
def end():
    resource('ska_low/tm_subarray_node/1').assert_attribute('obsState').equals('READY')
    resource('low-mccs/subarray/01').assert_attribute('obsState').equals('READY')
    LOGGER.info('Before invoking End Command all the devices obsstate is ready')
    SubarrayNodeLow = DeviceProxy('ska_low/tm_subarray_node/1')
    SubarrayNodeLow.End()
    LOGGER.info('Invoked End on Subarray')

@sync_release_resources
def release_resources():
    resource('ska_low/tm_subarray_node/1').assert_attribute('obsState').equals('IDLE')
    CentralNodeLow = DeviceProxy('ska_low/tm_central/central_node')
    release_resources_file = download_test_data(
        "mccs_release_resources_v1.json", "skampi-test-data/tmc-integration/release-resources")
    release_json = load_config_from_file(release_resources_file)
    os.remove(release_resources_file)
    CentralNodeLow.ReleaseResources(release_json)
    SubarrayNodeLow = DeviceProxy('ska_low/tm_subarray_node/1')
    LOGGER.info('After Invoking Release Resource on Subarray, SubarrayNodeLow State and ObsState:' + str(SubarrayNodeLow.State()) + str(SubarrayNodeLow.ObsState))
    the_waiter = waiter()
    the_waiter.wait()
    LOGGER.info('finished ReleaseResources on CentralNodeLow')

@sync_set_to_standby
def set_to_standby():
    CentralNodeLow = DeviceProxy('ska_low/tm_central/central_node')
    CentralNodeLow.StandByTelescope()
    SubarrayNodeLow = DeviceProxy('ska_low/tm_subarray_node/1')
    LOGGER.info('After Standby SubarrayNodeLow State and ObsState:' + str(SubarrayNodeLow.State()) + str(SubarrayNodeLow.ObsState))
    LOGGER.info('After Standby CentralNodeLow State:' + str(CentralNodeLow.State()))
    LOGGER.info('Standby the Telescope')

@sync_configure
def configure_sub():
    configure_file = download_test_data("low_configure_v1.json", "skampi-test-data/tmc-integration/configure")
    config = load_config_from_file(configure_file)
    os.remove(configure_file)
    SubarrayNodeLow = DeviceProxy('ska_low/tm_subarray_node/1')
    SubarrayNodeLow.Configure(config)
    LOGGER.info("Subarray obsState is: " + str(SubarrayNodeLow.obsState))
    LOGGER.info('Invoked Configure on Subarray')
    
@sync_obsreset()
def obsreset():
    resource('ska_low/tm_subarray_node/1').assert_attribute('obsState').equals('ABORTED')
    SubarrayNodeLow = DeviceProxy('ska_low/tm_subarray_node/1')
    SubarrayNodeLow.ObsReset()
    LOGGER.info("Subarray obsState is: " + str(SubarrayNodeLow.obsState))
    LOGGER.info('Invoked ObsReset command on Subarray')

@sync_restart()
def restart():
    resource('ska_low/tm_subarray_node/1').assert_attribute('obsState').equals('ABORTED')
    SubarrayNodeLow = DeviceProxy('ska_low/tm_subarray_node/1')
    SubarrayNodeLow.Restart()
    LOGGER.info("Subarray obsState is: " + str(SubarrayNodeLow.obsState))
    LOGGER.info('Invoked Restart command on Subarray')