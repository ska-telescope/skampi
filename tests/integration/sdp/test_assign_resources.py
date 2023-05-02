"""Assign resources to subarray feature tests."""
import logging

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)

# log capturing


@pytest.fixture(name="composition")
def fxt_default_composition(sdp_base_configuration: conf_types.Composition):
    """
    A default composition fixture
    :param sdp_base_configuration: A sdp base configuration object
    :return: A class representing the sdp base configuration for the system under test.
    """
    return sdp_base_configuration


@pytest.fixture(name="set_restart_after_abort")
def fxt_set_restart_after_abort(sut_settings: SutTestSettings):
    """
    A set restart after abort fixture

    :param sut_settings: Object for system under tests setting
    """
    sut_settings.restart_after_abort = True


@pytest.mark.skalow
@pytest.mark.assign
@pytest.mark.sdp
@scenario(
    "features/sdp_assign_resources.feature",
    "Assign resources to sdp subarray in low",
)
def test_assign_resources_to_sdp_subarray_in_low(
    assign_resources_test_exec_settings: None,
):
    """
    Assign resources to sdp subarray in low.
    :param assign_resources_test_exec_settings: Object for assign_resources_test_exec_settings
    """


@pytest.mark.skamid
@pytest.mark.assign
@pytest.mark.sdp
@scenario(
    "features/sdp_assign_resources.feature",
    "Assign resources to sdp subarray in mid",
)
def test_assign_resources_to_sdp_subarray_in_mid(
    assign_resources_test_exec_settings: None,
):
    """
    Assign resources to sdp subarray in mid.

    :param assign_resources_test_exec_settings: Object for assign_resources_test_exec_settings
    """


@pytest.mark.skamid
@pytest.mark.assign
@pytest.mark.sdp
@scenario("features/sdp_assign_resources.feature", "Assign resources with duplicate id to SDP")
def test_assign_resources_with_duplicate_id(assign_resources_test_exec_settings):  # type: ignore
    """Assign resources with duplicate id.

    :param assign_resources_test_exec_settings: setup assign_resources_test_exec_settings
    """


@pytest.mark.skamid
@pytest.mark.assign
@pytest.mark.sdp
@scenario("features/sdp_assign_resources.feature", "Command assign resources twice in order")
def test_assign_resources_duplicate_commands(assign_resources_test_exec_settings):  # type: ignore
    """Command assign resources twice in order.

    :param assign_resources_test_exec_settings: setup assign_resources_test_exec_settings
    """


@pytest.mark.skip(reason="Unable to correctly tear down after this test")
@pytest.mark.skamid
@pytest.mark.assign
@pytest.mark.sdp
@scenario(
    "features/sdp_assign_resources.feature",
    "Assign resources with invalid processing block script name to SDP",
)
def test_assign_resources_with_invalid_script(assign_resources_test_exec_settings):  # type: ignore
    """Command assign resources twice in order.

    :param assign_resources_test_exec_settings: setup assign_resources_test_exec_settings
    """


@scenario("features/sdp_assign_resources.feature", "Abort assigning SDP")
def test_abort_in_resourcing_sdp_subarray_in_mid(
    set_restart_after_abort: None, composition: conf_types.Composition
):
    """
    Assign resources to sdp subarray in mid.

    :param set_restart_after_abort: object for set_restart_after_abort
    :param composition: A fixture that represents the composition of the subarray.
    """


@pytest.mark.skalow
@pytest.mark.assign
@pytest.mark.sdp
@scenario("features/sdp_assign_resources.feature", "Abort assigning SDP Low")
def test_abort_in_resourcing_sdp_subarray_in_low(
    set_restart_after_abort: None, composition: conf_types.Composition
):
    """
    Assign resources to sdp subarray in low.
    :param set_restart_after_abort: object for set_restart_after_abort
    :param composition: The assign resources configuration paramaters
    """


@given("an SDP subarray", target_fixture="composition")
def an_sdp_subarray(
    set_up_subarray_log_checking_for_sdp,  # type: ignore
    sdp_base_composition: conf_types.Composition,
    sut_settings: SutTestSettings,
) -> conf_types.Composition:
    """
    an SDP subarray.
    :param set_up_subarray_log_checking_for_sdp: A fixture for
        setting up log checking for the SDP subarray.
    :param sdp_base_composition: sdp_base_composition fixture
    :param sut_settings: sut_settings fixture
    :return: A class representing the sdp base configuration for the system under test.
    """
    sut_settings.default_subarray_name = sut_settings.tel.sdp.subarray(sut_settings.subarray_id)

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
    """the subarray must be in IDLE state.

    :param sut_settings: sut_settings fixture
    """
    sdp_subarray = con_config.get_device_proxy(sut_settings.default_subarray_name)
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.IDLE)


# mock tests
