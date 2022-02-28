# import logging
# import time

# import pytest
# from tango import DeviceProxy, DevState

# LOGGER = logging.getLogger(__name__)


# @pytest.mark.skamid
# def test_telescopestandby():
#     try:
#         fixture = {}
#         fixture["state"] = "Unknown"

#         # given a started up telescope
#         LOGGER.info("Staring up the Telescope")

#         TMCCentralNode = DeviceProxy("ska_mid/tm_central/central_node")
#         SdpMasterLeafNode = DeviceProxy("ska_mid/tm_leaf_node/sdp_master")
#         SdpMaster = DeviceProxy("mid_sdp/elt/master")
#         SdpSubarray = DeviceProxy("mid_sdp/elt/subarray_1")


#         LOGGER.info(
#         "Before Sending TelescopeOn command on CentralNode state :"
#         + str(TMCCentralNode.State())
#         )
#         LOGGER.info(
#         "Before Sending TelescopeOn command on CentralNode telescopeState :"
#         + str(TMCCentralNode.telescopeState)
#         )
#         LOGGER.info(
#         "Before Sending TelescopeOn command on sdp master leaf node state :"
#         + str(SdpMasterLeafNode.State())
#         )
#         LOGGER.info(
#         "Before Sending TelescopeOn command on sdp master state :"
#         + str(SdpMaster.State())
#         )
#         LOGGER.info(
#         "Before Sending TelescopeOn command on sdp subarray state :"
#         + str(SdpSubarray.State())
#         )

#         # command invokation
#         TMCCentralNode.TelescopeOn()
#         time.sleep(0.5)
#         fixture["state"] = "Telescope On"
#         LOGGER.info("Invoked TelescopeOn on CentralNode")

#         assert TMCCentralNode.State() == DevState.ON
#         assert SdpMasterLeafNode.State() == DevState.ON
#         assert SdpMaster.State() == DevState.ON

#         LOGGER.info(
#         "After Sending TelescopeOn command on CentralNode state :"
#         + str(TMCCentralNode.State())
#         )
#         LOGGER.info(
#         "After Sending TelescopeOn command on CentralNode telescopeState :"
#         + str(TMCCentralNode.telescopeState)
#         )
#         LOGGER.info(
#         "After Sending TelescopeOn command on sdp master leaf node state :"
#         + str(SdpMasterLeafNode.State())
#         )
#         LOGGER.info(
#         "After Sending TelescopeOn command on sdp master state :"
#         + str(SdpMaster.State())
#         )
#         LOGGER.info(
#         "After Sending TelescopeOn command on sdp subarray state :"
#         + str(SdpSubarray.State())
#         )
#         # command invokation
#         TMCCentralNode.TelescopeStandby()
#         time.sleep(0.5)

#         fixture["state"] = "Telescope standby"

#         assert TMCCentralNode.State() == DevState.ON
#         assert TMCCentralNode.telescopeState == DevState.STANDBY
#         assert SdpMasterLeafNode.State() == DevState.ON
#         assert SdpMaster.State() == DevState.STANDBY
#         LOGGER.info(
#         "After Sending TelescopeStandby command on CentralNode state :"
#         + str(TMCCentralNode.State())
#         )
#         LOGGER.info(
#         "After Sending TelescopeStandby command on CentralNode telescopeState :"
#         + str(TMCCentralNode.telescopeState)
#         )
#         LOGGER.info(
#         "After Sending TelescopeStandby command on sdp master leaf node state :"
#         + str(SdpMasterLeafNode.State())
#         )
#         LOGGER.info(
#         "After Sending TelescopeStandby command on sdp master state :"
#         + str(SdpMaster.State())
#         )
#         LOGGER.info(
#         "After Sending TelescopeOff command on sdp subarray state :"
#         + str(SdpSubarray.State())
#         )

#         LOGGER.info("Tests complete: tearing down...")
#     except Exception:
#         LOGGER.info(
#             "Tearing down failed test, state = {}".format(fixture["state"])
#         )
#         if fixture["state"] == "Telescope On":
#             TMCCentralNode.TelescopeOff()
#         pytest.fail("unable to complete test without exceptions")
