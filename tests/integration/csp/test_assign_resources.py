"""Assign resources to subarray feature tests."""
import logging
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

from resources.models.mvp_model.states import ObsState

from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)


@pytest.mark.skalow
@pytest.mark.csp
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature", "Assign resources to CSP low subarray"
)
def test_assign_resources_to_csp_low_subarray():
    """Assign resources to CSP low subarray."""


@pytest.mark.skamid
@pytest.mark.csp
@pytest.mark.assign
@scenario(
    "features/csp_assign_resources.feature", "Assign resources to CSP mid subarray"
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


@given("an CSP subarray", target_fixture="composition")
def an_csp_subarray(
    set_up_subarray_log_checking_for_csp,  # pylint: disable=unused-argument
    csp_base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """an CSP subarray."""
    return csp_base_composition


# use when from ..shared_assign_resources in ..conftest.py
# @when("I assign resources to it")

# for release resources test
# use when from ..shared_assign_resources in ..conftest.py
# @when("I release all resources assigned to it")


@then("the CSP subarray must be in IDLE state")
def the_csp_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    csp_subarray = con_config.get_device_proxy(
        tel.csp.subarray(sut_settings.subarray_id)
    )
    result = csp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.IDLE)


@then("the CSP subarray must be in EMPTY state")
def the_csp_subarray_must_be_in_empty_state(sut_settings: SutTestSettings):
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    csp_subarray = con_config.get_device_proxy(
        tel.csp.subarray(sut_settings.subarray_id)
    )
    result = csp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.EMPTY)


# mock tests
# TODO
