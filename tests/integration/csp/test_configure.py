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


@pytest.mark.skip(
    reason="Disable test as it need update to support new JSON Schema"
)
@pytest.mark.skalow
@pytest.mark.csp
@pytest.mark.configure
@scenario(
    "features/csp_configure_scan.feature",
    "Configure scan on csp subarray in low",
)
def test_configure_csp_low_subarray():
    """Configure CSP low subarray."""
