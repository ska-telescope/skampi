"""Assign resources to subarray feature tests."""
import logging
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

from resources.models.mvp_model.states import ObsState

from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)

# log capturing


@pytest.mark.skalow
@pytest.mark.assign
@pytest.mark.sdp
@scenario(
    "features/sdp_assign_resources.feature", "Assign resources to sdp subarray in low"
)
def test_assign_resources_to_sdp_subarray_in_low(assign_resources_test_exec_settings):
    """Assign resources to sdp subarray in low."""


@pytest.mark.skamid
@pytest.mark.assign
@pytest.mark.sdp
@scenario(
    "features/sdp_assign_resources.feature", "Assign resources to sdp subarray in mid"
)
def test_assign_resources_to_sdp_subarray_in_mid(assign_resources_test_exec_settings):
    """Assign resources to sdp subarray in mid."""


@pytest.mark.skamid
@pytest.mark.assign
@pytest.mark.sdp
@scenario(
    "features/sdp_assign_resources.feature", "Assign resources with duplicate id to SDP"
)
def test_assign_resources_with_duplicate_id(assign_resources_test_exec_settings):  # type: ignore
    """Assign resources with duplicate id."""


@pytest.mark.skamid
@pytest.mark.assign
@pytest.mark.sdp
@scenario(
    "features/sdp_assign_resources.feature", "Command assign resources twice in order"
)
def test_assign_resources_duplicate_commands(assign_resources_test_exec_settings):  # type: ignore
    """Command assign resources twice in order."""


@given("an SDP subarray", target_fixture="composition")
def an_sdp_subarray(
    set_up_subarray_log_checking_for_sdp,  # type: ignore
    sdp_base_composition: conf_types.Composition,
    sut_settings: SutTestSettings,
) -> conf_types.Composition:
    """an SDP subarray."""
    sut_settings.default_subarray_name = sut_settings.tel.sdp.subarray(
        sut_settings.subarray_id
    )
    return sdp_base_composition


# use when from ..shared_assign_resources
# @when("I assign resources to it")

# use when from ..conftest
# @when("I assign resources with a duplicate sb id"

# use when from ..conftest
# @when("I command the assign resources twice in consecutive fashion"


# use then from ..conftest
# @then("the subarray should throw an exception and remain in the previous state")


@then("the subarray must be in IDLE state")
def the_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
    """the subarray must be in IDLE state."""
    sdp_subarray = con_config.get_device_proxy(sut_settings.default_subarray_name)
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.IDLE)


# mock tests
