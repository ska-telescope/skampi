"""
test_XTP-
---------------------------------------------------------
Tests for Configuring a scan on low telescope subarray using OET from scan duration (XTP-).
"""
import pytest
from assertpy import assert_that
from pytest_bdd import given, when, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_oso_scripting.objects import SubArray
from resources.models.mvp_model.states import ObsState
from ska_tmc_cdm.schemas import CODEC
from ska_tmc_cdm.messages.subarray_node.configure import ConfigureRequest
from ..conftest import SutTestSettings

@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.configure
@scenario("features/oet_configure_scan.feature", "Configure the low telescope subarray using OET")
def test_oet_configure_scan_on_low_subarray():
    """Configure scan on OET low telescope subarray."""


@given("an OET")
def an_oet():
    """an OET"""

@given("a low telescope subarray in IDLE state")
def a_subarray_in_the_idle_state(
    running_telescope: fxt_types.running_telescope,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """I assign resources to it in low."""

    subarray_id = sut_settings.subarray_id
    subarray = SubArray(subarray_id)
    receptors = sut_settings.receptors
    observation = sut_settings.observation
    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            config = observation.generate_low_assign_resources_config(subarray_id).as_object
            subarray.assign_from_cdm(config)

    """when resources assigned the low telescope subarray goes in IDLE state."""
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)    

@when("I configure it for a scan")
def i_configure_it_for_a_scan(
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """I configure it for a scan."""
    
    low_config_json="""{
    "interface": "https://schema.skao.int/ska-low-tmc-configure/3.0",
    "transaction_id": "txn-....-00001",
    "mccs": {
        "stations": [
            {
                "station_id": 1
            },
            {
                "station_id": 2
            }
        ],
        "subarray_beams": [
            {
                "subarray_beam_id": 1,
                "station_ids": [
                    1,
                    2
                ],
                "update_rate": 0,
                "channels": [
                    [
                        0,
                        8,
                        1,
                        1
                    ],
                    [
                        8,
                        8,
                        2,
                        1
                    ],
                    [
                        24,
                        16,
                        2,
                        1
                    ]
                ],
                "antenna_weights": [
                    1,
                    1,
                    1
                ],
                "phase_centre": [
                    0,
                    0
                ],
                "target": {
                    "reference_frame": "HORIZON",
                    "target_name": "DriftScan",
                    "az": 180,
                    "el": 45
                }
            }
        ]
    },
    "sdp": {
        "interface": "https://schema.skao.int/ska-sdp-configure/0.4",
        "scan_type": "science_A"
    },
    "csp": {
        "interface": "https://schema.skao.int/ska-csp-configure/2.0",
        "subarray": {
            "subarray_name": "science period 23"
        },
        "common": {
            "config_id": "sbi-mvp01-20200325-00001-science_A"
        },
        "lowcbf": {
            "stations": {
                "stns": [
                    [
                        1,
                        0
                    ],
                    [
                        2,
                        0
                    ],
                    [
                        3,
                        0
                    ],
                    [
                        4,
                        0
                    ]
                ],
                "stn_beams": [
                    {
                        "beam_id": 1,
                        "freq_ids": [
                            64,
                            65,
                            66,
                            67,
                            68,
                            68,
                            70,
                            71
                        ],
                        "boresight_dly_poly": "url"
                    }
                ]
            },
            "timing_beams": {
                "beams": [
                    {
                        "pst_beam_id": 13,
                        "stn_beam_id": 1,
                        "offset_dly_poly": "url",
                        "stn_weights": [
                            0.9,
                            1,
                            1,
                            0.9
                        ],
                        "jones": "url",
                        "dest_chans": [
                            128,
                            256
                        ],
                        "rfi_enable": [
                            true,
                            true,
                            true
                        ],
                        "rfi_static_chans": [
                            1,
                            206,
                            997
                        ],
                        "rfi_dynamic_chans": [
                            242,
                            1342
                        ],
                        "rfi_weighted": 0.87
                    }
                ]
            }
        }
    },
    "tmc": {
        "scan_duration": 10
    }
}"""    

    #delete above & uncomment below after replacing obsconfig 
    #observation = sut_settings.observation
    #scan_duration = sut_settings.scan_duration
    config_obj=CODEC.loads(ConfigureRequest, low_config_json)
    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_configuring_a_subarray(
            integration_test_exec_settings
        ):
            #config = observation.generate_low_tmc_scan_config(scan_duration, low_tmc=True).as_object
            tel = names.TEL()
            subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
            #logging.info(f"...:{config. . }")
            subarray.configure_from_cdm(config_obj)

@then("the subarray must be in the READY state")
def the_subarray_must_be_in_the_ready_state(
    sut_settings: SutTestSettings, integration_test_exec_settings: fxt_types.exec_settings
):
    """the subarray must be in the READY state."""
    tel = names.TEL()
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(
        str(tel.tm.subarray(sut_settings.subarray_id)))
    oet_subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = oet_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)
