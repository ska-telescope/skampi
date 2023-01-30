"""Assign resources to subarray feature tests."""
import logging
import pytest
import json,os
from assertpy import assert_that
from pytest_bdd import given, scenario, then, parsers

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
@scenario(
    "features/tmc_assign_resources_sut.feature", "Assign resources to subarray - happy flow"
)
def test_assign_resources_from_tmc_subarray_in_low():
    """Assign resources from tmc subarrays in low."""

#in conftest
# @given("the Telescope is in ON state")


@given(parsers.parse("the subarray {subarray_id} obsState is EMPTY"), 
       target_fixture="composition")
def subarray_obstate_is_empty(subarray_id, sut_settings: SutTestSettings,
                              set_up_subarray_log_checking_for_tmc,
                              base_composition):
    """an telescope subarray."""
    sut_settings.subarray_id = subarray_id
    tel = names.TEL()
    subarray = con_config.get_device_proxy(
        tel.tm.subarray(sut_settings.subarray_id)
        )
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.EMPTY)
    return base_composition



# using when from conftest
# @when("I issue the assignResources command with the {resources_list} to the subarray {subarray_id}")


@then(parsers.parse("the subarray {subarray_id} obsState is IDLE"))
def the_subarray_must_be_in_idle_state(subarray_id, sut_settings: SutTestSettings):
    """the subarray must be in IDLE state."""
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)

@then(parsers.parse("the correct resources {resources_list} are assigned"))
def check_resources_assigned(subarray_id, sut_settings: SutTestSettings):
    """the subarray must be in IDLE state."""
    resources_list = []
    json_file_path = os.path.join("tests", "resources", "test_data", "TMC_integration", "assign_resource_low.json")  
    with open(json_file_path) as f:
        config = f.read()
        config_json = json.loads(config)
        sdp_resources = config_json["sdp"]["resources"]
        csp_resources = config_json["csp"]["lowcbf"]["resources"]

        for resources in csp_resources:
            resources_list.append(resources["device"])

        tel = names.TEL()
        sdpsubarray = con_config.get_device_proxy(tel.sdp.subarray(subarray_id))
        cspsubarray = con_config.get_device_proxy(tel.csp.cbf.subarray(subarray_id))
        
    result_sdp = sdpsubarray.read_attribute("Resources").value
    result_csp = cspsubarray.read_attribute("assignedResources").value
    sdp_resources = str(sdp_resources).replace("\'", "\"")
    csp_resources = str(csp_resources)

    assert_that(result_sdp).is_equal_to(sdp_resources)
    assert_that(result_csp).is_equal_to(tuple(resources_list[::-1]))
        

