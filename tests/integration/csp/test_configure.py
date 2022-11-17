"""Configure subarray feature tests."""
import logging

import pytest
from pytest_bdd import scenario


logger = logging.getLogger(__name__)

@pytest.mark.skamid
@pytest.mark.csp
@pytest.mark.configure
@scenario(
    "features/csp_configure_scan.feature",
    "Configure scan on csp subarray in mid",
)
def test_configure_csp_mid_subarray():
    """Configure CSP low subarray."""

@pytest.mark.skalow
@pytest.mark.csp
@pytest.mark.configure
@scenario(
    "features/csp_configure_scan.feature",
    "Configure scan on csp subarray in low",
)
def test_configure_csp_low_subarray():
    """Configure CSP low subarray."""
