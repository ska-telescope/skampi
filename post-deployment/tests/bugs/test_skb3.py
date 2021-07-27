from resources.test_support.helpers import resource,watch,waiter
from resources.test_support.controls import set_telescope_to_standby,telescope_is_in_standby
import pytest
from tango import DeviceProxy

import logging
LOGGER = logging.getLogger(__name__)

@pytest.mark.skip
@pytest.mark.skamid
def test_tm_subarray_inconsistent_at_start_up():
    try:
        the_waiter = waiter()
        the_waiter.set_wait_for_starting_up()
        resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('DISABLE')
        #when I Startup the telescope and the TM subbarray reports its state as being OFF
        CentralNode = DeviceProxy('ska_mid/tm_central/central_node')  
        # the_watch = watch(resource('ska_mid/tm_subarray_node/1')).for_a_change_on('State')
        CentralNode.TelescopeOn()
        # CentralNode.StartUpTelescope()
        the_waiter.wait()
        # the_watch.wait_until_value_changed_to('OFF')
        #then the children subarray devices should also be in state OFF
        resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('OFF')
        resource('mid_sdp/elt/subarray_1').assert_attribute('State').equals('OFF')
        resource('mid_csp/elt/subarray_01').assert_attribute('State').equals('OFF')
        resource('mid_csp_cbf/sub_elt/subarray_01').assert_attribute('State').equals('OFF')
        #teardown
    finally:
        if not telescope_is_in_standby():
            set_telescope_to_standby()




    
#these tests are all wrong, there should not be any sleep commands to make it pass!
'''
@pytest.mark.fast
def test_startup(create_centralnode_proxy, create_subarray1_proxy):
    create_centralnode_proxy.StartUpTelescope()
    sleep(3)
    result = create_subarray1_proxy.state()
    assert result == DevState.OFF

@pytest.mark.fast
def test_assignresources_sub1(create_centralnode_proxy, create_subarray1_proxy):
    test_input = '{"subarrayID":1,"dish":{"receptorIDList":["0001"]},"sdp":{"id":"sbi-mvp01-20200325-00001","max_length":100.0,"scan_types":[{"id":"science_A","coordinate_system":"ICRS","ra":"02:42:40.771","dec":"-00:00:47.84","subbands":[{"freq_min":0.35e9,"freq_max":1.05e9,"nchan":372,"input_link_map":[[1,0],[101,1]]}]},{"id":"calibration_B","coordinate_system":"ICRS","ra":"12:29:06.699","dec":"02:03:08.598","subbands":[{"freq_min":0.35e9,"freq_max":1.05e9,"nchan":372,"input_link_map":[[1,0],[101,1]]}]}],"processing_blocks":[{"id":"pb-mvp01-20200325-00001","workflow":{"type":"realtime","id":"vis_receive","version":"0.1.0"},"parameters":{}},{"id":"pb-mvp01-20200325-00002","workflow":{"type":"realtime","id":"test_realtime","version":"0.1.0"},"parameters":{}},{"id":"pb-mvp01-20200325-00003","workflow":{"type":"batch","id":"ical","version":"0.1.0"},"parameters":{},"dependencies":[{"pb_id":"pb-mvp01-20200325-00001","type":["visibilities"]}]},{"id":"pb-mvp01-20200325-00004","workflow":{"type":"batch","id":"dpreb","version":"0.1.0"},"parameters":{},"dependencies":[{"pb_id":"pb-mvp01-20200325-00003","type":["calibration"]}]}]}}'
    create_centralnode_proxy.AssignResources(test_input)
    sleep(3)
    result = create_subarray1_proxy.receptorIDList
    assert result == (1,)
    release_res_test_input = '{"subarrayID":1,"releaseALL":true,"receptorIDList":[]}'
    create_centralnode_proxy.ReleaseResources(release_res_test_input)

@pytest.mark.xfail
def test_check_subarray_state_change_sequence(create_centralnode_proxy, create_subarray1_proxy,
                                              create_cspsubarray1_proxy, create_sdpsubarray1_proxy):
    # When ReleaseResources command is invoked, subarraynode should change its state to "OFF"
    # *after* cspsubarray and sdpsubarray change their state to "OFF"
    # TODO: For future reference
    # release_res_test_input = '{"subarrayID":1,"releaseALL":true,"receptorIDList":[]}'
    # create_centralnode_proxy.ReleaseResources(release_res_test_input)
    assert ((create_cspsubarray1_proxy.state() == DevState.OFF or
             create_sdpsubarray1_proxy.state() == DevState.OFF) and
            create_subarray1_proxy.state() == DevState.ON)
    sleep(3)
    assert ((create_cspsubarray1_proxy.state() == DevState.OFF or
             create_sdpsubarray1_proxy.state() == DevState.OFF) and
            create_subarray1_proxy.state() == DevState.OFF)


@pytest.mark.fast
def test_standby(create_centralnode_proxy, create_subarray1_proxy):
    sleep(1)
    create_centralnode_proxy.StandByTelescope()
    sleep(2)
    result = create_subarray1_proxy.state()
    assert result == DevState.DISABLE'''
