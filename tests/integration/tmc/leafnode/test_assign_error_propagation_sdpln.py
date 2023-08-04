import logging

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from tests.resources.models.tmc_model.leafnodes.sdpln_error_entry_point import SDPLnErrorEntryPoint

from ...conftest import SutTestSettings

logger = logging.getLogger(__name__)


@pytest.mark.sdpln
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@scenario(
    "features/sdpsln_error.feature",
    "Error propagation",
)
def test_error_propogation_from_tmc_subarray_in_low():
    """Release resources from tmc subarrays in mid."""


@given("a TMC SDP subarray Leaf Node", target_fixture="composition")
def an_telescope_subarray(
    base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """
    an telescope subarray.

    :param set_up_subarray_log_checking_for_tmc: To set up subarray log checking for tmc.
    :param base_composition : An object for base composition
    :return: base composition
    """
    return base_composition


@given("I assign resources and release for the first time")
def i_release_all_resources_assigned_to_it(
    set_sdp_ln_entry_point,
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    I release all resources assigned to it.

    :param allocated_subarray: The allocated subarray to be configured.
    :param context_monitoring: Context monitoring object.
    :param entry_point: The entry point to be used for the configuration.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    sub_array_id = allocated_subarray.id

    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_releasing_a_subarray(integration_test_exec_settings):
            entry_point.tear_down_subarray(sub_array_id)


@given("subarray again in empty")
def subarray_in_empty(set_sdp_ln_error_entry_point):
    pass


@when("I assign resources for the second time with same eb_id")
def i_assign_resources_to_sdpsln(
    running_telescope: fxt_types.running_telescope,
    context_monitoring: fxt_types.context_monitoring,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """
    I assign resources to it

    :param running_telescope: Dictionary containing the running telescope's devices
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
        with running_telescope.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):

            SDPLnErrorEntryPoint().compose_subarray(
                subarray_id, receptors, composition, sb_config.sbid
            )


@then("the lrcr event throws error")
def lrcr_event(
    sut_settings: SutTestSettings,
    running_telescope: fxt_types.running_telescope,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node)
    subarray_name = tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node
    context_monitoring.wait_for(subarray_name).for_attribute(
        "longRunningCommandResult"
    ).to_become_equal_to("3", ignore_first=True, settings=integration_test_exec_settings)
    _, message = subarray.read_attribute("longRunningCommandResult").value

    assert message == "3"
    running_telescope.disable_automatic_setdown()
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.sdp.subarray(sut_settings.subarray_id))
    # context_monitoring.wait_for(subarray_name).for_attribute("obsState").to_become_equal_to(
    #     "E", ignore_first=False, settings=integration_test_exec_settings
    # )
    result = subarray.read_attribute("sdpSubarrayObsState").value
    assert result == "0"
