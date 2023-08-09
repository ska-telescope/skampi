# import logging
# import pytest
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
#     entry_point: fxt_types.entry_point,
#     sb_config: fxt_types.sb_config,
#     composition: conf_types.Composition,
#     sut_settings: SutTestSettings,
# ):
#     """
#     I assign resources to it

#     :param running_telescope: Dictionary containing the running telescope's devices
#     :param context_monitoring: Object containing information about
#         the context in which the test is being executed
#     :param entry_point: Information about the entry point used for the test
#     :param sb_config: Object containing the Subarray Configuration
#     :param composition: Object containing information about the composition of the subarray
#     :param integration_test_exec_settings: Object containing
#         the execution settings for the integration test
#     :param sut_settings: Object containing the system under test settings
#     """

#     subarray_id = sut_settings.subarray_id
#     receptors = sut_settings.receptors
#     entry_point.compose_subarray(subarray_id, receptors, composition, sb_config.sbid)


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
#     ).to_become_equal_to("EMPTY", ignore_first=False, settings=integration_test_exec_settings)

#     context_monitoring.wait_for(subarray_name).for_attribute(
#         "longRunningCommandResult"
#     ).to_become_equal_to(
#         [f"('{unique_id[0]}', 'Execution block eb-mvp01-20210623-00000 already exists')",f"('{unique_id[0]}', '3')"],
#         settings=integration_test_exec_settings,
#     )



import logging
import os
import time
import json
import copy

import pytest
from assertpy import assert_that
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
def i_assign_resources_to_sdpsln(
    sut_settings: SutTestSettings,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    composition: conf_types.Composition,
    sb_config: fxt_types.sb_config,
    entry_point: fxt_types.entry_point,
    running_telescope: fxt_types.running_telescope
    ):
    """
    I assign resources to it
    """
    global unique_id
    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors


    with running_telescope.wait_for_allocating_a_subarray(
        subarray_id, receptors, integration_test_exec_settings
    ):
        entry_point.compose_subarray(subarray_id, receptors, composition, sb_config.sbid)

    tel = names.TEL()
    observation = Observation()
    subarray_name = tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node
    subarray = con_config.get_device_proxy(subarray_name)
    # config = observation.generate_sdp_assign_resources_config().as_json
    config_json = copy.deepcopy(ASSIGN_RESOURCE_JSON_LOW)
        # we retry this command three times in case there is a transitory race
        # condition
    config = json.dumps(config_json)
    subarray.command_inout("AssignResources", config)
    # context_monitoring.wait_for(subarray_name).for_attribute(
    #     "sdpSubarrayObsState"
    # ).to_become_equal_to("IDLE", ignore_first=False, settings=integration_test_exec_settings)
    # subarray.command_inout("ReleaseAllResources")
    unique_id = subarray.command_inout("AssignResources", config)
    logger.info(f"--------------> unique_id {unique_id}")



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
    ).to_become_equal_to("IDLE", ignore_first=False, settings=integration_test_exec_settings)
    
    context_monitoring.wait_for(subarray_name).for_attribute(
        "longRunningCommandResult"
    ).to_become_equal_to(
        [f"('{unique_id[0]}', 'Execution block eb-mvp01-20210623-00000 already exists')",f"('{unique_id[0]}', '3')"],
        settings=integration_test_exec_settings,
    )

ASSIGN_RESOURCE_JSON_LOW = {
    "interface": "https://schema.skao.int/ska-low-tmc-assignresources/3.0",
    "transaction_id": "txn-....-00001",
    "subarray_id": 1,
    "mccs": {
        "subarray_beam_ids": [1],
        "station_ids": [[1, 2]],
        "channel_blocks": [3],
    },
    "sdp": {
        "interface": "https://schema.skao.int/ska-sdp-assignres/0.4",
        "resources": {"receptors": ["SKA001", "SKA002", "SKA003", "SKA004"]},
        "execution_block": {
            "eb_id": "eb-test-20220916-00000",
            "context": {},
            "max_length": 3600.0,
            "beams": [{"beam_id": "vis0", "function": "visibilities"}],
            "scan_types": [
                {
                    "scan_type_id": ".default",
                    "beams": {
                        "vis0": {
                            "channels_id": "vis_channels",
                            "polarisations_id": "all",
                        }
                    },
                },
                {
                    "scan_type_id": "target:a",
                    "derive_from": ".default",
                    "beams": {"vis0": {"field_id": "field_a"}},
                },
                {
                    "scan_type_id": "calibration:b",
                    "derive_from": ".default",
                    "beams": {"vis0": {"field_id": "field_b"}},
                },
            ],
            "channels": [
                {
                    "channels_id": "vis_channels",
                    "spectral_windows": [
                        {
                            "spectral_window_id": "fsp_1_channels",
                            "count": 4,
                            "start": 0,
                            "stride": 2,
                            "freq_min": 350000000.0,
                            "freq_max": 368000000.0,
                            "link_map": [[0, 0], [200, 1], [744, 2], [944, 3]],
                        }
                    ],
                }
            ],
            "polarisations": [
                {
                    "polarisations_id": "all",
                    "corr_type": ["XX", "XY", "YX", "YY"],
                }
            ],
            "fields": [
                {
                    "field_id": "field_a",
                    "phase_dir": {
                        "ra": [123.0],
                        "dec": [-60.0],
                        "reference_time": "...",
                        "reference_frame": "ICRF3",
                    },
                    "pointing_fqdn": "...",
                },
                {
                    "field_id": "field_b",
                    "phase_dir": {
                        "ra": [123.0],
                        "dec": [-60.0],
                        "reference_time": "...",
                        "reference_frame": "ICRF3",
                    },
                    "pointing_fqdn": "...",
                },
            ],
        },
        "processing_blocks": [
            {
                "pb_id": "pb-test-20220916-00000",
                "script": {
                    "kind": "realtime",
                    "name": "test-receive-addresses",
                    "version": "0.6.1",
                },
                "sbi_ids": ["sbi-test-20220916-00000"],
                "parameters": {
                    # makes sure that Configure transitions to READY
                    # after 5 seconds of being in CONFIGURING;
                    # this is only needed for `test-receive-addresses` script (v0.6.1+)
                    "time-to-ready": 5
                },
            }
        ],
    },
    "csp": {
        "interface": "https://schema.skao.int/ska-low-csp-assignresources/2.0",
        "common": {"subarray_id": 1},
        "lowcbf": {
            "resources": [
                {
                    "device": "fsp_01",
                    "shared": True,
                    "fw_image": "pst",
                    "fw_mode": "unused",
                },
                {
                    "device": "p4_01",
                    "shared": True,
                    "fw_image": "p4.bin",
                    "fw_mode": "p4",
                },
            ]
        },
    },
}
