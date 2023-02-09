"""Assign resources to subarray feature tests."""
import logging
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

# from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState

from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)

# log capturing
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.assign
@scenario("features/tmc_assign_resources.feature", "Assign resources to low subarray")
def test_assign_resources_to_tmc_subarray_in_low():
    """Assign resources to tmc subarray in low."""

@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@scenario(
    "features/tmc_assign_resources.feature", "Release resources from low subarray"
)
def test_release_resources_from_tmc_subarray_in_low():
    """Release resources from tmc subarrays in low."""


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.assign
@scenario("features/tmc_assign_resources.feature", "Assign resources to mid subarray")
def test_assign_resources_to_tmc_subarray_in_mid():
    """Assign resources to tmc subarray in mid."""


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@scenario(
    "features/tmc_assign_resources.feature", "Release resources from mid subarray"
)
def test_release_resources_from_tmc_subarray_in_mid():
    """Release resources from tmc subarrays in mid."""


@given("an TMC")
def a_tmc():
    """an TMC"""


@given("an telescope subarray", target_fixture="composition")
def an_telescope_subarray(
    set_up_subarray_log_checking_for_tmc, base_composition: conf_types.Composition  # type: ignore
) -> conf_types.Composition:
    """an telescope subarray."""
    return base_composition


# use when from ..shared_assign_resources
# @when("I assign resources to it")


@then("the subarray must be in IDLE state")
def the_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)


@given("a subarray in the IDLE state")
def a_subarray_in_the_idle_state():
    """a subarray in the IDLE state."""


# @when("I release all resources assigned to it")


@then("the subarray must be in EMPTY state")
def the_subarray_must_be_in_empty_state(sut_settings: SutTestSettings):
    """the subarray must be in EMPTY state."""
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.EMPTY)
