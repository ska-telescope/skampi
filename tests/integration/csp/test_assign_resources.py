"""Assign resources to subarray feature tests."""
import logging

import pytest
from pytest_bdd import scenario


logger = logging.getLogger(__name__)


@pytest.mark.skalow
@pytest.mark.csp
@pytest.mark.k8s
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature",
    "Assign resources to CSP low subarray",
)
def test_assign_resources_to_csp_low_subarray():
    """Assign resources to CSP low subarray."""


@pytest.mark.skamid
@pytest.mark.csp
@pytest.mark.assign
@pytest.mark.k8s
@scenario(
    "features/csp_assign_resources.feature",
    "Assign resources to CSP mid subarray",
)
def test_assign_resources_to_csp_mid_subarray():
    """Assign resources to CSP mid subarray."""


@pytest.mark.skalow
@pytest.mark.csp
@pytest.mark.assign
@pytest.mark.k8s
@scenario(
    "features/csp_assign_resources.feature",
    "Release resources assigned to an CSP low subarray",
)
def test_release_resources_to_csp_low_subarray():
    """Release resources assigned to an CSP low subarray"""


@pytest.mark.skamid
@pytest.mark.csp
@pytest.mark.assign
@pytest.mark.k8s
@scenario(
    "features/csp_assign_resources.feature",
    "Release resources assigned to an CSP mid subarray",
)
def test_release_resources_to_csp_mid_subarray():
    """Release resources assigned to an CSP mid subarray"""


# use when from ..shared_assign_resources in ..conftest.py
# @when("I assign resources to it")

# for release resources test
# use when from ..shared_assign_resources in ..conftest.py
# @when("I release all resources assigned to it")

# mock tests
# TODO
