from tango import DeviceProxy   
from resources.test_support.helpers import waiter,watch,resource
from resources.test_support.persistance_helping import load_config_from_file

def test_multi_scan():

    CentralNode = DeviceProxy('ska_mid/tm_central/central_node')  
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')  
    assign_resources_file = 'resources/test_data/TMC_integration/assign_resources.json'
    configure1_file = 'resources/test_data/TMC_integration/configure1.json'
    configure2_file = 'resources/test_data/TMC_integration/configure2.json'


    CentralNode.StartUpTelescope()

    the_waiter = waiter()
    the_waiter.set_wait_for_assign_resources()
    config = load_config_from_file(assign_resources_file)
    SubarrayNode.AssignResources(config)
    the_waiter.wait()

    the_watch = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on('obsState')
    config = load_config_from_file(configure1_file)
    SubarrayNode.Configure(config)
    the_watch.wait_until_value_changed_to('READY')

    SubarrayNode.Scan('{"id":1}')
    the_watch.wait_until_value_changed_to('READY')
    
 
    config = load_config_from_file(configure2_file)
    SubarrayNode.Configure(config)
    the_watch.wait_until_value_changed_to('READY')

    SubarrayNode.Scan('{"id":1}')
    the_watch.wait_until_value_changed_to('READY')

    the_waiter.clear_watches()
    the_waiter.set_wait_for_ending_SB()
    SubarrayNode.EndSB()
    the_waiter.wait()

    the_waiter.clear_watches()
    the_waiter.set_wait_for_tearing_down_subarray()
    SubarrayNode.ReleaseResources('{"subarrayID":1,"releaseALL":true,"receptorIDList":[]}')
    the_waiter.wait()

    the_waiter.clear_watches()
    the_waiter.set_wait_for_going_to_standby()
    CentralNode.StandByTelescope()
    the_waiter.wait()