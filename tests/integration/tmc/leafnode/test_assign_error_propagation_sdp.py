import logging
import os
import time

import pytest
from pytest_bdd import given, scenario, then, when
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from tests.resources.models.obsconfig.config import Observation

from ...conftest import SutTestSettings

logger = logging.getLogger(__name__)


@pytest.mark.sdpln
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@scenario(
    "features/sdpln_assign_resources_mid.feature",
    "Error propagation",
)
def test_error_propogation_from_tmc_subarray_in_low():
    """Release resources from tmc subarrays in mid."""


@given("a TMC SDP subarray Leaf Node", target_fixture="composition")
def an_telescope_subarray(
    set_sdp_ln_entry_point,
    base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """
    an telescope subarray.

    :param set_up_subarray_log_checking_for_tmc: To set up subarray log checking for tmc.
    :param base_composition : An object for base composition
    :return: base composition
    """
    return base_composition

@given("subarray again in empty")
def subarray_in_empty(set_sdp_ln_error_entry_point):
    pass


@when("I assign resources for the second time with same eb_id")
def i_assign_resources_to_sdpsln(sut_settings: SutTestSettings, allocated_subarray: fxt_types.allocated_subarray):
    """
    I assign resources to it
    """
    tel = names.TEL()
    observation = Observation()
    subarray_name = tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node
    subarray = con_config.get_device_proxy(subarray_name)
    config = observation.generate_sdp_assign_resources_config().as_json
    allocated_subarray.disable_automatic_teardown()
    subarray.command_inout("AssignResources", config)


@then("the lrcr event throws error")
def lrcr_event(
    sut_settings: SutTestSettings,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    tel = names.TEL()
    subarray_name = tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node)
    time.sleep(10)
    # context_monitoring.wait_for(subarray_name).for_attribute("longRunningCommandResult").to_become_equal_to(
    #     "3", ignore_first=False, settings=integration_test_exec_settings
    # )
    _, resultcode_or_message = subarray.read_attribute("longRunningCommandResult").value

    assert resultcode_or_message == "3"
    # "Execution block eb-mvp01-20210623-00000 already exists"
