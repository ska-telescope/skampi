from tango import DeviceProxy   
from resources.test_support.helpers import waiter



def test_multi_scan():
    
    CentralNode = DeviceProxy('ska_mid/tm_central/central_node')  
    SubarrayNode = DeviceProxy('ska_mid/tm_subarray_node/1')  

    CentralNode.StartUpTelescope()

    the_waiter = waiter()
    the_waiter.set_wait_for_assign_resources()
    SubarrayNode.AssignResources()
    the_waiter.wait()

    SubarrayNode.Confgure()
    #TODO add script to wait untill ready

    SubarrayNode.Scan()
    #TODO add script to wait untill scan finished

    SubarrayNode.Confgure()
    #TODO add script to wait untill ready

    SubarrayNode.Scan()
    #TODO add script to wait untill scan finished

    the_waiter = waiter()
    the_waiter.set_wait_for_ending_SB()
    SubarrayNode.EndSB()
    the_waiter.wait()

    the_waiter = waiter()
    the_waiter.set_wait_for_tearing_down_subarray()
    SubarrayNode.ReleaseResources()
    the_waiter.wait()

    the_waiter = waiter()
    the_waiter.set_wait_for_going_to_standby()
    CentralNode.StandByTelescope()
    the_waiter.wait()