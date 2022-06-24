"""Configure subarray feature tests."""
import logging

import pytest
from pytest_bdd import given, scenario, then
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

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
