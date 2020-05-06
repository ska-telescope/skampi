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
    test_input = '{"subarrayID":1,"dish":{"receptorIDList":["0004"]},"sdp":{"id":"sbi-mvp01-20200325-00001","max_length":100.0,"scan_types":[{"id":"science_A","coordinate_system":"ICRS","ra":"02:42:40.771","dec":"-00:00:47.84","subbands":[{"freq_min":0.35e9,"freq_max":1.05e9,"nchan":372,"input_link_map":[[1,0],[101,1]]}]},{"id":"calibration_B","coordinate_system":"ICRS","ra":"12:29:06.699","dec":"02:03:08.598","subbands":[{"freq_min":0.35e9,"freq_max":1.05e9,"nchan":372,"input_link_map":[[1,0],[101,1]]}]}],"processing_blocks":[{"id":"pb-mvp01-20200325-00001","workflow":{"type":"realtime","id":"vis_receive","version":"0.1.0"},"parameters":{}},{"id":"pb-mvp01-20200325-00002","workflow":{"type":"realtime","id":"test_realtime","version":"0.1.0"},"parameters":{}},{"id":"pb-mvp01-20200325-00003","workflow":{"type":"batch","id":"ical","version":"0.1.0"},"parameters":{},"dependencies":[{"pb_id":"pb-mvp01-20200325-00001","type":["visibilities"]}]},{"id":"pb-mvp01-20200325-00004","workflow":{"type":"batch","id":"dpreb","version":"0.1.0"},"parameters":{},"dependencies":[{"pb_id":"pb-mvp01-20200325-00003","type":["calibration"]}]}]}}'
    create_centralnode_proxy.AssignResources(test_input)
    sleep(3)
    result = create_subarray1_proxy.receptorIDList
    assert result == (4,)

@pytest.mark.fast
def test_assignresouce_sub2(create_centralnode_proxy, create_subarray2_proxy):
    test_input = '{"subarrayID":2,"dish":{"receptorIDList":["0002"]},"sdp":{"id":"sbi-mvp01-20200325-00001","max_length":100.0,"scan_types":[{"id":"science_A","coordinate_system":"ICRS","ra":"02:42:40.771","dec":"-00:00:47.84","subbands":[{"freq_min":0.35e9,"freq_max":1.05e9,"nchan":372,"input_link_map":[[1,0],[101,1]]}]},{"id":"calibration_B","coordinate_system":"ICRS","ra":"12:29:06.699","dec":"02:03:08.598","subbands":[{"freq_min":0.35e9,"freq_max":1.05e9,"nchan":372,"input_link_map":[[1,0],[101,1]]}]}],"processing_blocks":[{"id":"pb-mvp01-20200325-00001","workflow":{"type":"realtime","id":"vis_receive","version":"0.1.0"},"parameters":{}},{"id":"pb-mvp01-20200325-00002","workflow":{"type":"realtime","id":"test_realtime","version":"0.1.0"},"parameters":{}},{"id":"pb-mvp01-20200325-00003","workflow":{"type":"batch","id":"ical","version":"0.1.0"},"parameters":{},"dependencies":[{"pb_id":"pb-mvp01-20200325-00001","type":["visibilities"]}]},{"id":"pb-mvp01-20200325-00004","workflow":{"type":"batch","id":"dpreb","version":"0.1.0"},"parameters":{},"dependencies":[{"pb_id":"pb-mvp01-20200325-00003","type":["calibration"]}]}]}}'
    create_centralnode_proxy.AssignResources(test_input)
    sleep(3)
    result = create_subarray2_proxy.receptorIDList
    assert result == (2,)

@pytest.mark.fast
def test_assignresouce_sub3(create_centralnode_proxy, create_subarray3_proxy):
    test_input = '{"subarrayID":3,"dish":{"receptorIDList":["0003"]},"sdp":{"id":"sbi-mvp01-20200325-00001","max_length":100.0,"scan_types":[{"id":"science_A","coordinate_system":"ICRS","ra":"02:42:40.771","dec":"-00:00:47.84","subbands":[{"freq_min":0.35e9,"freq_max":1.05e9,"nchan":372,"input_link_map":[[1,0],[101,1]]}]},{"id":"calibration_B","coordinate_system":"ICRS","ra":"12:29:06.699","dec":"02:03:08.598","subbands":[{"freq_min":0.35e9,"freq_max":1.05e9,"nchan":372,"input_link_map":[[1,0],[101,1]]}]}],"processing_blocks":[{"id":"pb-mvp01-20200325-00001","workflow":{"type":"realtime","id":"vis_receive","version":"0.1.0"},"parameters":{}},{"id":"pb-mvp01-20200325-00002","workflow":{"type":"realtime","id":"test_realtime","version":"0.1.0"},"parameters":{}},{"id":"pb-mvp01-20200325-00003","workflow":{"type":"batch","id":"ical","version":"0.1.0"},"parameters":{},"dependencies":[{"pb_id":"pb-mvp01-20200325-00001","type":["visibilities"]}]},{"id":"pb-mvp01-20200325-00004","workflow":{"type":"batch","id":"dpreb","version":"0.1.0"},"parameters":{},"dependencies":[{"pb_id":"pb-mvp01-20200325-00003","type":["calibration"]}]}]}}'
    create_centralnode_proxy.AssignResources(test_input)
    sleep(3)
    result = create_subarray3_proxy.receptorIDList
    assert result == (3,)

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
