import logging
import pytest
from tango import DeviceProxy, DevState

LOGGER = logging.getLogger(__name__)


@pytest.mark.xfail
def test_telescopeon():
    try:
        fixture = {}
        fixture["state"] = "Unknown"

        # given a started up telescope
        LOGGER.info("Staring up the Telescope")

        CentralNode = DeviceProxy("ska_mid/tm_central/central_node")
        sdp_mln = DeviceProxy("ska_mid/tm_leaf_node/sdp_master")
        sdp_master = DeviceProxy("mid_sdp/elt/master")
        sdp_sa = DeviceProxy("mid_sdp/elt/subarray_1")

        LOGGER.info(
        "Before Sending TelescopeOn command on CentralNode state :"
        + str(CentralNode.State())
        )
        LOGGER.info(
        "Before Sending TelescopeOn command on CentralNode telescopeState :"
        + str(CentralNode.telescopeState)
        )
        LOGGER.info(
        "Before Sending TelescopeOn command on sdp master leaf node state :"
        + str(sdp_mln.State())
        )
        LOGGER.info(
        "Before Sending TelescopeOn command on sdp master state :"
        + str(sdp_master.State())
        )
        LOGGER.info(
        "Before Sending TelescopeOn command on sdp subarray state :"
        + str(sdp_sa.State())
        )

        # command invokation
        CentralNode.TelescopeOn()

        fixture["state"] = "Telescope On"
        LOGGER.info("Invoked TelescopeOn on CentralNode")

        assert CentralNode.State() == DevState.ON
        # assert CentralNode.telescopeState == DevState.UNKNOWN
        assert sdp_mln.State() == DevState.ON
        assert sdp_master.State() == DevState.ON

        LOGGER.info(
        "After Sending TelescopeOn command on CentralNode state :"
        + str(CentralNode.State())
        )
        LOGGER.info(
        "After Sending TelescopeOn command on CentralNode telescopeState :"
        + str(CentralNode.telescopeState)
        )
        LOGGER.info(
        "After Sending TelescopeOn command on sdp master leaf node state :"
        + str(sdp_mln.State())
        )
        LOGGER.info(
        "After Sending TelescopeOn command on sdp master state :"
        + str(sdp_master.State())
        )
        LOGGER.info(
        "After Sending TelescopeOn command on sdp subarray state :"
        + str(sdp_sa.State())
        )
        # command invokation
        CentralNode.TelescopeOff()
        fixture["state"] = "Telescope Off"

        LOGGER.info(
        "After Sending TelescopeOff command on CentralNode state :"
        + str(CentralNode.State())
        )
        LOGGER.info(
        "After Sending TelescopeOff command on CentralNode telescopeState :"
        + str(CentralNode.telescopeState)
        )
        LOGGER.info(
        "After Sending TelescopeOff command on sdp master leaf node state :"
        + str(sdp_mln.State())
        )
        LOGGER.info(
        "After Sending TelescopeOff command on sdp master state :"
        + str(sdp_master.State())
        )
        LOGGER.info(
        "After Sending TelescopeOff command on sdp subarray state :"
        + str(sdp_sa.State())
        )
        assert CentralNode.State() == DevState.ON
        assert CentralNode.telescopeState == DevState.UNKNOWN
        assert sdp_mln.State() == DevState.ON
        assert sdp_master.State() == DevState.OFF

        LOGGER.info("Tests complete: tearing down...")
    except Exception:
        LOGGER.info(
            "Tearing down failed test, state = {}".format(fixture["state"])
        )
        if fixture["state"] == "Telescope On":
            CentralNode.TelescopeOff()
        pytest.fail("unable to complete test without exceptions")
