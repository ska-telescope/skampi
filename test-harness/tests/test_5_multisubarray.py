from time import sleep
import pytest
import tango
import json

def test_init():
  print("Init test multisubarray")


def test_assignresources_sub1(create_centralnode_proxy, create_subarray1_proxy):
    test_input = '{"subarrayID":1,"dish":{"receptorIDList":["0001"]}}'
    create_centralnode_proxy.AssignResources(test_input)
    sleep(3)
    result = create_subarray1_proxy.receptorIDList
    assert result == (1,)

# def test_assignresouce_sub2(create_centralnode_proxy, create_subarray2_proxy):
#     test_input = '{"subarrayID":2,"dish":{"receptorIDList":["0003"]}}'
#     create_centralnode_proxy.AssignResources(test_input)
#     sleep(3)
#     result = create_subarray2_proxy.receptorIDList
#     assert result == (3,)

def test_configure_sub1(create_subarray1_proxy):
    test_input = '{"scanID":12345,"pointing":{"target":{"system":"ICRS","name":'\
                   '"Polaris","RA":"02:31:49.0946","dec":"+89:15:50.7923"}},"dish":'\
                   '{"receiverBand":"1"},"csp":{"frequencyBand":"1","fsp":[{"fspID":1,'\
                   '"functionMode":"CORR","frequencySliceID":1,"integrationTime":1400,'\
                   '"corrBandwidth":0}]},"sdp":{"configure":'\
                   '[{"id":"realtime-20190627-0001","sbiId":"20190627-0001","workflow":'\
                   '{"id":"vis_ingest","type":"realtime","version":"0.1.0"},"parameters":'\
                   '{"numStations":4,"numChannels":372,"numPolarisations":4,'\
                   '"freqStartHz":0.35e9,"freqEndHz":1.05e9,"fields":{"0":'\
                   '{"system":"ICRS","name":"Polaris","ra":0.662432049839445,'\
                   '"dec":1.5579526053855042}}},"scanParameters":{"12345":'\
                   '{"fieldId":0,"intervalMs":1400}}}]}}'
    create_subarray1_proxy.configure(test_input)
    print ("create_subarray1_proxy.obsState: ", create_subarray1_proxy.obsState.value)
    sleep(70)
    assert create_subarray1_proxy.obsState == 2

# def test_configure_sub2(create_subarray2_proxy):
#     test_input = '{"scanID":12345,"pointing":{"target":{"system":"ICRS","name":'\
#                    '"Polaris","RA":"02:31:49.0946","dec":"+89:15:50.7923"}},"dish":'\
#                    '{"receiverBand":"1"},"csp":{"frequencyBand":"1","fsp":[{"fspID":1,'\
#                    '"functionMode":"CORR","frequencySliceID":1,"integrationTime":1400,'\
#                    '"corrBandwidth":0}]},"sdp":{"configure":'\
#                    '[{"id":"realtime-20190627-0001","sbiId":"20190627-0001","workflow":'\
#                    '{"id":"vis_ingest","type":"realtime","version":"0.1.0"},"parameters":'\
#                    '{"numStations":4,"numChannels":372,"numPolarisations":4,'\
#                    '"freqStartHz":0.35e9,"freqEndHz":1.05e9,"fields":{"0":'\
#                    '{"system":"ICRS","name":"Polaris","ra":0.662432049839445,'\
#                    '"dec":1.5579526053855042}}},"scanParameters":{"12345":'\
#                    '{"fieldId":0,"intervalMs":1400}}}]}}'
#     create_subarray2_proxy.configure(test_input)
#     print ("create_subarray2_proxy.obsState: ", create_subarray2_proxy.obsState.value)
#     sleep(70)
#     assert create_subarray2_proxy.obsState == 2

def test_scan_sub1(create_subarray1_proxy):
    create_subarray1_proxy.Scan('{"scanDuration": 5.0}')
    sleep(2)
    assert create_subarray1_proxy.obsState == 3

# def test_scan_sub2(create_subarray2_proxy):
#     create_subarray2_proxy.Scan('{"scanDuration": 5.0}')
#     sleep(2)
#     assert create_subarray2_proxy.obsState == 3

def test_endsb_sub1(create_subarray1_proxy):
    sleep(10)
    create_subarray1_proxy.EndSB()
    sleep(10)
    assert create_subarray1_proxy.obsState == 0

# def test_endsb_sub2(create_subarray2_proxy):
#     create_subarray2_proxy.EndSB()
#     sleep(15)
#     assert create_subarray2_proxy.obsState == 0

def test_releaseresources_sub1(create_centralnode_proxy, create_subarray1_proxy):
    test_input = '{"subarrayID":1,"releaseALL":true,"receptorIDList":[]}'
    retVal = json.loads(create_centralnode_proxy.ReleaseResources(test_input))
    assert retVal["receptorIDList"] == []
    sleep(3)
    result = create_subarray1_proxy.receptorIDList
    assert result == None

# def test_releaseResources_sub2(create_centralnode_proxy, create_subarray2_proxy):
#     test_input = '{"subarrayID":2,"releaseALL":true,"receptorIDList":[]}'
#     with pytest.raises(tango.DevFailed):
#         retVal = create_centralnode_proxy.ReleaseResources(test_input)
#         assert retVal["receptorIDList"] == []
#     sleep(3)
#     result = create_subarray2_proxy.receptorIDList
#     assert result == None
