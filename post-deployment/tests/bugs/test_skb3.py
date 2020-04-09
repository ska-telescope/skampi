import logging
from tango import DevState
from resources.test_support.helpers import resource, watch
import pytest
from time import sleep


@pytest.mark.xfail(reason="subarray node is not in sync with cspsuarray state.")
def test_check_subarray_state_change_sequence(create_centralnode_proxy, create_subarray1_proxy,
                                              create_cspsubarray1_proxy, create_sdpsubarray1_proxy):
    create_centralnode_proxy.StartUpTelescope()
    sleep(3)

    assign_res_test_input = '{"subarrayID":1,"dish":{"receptorIDList":["0001","0002"]}}'
    create_centralnode_proxy.AssignResources(assign_res_test_input)

    sleep(3)

    # When ReleaseResources command is invoked, subarraynode should change its state to "OFF"
    # *after* cspsubarray and sdpsubarray change their state to "OFF"
    release_res_test_input = '{"subarrayID":1,"releaseALL":true,"receptorIDList":[]}'
    create_centralnode_proxy.ReleaseResources(release_res_test_input)
    logging.info("cspsubarray1 state: " + resource('mid_csp/elt/subarray_01').get("State"))
    logging.info("sdpsubarray1 state: " + resource('mid_sdp/elt/subarray_1').get("State"))
    logging.info("subarray1 state: " + resource('ska_mid/tm_subarray_node/1').get("State"))

    assert ((create_cspsubarray1_proxy.state() == DevState.OFF or
             create_sdpsubarray1_proxy.state() == DevState.OFF) and
            create_subarray1_proxy.state() == DevState.ON)

    sleep(3)
    logging.info("cspsubarray1 state: " + resource('mid_csp/elt/subarray_01').get("State"))
    logging.info("sdpsubarray1 state: " + resource('mid_sdp/elt/subarray_1').get("State"))
    logging.info("subarray1 state: " + resource('ska_mid/tm_subarray_node/1').get("State"))

    assert ((create_cspsubarray1_proxy.state() == DevState.OFF or
             create_sdpsubarray1_proxy.state() == DevState.OFF) and
            create_subarray1_proxy.state() == DevState.OFF)


def test_standby(create_centralnode_proxy, create_subarray1_proxy):
    sleep(2)
    create_centralnode_proxy.StandByTelescope()
    sleep(3)
    result = create_subarray1_proxy.state()
    assert result == DevState.DISABLE
