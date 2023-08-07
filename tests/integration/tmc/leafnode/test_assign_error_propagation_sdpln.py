"""Assign Resource on a SDP Subarray"""
import pytest
import logging
from assertpy import assert_that
from pytest_bdd import given, scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

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


# @when("I assign resources to it") from ...conftest



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

@then("I assign resources command for second time")
def assign_resources_for_the_second_time(sut_settings: SutTestSettings):
    """Assign resources for two times"""

    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node)
    unique_id = subarray.command_inout("AssignResources", ASSIGN_MID_JSON)
    logger.info(f"-----------> unique_id{unique_id}")



ASSIGN_MID_JSON = {
    "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
    "transaction_id": "txn-....-00001",
    "subarray_id": 1,
    "dish": {"receptor_ids": ["SKA001"]},
    "sdp": {
        "interface": "https://schema.skao.int/ska-sdp-assignres/0.4",
        "execution_block": {
            "eb_id": "eb-mvp01-20210623-00000",
            "max_length": 100.0,
            "context": {},
            "beams": [
                {"beam_id": "vis0", "function": "visibilities"},
                {"beam_id": "pss1", "search_beam_id": 1, "function": "pulsar search"},
                {"beam_id": "pss2", "search_beam_id": 2, "function": "pulsar search"},
                {"beam_id": "pst1", "timing_beam_id": 1, "function": "pulsar timing"},
                {"beam_id": "pst2", "timing_beam_id": 2, "function": "pulsar timing"},
                {"beam_id": "vlbi1", "vlbi_beam_id": 1, "function": "vlbi"},
            ],
            "scan_types": [
                {
                    "scan_type_id": ".default",
                    "beams": {
                        "vis0": {"channels_id": "vis_channels", "polarisations_id": "all"},
                        "pss1": {
                            "field_id": "pss_field_0",
                            "channels_id": "pulsar_channels",
                            "polarisations_id": "all",
                        },
                        "pss2": {
                            "field_id": "pss_field_1",
                            "channels_id": "pulsar_channels",
                            "polarisations_id": "all",
                        },
                        "pst1": {
                            "field_id": "pst_field_0",
                            "channels_id": "pulsar_channels",
                            "polarisations_id": "all",
                        },
                        "pst2": {
                            "field_id": "pst_field_1",
                            "channels_id": "pulsar_channels",
                            "polarisations_id": "all",
                        },
                        "vlbi": {
                            "field_id": "vlbi_field",
                            "channels_id": "vlbi_channels",
                            "polarisations_id": "all",
                        },
                    },
                },
                {
                    "scan_type_id": "target:a",
                    "derive_from": ".default",
                    "beams": {"vis0": {"field_id": "field_a"}},
                },
            ],
            "channels": [
                {
                    "channels_id": "vis_channels",
                    "spectral_windows": [
                        {
                            "spectral_window_id": "fsp_1_channels",
                            "count": 744,
                            "start": 0,
                            "stride": 2,
                            "freq_min": 350000000.0,
                            "freq_max": 368000000.0,
                            "link_map": [[0, 0], [200, 1], [744, 2], [944, 3]],
                        },
                        {
                            "spectral_window_id": "fsp_2_channels",
                            "count": 744,
                            "start": 2000,
                            "stride": 1,
                            "freq_min": 360000000.0,
                            "freq_max": 368000000.0,
                            "link_map": [[2000, 4], [2200, 5]],
                        },
                        {
                            "spectral_window_id": "zoom_window_1",
                            "count": 744,
                            "start": 4000,
                            "stride": 1,
                            "freq_min": 360000000.0,
                            "freq_max": 361000000.0,
                            "link_map": [[4000, 6], [4200, 7]],
                        },
                    ],
                },
                {
                    "channels_id": "pulsar_channels",
                    "spectral_windows": [
                        {
                            "spectral_window_id": "pulsar_fsp_channels",
                            "count": 744,
                            "start": 0,
                            "freq_min": 350000000.0,
                            "freq_max": 368000000.0,
                        }
                    ],
                },
            ],
            "polarisations": [{"polarisations_id": "all", "corr_type": ["XX", "XY", "YY", "YX"]}],
            "fields": [
                {
                    "field_id": "field_a",
                    "phase_dir": {
                        "ra": [123, 0.1],
                        "dec": [80, 0.1],
                        "reference_time": "...",
                        "reference_frame": "ICRF3",
                    },
                    "pointing_fqdn": "low-tmc/telstate/0/pointing",
                }
            ],
        },
        "processing_blocks": [
            {
                "pb_id": "pb-mvp01-20210623-00000",
                "sbi_ids": ["sbi-mvp01-20200325-00001"],
                "script": {"kind": "realtime", "name": "vis_receive", "version": "0.1.0"},
                "parameters": {},
            },
            {
                "pb_id": "pb-mvp01-20210623-00001",
                "sbi_ids": ["sbi-mvp01-20200325-00001"],
                "script": {"kind": "realtime", "name": "test_realtime", "version": "0.1.0"},
                "parameters": {},
            },
            {
                "pb_id": "pb-mvp01-20210623-00002",
                "sbi_ids": ["sbi-mvp01-20200325-00002"],
                "script": {"kind": "batch", "name": "ical", "version": "0.1.0"},
                "parameters": {},
                "dependencies": [{"pb_id": "pb-mvp01-20210623-00000", "kind": ["visibilities"]}],
            },
            {
                "pb_id": "pb-mvp01-20210623-00003",
                "sbi_ids": ["sbi-mvp01-20200325-00001", "sbi-mvp01-20200325-00002"],
                "script": {"kind": "batch", "name": "dpreb", "version": "0.1.0"},
                "parameters": {},
                "dependencies": [{"pb_id": "pb-mvp01-20210623-00002", "kind": ["calibration"]}],
            },
        ],
        "resources": {
            "csp_links": [1, 2, 3, 4],
            "receptors": [
                "FS4",
                "FS8",
                "FS16",
                "FS17",
                "FS22",
                "FS23",
                "FS30",
                "FS31",
                "FS32",
                "FS33",
                "FS36",
                "FS52",
                "FS56",
                "FS57",
                "FS59",
                "FS62",
                "FS66",
                "FS69",
                "FS70",
                "FS72",
                "FS73",
                "FS78",
                "FS80",
                "FS88",
                "FS89",
                "FS90",
                "FS91",
                "FS98",
                "FS108",
                "FS111",
                "FS132",
                "FS144",
                "FS146",
                "FS158",
                "FS165",
                "FS167",
                "FS176",
                "FS183",
                "FS193",
                "FS200",
                "FS345",
                "FS346",
                "FS347",
                "FS348",
                "FS349",
                "FS350",
                "FS351",
                "FS352",
                "FS353",
                "FS354",
                "FS355",
                "FS356",
                "FS429",
                "FS430",
                "FS431",
                "FS432",
                "FS433",
                "FS434",
                "FS465",
                "FS466",
                "FS467",
                "FS468",
                "FS469",
                "FS470",
            ],
            "receive_nodes": 10,
        },
    },
}
