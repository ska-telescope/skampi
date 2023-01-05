"""Run scan on subarray feature tests."""
import pytest
from pytest_bdd import scenario

from ... import conftest


#@pytest.mark.skamid
@pytest.mark.configure
@scenario(
    "features/sdpln_run_scan.feature",
    "Run scan on sdp subarray in mid using the leaf node",
)
def test_run_scan_on_sdp_subarray_in_mid():
    """Run scan on sdp subarray in mid using the leaf node."""


# @given("an SDP subarray in READY state")

# @given("a TMC SDP subarray Leaf Node")

# @when("I command it to scan for a given period") from ...conftest

# @then("the SDP subarray shall go from READY to SCANNING") 

# @then("the SDP shall go back to READY when finished")




@pytest.mark.skalow
@pytest.mark.configure
@scenario(
    "features/tmc_sdpln_scan.feature",
    "Scan the sdp low using csp leaf node",
)
def test_run_scan_on_sdp_subarray_in_low():
    """Run scan on sdp subarray in low using the leaf node."""


# @given("an SDP subarray in READY state")

# @given("a TMC SDP subarray Leaf Node")

# @when("I command it to scan for a given period") from ...conftest

# @then("the SDP subarray shall go from READY to SCANNING") 

# @then("the SDP shall go back to READY when finished")
