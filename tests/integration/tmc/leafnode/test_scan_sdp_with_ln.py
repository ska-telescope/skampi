"""Run scan on subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState

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

@given("a TMC SDP subarray Leaf Node")
def a_sdp_sln(set_sdp_ln_entry_point):
    """a TMC SDP subarray Leaf Node."""


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

@given("a TMC SDP subarray Leaf Node")
def a_sdp_sln(set_sdp_ln_entry_point):
    """a TMC SDP subarray Leaf Node."""


# @when("I command it to scan for a given period") from ...conftest

# @then("the SDP subarray shall go from READY to SCANNING") 

# @then("the SDP shall go back to READY when finished")
