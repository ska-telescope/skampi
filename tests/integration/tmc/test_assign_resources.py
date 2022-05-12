"""Assign resources to subarray feature tests."""
import logging
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState

from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)

# log capturing


@pytest.mark.skip(reason="test under development")
@pytest.mark.skamid
@pytest.mark.assign
@scenario("features/tmc_assign_resources.feature", "Assign resources to mid subarray")
def test_assign_resources_to_tmc_subarray_in_mid():
    """Assign resources to sdp subarray in mid."""


@given("an TMC")
def a_tmc():
    """an TMC"""


@given("an telescope subarray", target_fixture="composition")
def an_sdp_subarray(
    set_up_subarray_log_checking_for_tmc, base_composition: conf_types.Composition
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
    result = subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.IDLE)