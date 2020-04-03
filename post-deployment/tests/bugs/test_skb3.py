from time import sleep
import json
from tango import DevState


def test_init():
    print("Init test multisubarray")


def test_check_subarray_state_change_sequence(create_centralnode_proxy, create_subarray1_proxy,
                                              create_cspsubarray1_proxy, create_sdpsubarray1_proxy):
    create_centralnode_proxy.StartUpTelescope()
    sleep(3)
    assign_res_test_input = '{"subarrayID":1,"dish":{"receptorIDList":["0001","0002"]}}'
    create_centralnode_proxy.AssignResources(assign_res_test_input)
    sleep(3)
    release_res_test_input = '{"subarrayID":1,"releaseALL":true,"receptorIDList":[]}'
    json.loads(create_centralnode_proxy.ReleaseResources(release_res_test_input))
    assert ((create_cspsubarray1_proxy.state() == DevState.OFF or
             create_sdpsubarray1_proxy.state() == DevState.OFF) and
            create_subarray1_proxy.state() == DevState.ON)
    sleep(1)
    assert ((create_cspsubarray1_proxy.state() == DevState.OFF or
             create_sdpsubarray1_proxy.state() == DevState.OFF) and
            create_subarray1_proxy.state() == DevState.OFF)
    create_centralnode_proxy.StandByTelescope()
