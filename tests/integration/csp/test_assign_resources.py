"""Assign resources to subarray feature tests."""
import logging

import pytest
from pytest_bdd import scenario
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)


@pytest.fixture(name="composition")
def fxt_default_composition(csp_base_composition: conf_types.Composition):
    """
    A fixture for default composition
    :param csp_base_composition: A csp base composition object
    :type csp_base_composition: conf_types.Composition
    :return: A class representing the csp base configuration for the system under test.
    """
    return csp_base_composition


@pytest.mark.csprelated
@pytest.mark.skalow
@pytest.mark.csplmc
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature",
    "Assign resources to CSP low subarray",
)
def test_assign_resources_to_csp_low_subarray():
    """Assign resources to CSP low subarray."""


@pytest.mark.csp_related
@pytest.mark.skamid
@pytest.mark.csplmc
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature",
    "Assign resources to CSP mid subarray",
)
def test_assign_resources_to_csp_mid_subarray():
    """Assign resources to CSP mid subarray."""


@pytest.mark.csp_related
@pytest.mark.skalow
@pytest.mark.csplmc
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature",
    "Release resources assigned to an CSP low subarray",
)
def test_release_resources_to_csp_low_subarray():
    """Release resources assigned to an CSP low subarray"""


@pytest.mark.csp_related
@pytest.mark.skamid
@pytest.mark.csplmc
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature",
    "Release resources assigned to an CSP mid subarray",
)
def test_release_resources_to_csp_mid_subarray():
    """Release resources assigned to an CSP mid subarray"""


@pytest.fixture(name="set_restart_after_abort")
def fxt_set_restart_after_abort(sut_settings: SutTestSettings):
    """
    A fixture to set restart after abort
    :param sut_settings: An instance of SutTestSettings class
        containing test settings for the SUT.
    """
    sut_settings.restart_after_abort = True


@pytest.mark.skip(reason="abort in resourcing not implemented yet for CSP")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.assign
@scenario("features/csp_assign_resources.feature", "Abort assigning CSP")
def test_abort_in_resourcing_mid(
    set_restart_after_abort: None, composition: conf_types.Composition
):
    """Assign resources to csp subarray in mid.
    :param set_restart_after_abort: A fixture to set restart after abort which is set as none
    :param composition: The assign resources configuration paramaters
    """


@pytest.mark.skip(reason="abort in resourcing not implemented yet for CSP")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.assign
@scenario("features/csp_assign_resources.feature", "Abort assigning CSP Low")
def test_abort_in_resourcing_low(
    set_restart_after_abort: None, composition: conf_types.Composition
):
    """Assign resources to csp subarray in low.
    :param set_restart_after_abort: A fixture to set restart after abort which is set as none
    :param composition: The assign resources configuration paramaters
    """


# use when from ..shared_assign_resources in ..conftest.py
# @when("I assign resources to it")

# for release resources test
# use when from ..shared_assign_resources in ..conftest.py
# @when("I release all resources assigned to it")

# mock tests
# TODO
