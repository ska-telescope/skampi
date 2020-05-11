from time import sleep
import json
from tango import DevState
import pytest

def test_init():
  print("Init test multisubarray")

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

@pytest.mark.fast
def test_assignresouce_sub2(create_centralnode_proxy, create_subarray2_proxy):
    test_input = '{"subarrayID":2,"dish":{"receptorIDList":["0003"]}}'
    create_centralnode_proxy.AssignResources(test_input)
    sleep(3)
    result = create_subarray2_proxy.receptorIDList
    assert result == (3,)

@pytest.mark.fast
def test_assignresouce_sub3(create_centralnode_proxy, create_subarray3_proxy):
    test_input = '{"subarrayID":3,"dish":{"receptorIDList":["0004"]}}'
    create_centralnode_proxy.AssignResources(test_input)
    sleep(3)
    result = create_subarray3_proxy.receptorIDList
    assert result == (4,)

@pytest.mark.fast
def test_releaseresources_sub1(create_centralnode_proxy, create_subarray1_proxy):
    test_input = '{"subarrayID":1,"releaseALL":true,"receptorIDList":[]}'
    retVal = json.loads(create_centralnode_proxy.ReleaseResources(test_input))
    sleep(3)
    result = create_subarray1_proxy.receptorIDList
    assert result == None

@pytest.mark.fast
def test_releaseresources_sub2(create_centralnode_proxy, create_subarray2_proxy):
    test_input = '{"subarrayID":2,"releaseALL":true,"receptorIDList":[]}'
    retVal = create_centralnode_proxy.ReleaseResources(test_input)
    sleep(3)
    result = create_subarray2_proxy.receptorIDList
    assert result == None

@pytest.mark.fast
def test_releaseresources_sub3(create_centralnode_proxy, create_subarray3_proxy):
    test_input = '{"subarrayID":3,"releaseALL":true,"receptorIDList":[]}'
    retVal = create_centralnode_proxy.ReleaseResources(test_input)
    sleep(3)
    result = create_subarray3_proxy.receptorIDList
    assert result == None

@pytest.mark.fast
def test_standby(create_centralnode_proxy, create_subarray1_proxy):
    create_centralnode_proxy.StandByTelescope()
    sleep(3)
    result = create_subarray1_proxy.state()
    assert result == DevState.DISABLE
