"""Default feature tests."""
import pytest
import time
from pytest_bdd import given, scenario, then, when

import logging
import pytest
from tango import DeviceProxy, DevState

LOGGER = logging.getLogger(__name__)

TMCCentralNode = DeviceProxy("ska_mid/tm_central/central_node")
SdpMasterLeafNode = DeviceProxy("ska_mid/tm_leaf_node/sdp_master")
SdpMaster = DeviceProxy("mid_sdp/elt/master")
SdpSubarray = DeviceProxy("mid_sdp/elt/subarray_1")
TMCSubarrayNode = DeviceProxy("ska_mid/tm_subarray_node/1")

@pytest.fixture
def fixture():
    return {}

@pytest.mark.shraddha
@scenario("features/telescopeOn.feature", "Test TelescopeOn command")
def test_telescope_on():
    """TelescopeOn() is executed."""


@given("TMC and SDP devices are deployed")
def device_list():
    try:
        TMCCentralNode.ping()
        LOGGER.info("TMC CentralNode is up")
        SdpMasterLeafNode.ping()
        LOGGER.info("TMC SdpMasterLeafNode is up")
        SdpMaster.ping()
        LOGGER.info("Sdp Master is up")
        SdpSubarray.ping()
        LOGGER.info("Sdp Subarray is up")
        TMCSubarrayNode.ping()
        LOGGER.info("TMC Subarray is up")

    except Exception as e:
        LOGGER.info(f"Exception occured while checking the device {e}")


@given("Telescope is in OFF state")
def check_telescope_off():
    """Verify Telescope is Off"""
    assert SdpMaster.State() in [DevState.STANDBY, DevState.OFF]
    assert SdpSubarray.State() == DevState.OFF


@when("the operator invokes TelescopeOn command on TMC")
def invoke_telescope_on_command(fixture):
    """I invoke TelescopeOn() command on TMC"""

    fixture["state"] = "Unknown"

    LOGGER.info("Invoking TelescopeOn command on TMC CentralNode")
    TMCCentralNode.TelescopeOn()
    time.sleep(0.5)
    LOGGER.info("TelescopeOn command is invoked successfully")


@then("the SDP Master turns on and changes its state to ON")
def check_device_state(fixture):
    """Verify Sdp Master and Sdp Subarray State"""

    assert SdpMaster.State() == DevState.ON
    assert SdpSubarray.State() == DevState.ON

    fixture["state"] = "TelescopeOn"

    LOGGER.info("Tests complete: tearing down...")
    tear_down(fixture)


def tear_down(fixture):
    LOGGER.info(
            "Tearing down failed test, state = {}".format(fixture["state"])
    )
    if fixture["state"] == "TelescopeOn":
        TMCCentralNode.TelescopeOff()
    else:
        pytest.fail("unable to complete test without exceptions")

