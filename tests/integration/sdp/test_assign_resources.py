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

@pytest.mark.skip(reason="testing")
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


@given("an SDP subarray", target_fixture="composition")
def an_sdp_subarray(
    set_up_subarray_log_checking_for_sdp, sdp_base_composition: conf_types.Composition
) -> conf_types.Composition:
    """an SDP subarray."""
    return sdp_base_composition


# use when from ..shared_assign_resources
# @when("I assign resources to it")


@then("the subarray must be in IDLE state")
def the_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(
        tel.sdp.subarray(sut_settings.subarray_id)
    )
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.IDLE)


# mock tests


@pytest.mark.test_tests
@pytest.mark.usefixtures("setup_sdp_mock")
def test_test_sdp_assign_resources(
    run_mock, mock_entry_point: fxt_types.mock_entry_point
):
    """Test the test using a mock SUT"""
    run_mock(test_assign_resources_to_sdp_subarray_in_mid)
    mock_entry_point.spy.set_telescope_to_running.assert_called()
    mock_entry_point.spy.compose_subarray.assert_called()
    mock_entry_point.model.sdp.master.spy.command_inout.assert_called()
    mock_entry_point.model.sdp.subarray1.spy.command_inout.assert_called()
