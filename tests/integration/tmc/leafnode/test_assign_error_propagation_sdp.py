import logging

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when

# from resources.models.mvp_model.env import set_error_propagation
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from ...conftest import SutTestSettings

logger = logging.getLogger(__name__)


@pytest.mark.sdpln
@pytest.mark.skalow
@pytest.mark.assign
@scenario(
    "features/sdpln_assign_resources_mid.feature",
    "Assign resources to sdp low subarray using TMC leaf node",
)
def test_assign_resources_on_sdp_in_low():
    """AssignResources on sdp subarray in low using the leaf node."""


@given("a SDP subarray in the EMPTY state", target_fixture="composition")
def an_sdp_subarray_in_empty_state(
    set_sdp_ln_entry_point, base_composition: conf_types.Composition
) -> conf_types.Composition:
    """
    an SDP subarray in Empty state.

    :param set_sdp_ln_entry_point: An object to set sdp leafnode entry point
    :param base_composition : An object for base composition
    :return: base composition
    """
    return base_composition


@given("a TMC SDP subarray Leaf Node")
def a_sdp_sln():
    """a TMC SDP subarray Leaf Node."""


@when("I assign resources for the first time")
def assign_resources_with_subarray_id(
    telescope_context: fxt_types.telescope_context,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """
    I assign resources to it

    :param telescope_context: A fixture that represents the telescope context.
    :param context_monitoring: A fixture that represents the context monitoring service.
    :param entry_point: A fixture that represents the entry point for the subarray.
    :param sb_config: A fixture that represents the scan configuration for the subarray.
    :param composition: A fixture that represents the composition of the subarray.
    :param integration_test_exec_settings: A fixture that represents the execution
        settings for the integration test.
    :param sut_settings: An instance of the `SutTestSettings` class representing
        the settings for the system under test.
    """
    receptors = sut_settings.receptors
    subarray_id = sut_settings.subarray_id
    with context_monitoring.context_monitoring():
        telescope_context.disable_automatic_setdown()
        with telescope_context.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            entry_point.compose_subarray(subarray_id, receptors, composition, sb_config.sbid)


@then("the SDP subarray must be in IDLE state")
def the_sdp_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
    """
    the SDP Subarray must be in IDLE state.

    :param sut_settings: A class representing the settings for the system under test.
    """
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.sdp.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)


@when("I assign resources to it again")
def assign_resources_with_subarray(
    telescope_context: fxt_types.telescope_context,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """
    I assign resources to it

    :param telescope_context: A fixture that represents the telescope context.
    :param context_monitoring: A fixture that represents the context monitoring service.
    :param entry_point: A fixture that represents the entry point for the subarray.
    :param sb_config: A fixture that represents the scan configuration for the subarray.
    :param composition: A fixture that represents the composition of the subarray.
    :param integration_test_exec_settings: A fixture that represents the execution
        settings for the integration test.
    :param sut_settings: An instance of the `SutTestSettings` class representing
        the settings for the system under test.
    """
    # set_error_propagation(True)
    receptors = sut_settings.receptors
    subarray_id = sut_settings.subarray_id
    with context_monitoring.context_monitoring():
        telescope_context.disable_automatic_setdown()
        with telescope_context.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            entry_point.compose_subarray(subarray_id, receptors, composition, sb_config.sbid)
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.sdp.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    logger.info(result)
