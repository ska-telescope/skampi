"""Configure subarray feature tests."""
import logging

import pytest
from pytest_bdd import scenario, when

logger = logging.getLogger(__name__)


@pytest.mark.skamid
@pytest.mark.scan
@pytest.mark.csp
@scenario("features/csp_configure_scan.feature", "Abort configuring")
def test_abort_configuring(set_up_subarray_log_checking_for_csp: None):
    """Abort scanning.
    :param: set_up_subarray_log_checking_for_csp: sets up subarray log checking for csp
    """


@pytest.mark.skip(reason="This functionality not tested at CSP/CBF, raised SKB-221")
@pytest.mark.skalow
@pytest.mark.configure
@pytest.mark.csp
@scenario("features/csp_configure_scan.feature", "Abort configuring on CSP Low")
def test_csp_abort_configuring_low(set_up_subarray_log_checking_for_csp: None):
    """Abort in configuring obstate.
    :param: set_up_subarray_log_checking_for_csp: sets up subarray log checking for csp
    """


@pytest.mark.skamid
@pytest.mark.csp
@pytest.mark.configure
@scenario("features/csp_configure_scan.feature", "Configure scan on csp subarray in mid")
def test_configure_csp_mid_subarray():
    """Configure CSP mid subarray."""


@pytest.mark.skip(reason="Disable test as it need update to support new JSON Schema")
@pytest.mark.skalow
@pytest.mark.csp
@pytest.mark.configure
@scenario(
    "features/csp_configure_scan.feature",
    "Configure scan on csp subarray in low",
)
def test_configure_csp_low_subarray():
    """Configure CSP low subarray."""

@pytest.mark.skalow
@pytest.mark.csp
@pytest.mark.configure
@scenario(
    "features/csp_configure_scan.feature",
    "Clear scan configuration on csp subarray in mid",
)
def test_clear_configure_csp_low_subarray():
    """Clear scan configuration on csp subarray in mid."""

# use from local conftest
# @given("an CSP subarray in READY state")

# use from global conftest
# @when("I command it to clear configuration (End command)")

# use from local conftest
# @then("the CSP subarray must be in IDLE/READY state")

