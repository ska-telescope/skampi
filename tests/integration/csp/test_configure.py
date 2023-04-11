"""Configure subarray feature tests."""
import logging

import pytest
from pytest_bdd import scenario


logger = logging.getLogger(__name__)


@pytest.mark.skamid
@pytest.mark.scan
@pytest.mark.csp
@scenario("features/csp_configure_scan.feature", "Abort configuring")
def test_abort_configuring(set_up_subarray_log_checking_for_csp: None):
    """Abort scanning."""


@pytest.mark.skamid
@pytest.mark.csp
@pytest.mark.configure
@scenario(
    "features/csp_configure_scan.feature",
    "Configure scan on csp subarray in mid",
)
def test_configure_csp_mid_subarray():
    """Configure CSP low subarray."""


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


@pytest.mark.xfail
@pytest.mark.skamid
@pytest.mark.configure
@pytest.mark.csp
@scenario(
    "features/csp_configure_scan.feature",
    "Configure invalid scan on csp subarray in mid",
)
def test_configure_invalid_scan_on_csp_subarray_in_mid():
    """Configure invalid scan on csp subarray in mid."""


@pytest.mark.skamid
@pytest.mark.configure
@pytest.mark.csp
@scenario("features/csp_configure_scan.feature", "Abort configuring")
def test_abort_configure_scan_on_csp_subarray_in_mid():
    """Abort configuring."""


# use from local conftest
# @given("an SDP subarray in IDLE state", target_fixture="configuration")

# use when from global conftest
# @when("I configure it for a scan with an invalid configuration")

# use then from global conftest
# @then("the subarray should throw an exception and remain in the previous state")
