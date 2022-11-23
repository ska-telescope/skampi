"""Assign resources to subarray feature tests."""
import logging

import pytest
from pytest_bdd import given, scenario, then
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

logger = logging.getLogger(__name__)


@pytest.mark.skalow
@pytest.mark.csp
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
@scenario(
    "features/csp_assign_resources.feature",
    "Assign resources to CSP mid subarray",
)
def test_assign_resources_to_csp_mid_subarray():
    """Assign resources to CSP mid subarray."""


@pytest.mark.skalow
@pytest.mark.csp
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature",
    "Release resources assigned to an CSP low subarray",
)
def test_release_resources_to_csp_low_subarray():
    """Release resources assigned to an CSP low subarray"""


@pytest.mark.skamid
@pytest.mark.csp
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature",
    "Release resources assigned to an CSP mid subarray",
)
def test_release_resources_to_csp_mid_subarray():
    """Release resources assigned to an CSP mid subarray"""


@pytest.mark.skamid
@pytest.mark.assign
@pytest.mark.sdp
@scenario("features/sdp_assign_resources.feature", "Assign resources with duplicate id")
def test_assign_resources_with_duplicate_id(assign_resources_test_exec_settings):  # type: ignore
    """Assign resources with duplicate id."""


# use given from local .conftest
# @given("an CSP subarray", target_fixture="composition")

# use when from ..conftest
# @when("I assign resources with a duplicate sb id"


# use when from ..shared_assign_resources in ..conftest.py
# @when("I assign resources to it")

# for release resources test
# use when from ..shared_assign_resources in ..conftest.py
# @when("I release all resources assigned to it")

# mock tests
# TODO
