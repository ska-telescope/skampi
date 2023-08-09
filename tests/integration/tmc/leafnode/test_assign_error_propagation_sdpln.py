import logging
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
    "features/sdpsln_error.feature",
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


@when("I assign resources for the second time with same eb_id")
def i_assign_resources_to_sdpsln(sut_settings: SutTestSettings):
    """
    I assign resources to it
    """
    global unique_id
    tel = names.TEL()
    observation = Observation()
    subarray_name = tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node
    subarray = con_config.get_device_proxy(subarray_name)
    config = observation.generate_sdp_assign_resources_config().as_json

    result_code, unique_id = subarray.command_inout("AssignResources", config)


@then("the lrcr event throws error")
def lrcr_event(
    sut_settings: SutTestSettings,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    tel = names.TEL()
    subarray_name = tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node

    context_monitoring.re_init_builder()
    subarray = con_config.get_device_proxy(subarray_name)

    context_monitoring.wait_for(subarray_name).for_attribute(
        "sdpSubarrayObsState"
    ).to_become_equal_to("EMPTY", ignore_first=False, settings=integration_test_exec_settings)

    context_monitoring.wait_for(subarray_name).for_attribute(
        "longRunningCommandResult"
    ).to_become_equal_to(
        [f"('{unique_id[0]}', 'Execution block eb-mvp01-20210623-00000 already exists')",f"('{unique_id[0]}', '3')"],
        settings=integration_test_exec_settings,
    )



# import logging
# import os
# import time

# import pytest
# from assertpy import assert_that
# from pytest_bdd import given, scenario, then, when
# from resources.models.mvp_model.states import ObsState
# from ska_ser_skallop.connectors import configuration as con_config
# from ska_ser_skallop.mvp_control.describing import mvp_names as names
# from ska_ser_skallop.mvp_control.entry_points import types as conf_types
# from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

# from tests.resources.models.obsconfig.config import Observation

# from ...conftest import SutTestSettings

# logger = logging.getLogger(__name__)


# @pytest.mark.sdpln
# @pytest.mark.k8s
# @pytest.mark.k8sonly
# @pytest.mark.skalow
# @scenario(
#     "features/sdpsln_error.feature",
#     "Error propagation",
# )
# def test_error_propogation_from_tmc_subarray_in_low():
#     """Release resources from tmc subarrays in mid."""


# @given("a TMC SDP subarray Leaf Node", target_fixture="composition")
# def an_telescope_subarray(
#     set_sdp_ln_entry_point,
#     base_composition: conf_types.Composition,
# ) -> conf_types.Composition:
#     """
#     an telescope subarray.

#     :param set_up_subarray_log_checking_for_tmc: To set up subarray log checking for tmc.
#     :param base_composition : An object for base composition
#     :return: base composition
#     """
#     return base_composition


# @when("I assign resources for the second time with same eb_id")
# def i_assign_resources_to_sdpsln(
#     sut_settings: SutTestSettings,
#     context_monitoring: fxt_types.context_monitoring,
#     integration_test_exec_settings: fxt_types.exec_settings,
#     composition: conf_types.Composition,
#     sb_config: fxt_types.sb_config,
#     entry_point: fxt_types.entry_point,
#     running_telescope: fxt_types.running_telescope
#     ):
#     """
#     I assign resources to it
#     """
#     global unique_id
#     subarray_id = sut_settings.subarray_id
#     receptors = sut_settings.receptors


#     # with running_telescope.wait_for_allocating_a_subarray(
#     #     subarray_id, receptors, integration_test_exec_settings
#     # ):
#     #     entry_point.compose_subarray(subarray_id, receptors, composition, sb_config.sbid)

#     tel = names.TEL()
#     observation = Observation()
#     subarray_name = tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node
#     subarray = con_config.get_device_proxy(subarray_name)
#     config = observation.generate_sdp_assign_resources_config().as_json
#     subarray.command_inout("AssignResources", config)
#     context_monitoring.wait_for(subarray_name).for_attribute(
#         "sdpSubarrayObsState"
#     ).to_become_equal_to("IDLE", ignore_first=False, settings=integration_test_exec_settings)
#     subarray.command_inout("ReleaseAllResources")
#     unique_id = subarray.command_inout("AssignResources", config)
#     logger.info(f"--------------> unique_id {unique_id}")



# @then("the lrcr event throws error")
# def lrcr_event(
#     sut_settings: SutTestSettings,
#     context_monitoring: fxt_types.context_monitoring,
#     integration_test_exec_settings: fxt_types.exec_settings,
# ):
#     tel = names.TEL()
#     subarray_name = tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node

#     context_monitoring.re_init_builder()
#     subarray = con_config.get_device_proxy(subarray_name)

#     context_monitoring.wait_for(subarray_name).for_attribute(
#         "sdpSubarrayObsState"
#     ).to_become_equal_to("IDLE", ignore_first=False, settings=integration_test_exec_settings)
    
#     context_monitoring.wait_for(subarray_name).for_attribute(
#         "longRunningCommandResult"
#     ).to_become_equal_to(
#         [f"('{unique_id[0]}', 'Execution block eb-mvp01-20210623-00000 already exists')",f"('{unique_id[0]}', '3')"],
#         settings=integration_test_exec_settings,
#     )