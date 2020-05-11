from tango import DevState
import pytest
from time import sleep


@pytest.mark.fast
def test_startup(create_centralnode_proxy, create_subarray1_proxy):
    create_centralnode_proxy.StartUpTelescope()
    sleep(3)
    result = create_subarray1_proxy.state()
    assert result == DevState.OFF

@pytest.mark.fast
def test_assignresources_sub1(create_centralnode_proxy, create_subarray1_proxy):
    test_input = '{"subarrayID":1,"dish":{"receptorIDList":["0001"]}}'
    create_centralnode_proxy.AssignResources(test_input)
    sleep(3)
    result = create_subarray1_proxy.receptorIDList
    assert result == (1,)

@pytest.mark.xfail
def test_check_subarray_state_change_sequence(create_centralnode_proxy, create_subarray1_proxy,
                                              create_cspsubarray1_proxy, create_sdpsubarray1_proxy):
    # When ReleaseResources command is invoked, subarraynode should change its state to "OFF"
    # *after* cspsubarray and sdpsubarray change their state to "OFF"
    release_res_test_input = '{"subarrayID":1,"releaseALL":true,"receptorIDList":[]}'
    create_centralnode_proxy.ReleaseResources(release_res_test_input)
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
    assert result == DevState.DISABLE
