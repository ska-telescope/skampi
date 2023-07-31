"""Assign Resource on a SDP Subarray"""
import logging

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
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


# when
# use @when("I start up the telescope") from ...conftest

# @then("the SDP subarray must be in IDLE state")
# def the_sdp_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
#     """
#     the SDP Subarray must be in IDLE state.

#     :param sut_settings: A class representing the settings for the system under test.
#     """
#     tel = names.TEL()
#     subarray = con_config.get_device_proxy(tel.sdp.subarray(sut_settings.subarray_id))
#     result = subarray.read_attribute("obsState").value
#     logger.info(f"-----------------{result}")
#     assert_that(result).is_equal_to(ObsState.IDLE)


@when("I assign resources to it without eb_id")
def i_assign_resources_to_it_again(
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

    :param telescope_context: Dictionary containing the running telescope's devices
    :param context_monitoring: Object containing information about
        the context in which the test is being executed
    :param entry_point: Information about the entry point used for the test
    :param sb_config: Object containing the Subarray Configuration
    :param composition: Object containing information about the composition of the subarray
    :param integration_test_exec_settings: Object containing
        the execution settings for the integration test
    :param sut_settings: Object containing the system under test settings
    """

    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
    with context_monitoring.context_monitoring():
        with telescope_context.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            entry_point.compose_subarray(subarray_id, receptors, composition, sb_config.sbid)


@then("the SDP subarray throws an exception")
def the_sdp_subarray_must_be_raise_exception(sut_settings: SutTestSettings):
    """
    the SDP Subarray must be in IDLE state.

    :param sut_settings: A class representing the settings for the system under test.
    """
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.sdp_leaf_node)
    result, message = subarray.read_attribute("longRunningCommandResult").value
    logger.info(f"-----------------{message}")
    logger.info(f"-----------------{result}")
    assert_that(message).is_equal_to("Execution block eb-mvp01-20210623-00000 already exists")
