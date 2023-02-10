import pytest
from pytest_bdd import scenario, given, when, then

from tests.integration.cbf.test_assign_resources import an_cbf_subarray
from tests.integration.conftest import i_assign_resources_to_it
from tests.integration.sdp.test_assign_resources import an_sdp_subarray
from tests.integration.csp.conftest import an_csp_subarray

# DO NOT DELETE: needed for given steps to work
# from tests.integration.csp.conftest import fxt_set_up_log_checking_for_csp, fxt_csp_base_composition
# from tests.integration.cbf.conftest import fxt_set_up_log_checking_for_cbf, fxt_cbf_base_composition
# from tests.integration.sdp.conftest import fxt_set_up_log_capturing_for_sdp, fxt_sdp_base_composition

pytest_plugins = [
    "tests.integration.csp.conftest",
    "tests.integration.cbf.conftest",
    "tests.integration.sdp.conftest"
]


@pytest.mark.skamid
@pytest.mark.cbf
@pytest.mark.csp
@pytest.mark.sdp
@scenario(
    "features/csp_sdp_repeat_scan.feature", "SUT1 runs a single scan successfully"
)
def test_mid_sut1_repeats_commands_successfully():
    """MID SUT1 repeats commands successfully."""


given("the CSP LMC Subarray is On and its obsState is Empty", target_fixture="composition")(an_csp_subarray)
# TODO: is this indeed the mid CBF?
given("the Mid CBF Subarray is On and its obsState is Empty", target_fixture="composition")(an_cbf_subarray)
given("the SDP Subarray is On and its obsState is Empty", target_fixture="composition")(an_sdp_subarray)

when("I run AssignResources on the CSP LMC and the SDP")(i_assign_resources_to_it)
# when("I run Configure on the CSP LMC and the SDP")()
# when("I run Scan and after 10 seconds run EndScan on the CSP LMC and the SDP")()
# when("I run End and then ReleaseAllResources on the CSP LMC and the SDP")()
