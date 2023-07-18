"""Assign resources to subarray feature tests."""
import logging

import pytest
from assertpy import assert_that
from pytest_bdd import scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names

from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)

# log capturing


@pytest.mark.sdp
@pytest.mark.skamid
@pytest.mark.assign
@pytest.mark.xfail(reason="Temp failure in pipeline")
@scenario(
    "features/sdp_assign_resources.feature",
    "Releasing all resources from sdp sub-array in mid",
)
def test_release_all_resources_from_sdp_subarray_in_mid():
    """Releasing all resources from sdp sub-array in mid."""


# use from local conftest
# @given("an SDP subarray in IDLE state", target_fixture="configuration")

# use when from ..shared_assign_resources
# @when("I release all resources assigned to it")


@then("the subarray must be in EMPTY state")
def the_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
    """
    the subarray must be in EMPTY state.

    :param sut_settings: the SUT test settings.
    """
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(sut_settings.subarray_id))
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.EMPTY)
