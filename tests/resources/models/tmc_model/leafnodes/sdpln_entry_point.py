"""Domain logic for the sdp."""
import logging
from time import sleep
from typing import List

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    MessageBoardBuilder,
    NoOpStep,
)
from ska_ser_skallop.utils.singleton import Memo

from ...mvp_model.env import get_error_propagation
from ...obsconfig.config import Observation
from ...sdp_model.entry_point import (
    SdpAssignResourcesStep,
    SdpConfigureStep,
    SDPScanStep,
    StartUpStep,
)
from .utils import retry

logger = logging.getLogger(__name__)


class StartUpLnStep(StartUpStep):
    """Implementation of Startup step for SDP LN"""

    def __init__(self, nr_of_subarrays: int) -> None:
        super().__init__(nr_of_subarrays)
        self._sdp_master_ln_name = self._tel.tm.sdp_leaf_node

    def do_startup(self):
        """Domain logic for starting up a telescope on the interface to SDP LN.

        This implments the set_telescope_to_running method on the entry_point.
        """
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.tm.subarray(index).sdp_leaf_node
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"commanding {subarray_name} to On")
            subarray.command_inout("On")
        self._log(f"commanding {self._sdp_master_ln_name} to On")
        sdp_master_ln = con_config.get_device_proxy(self._sdp_master_ln_name)
        sdp_master_ln.command_inout("On")

    def undo_startup(self):
        """Domain logic for switching the SDP LN off."""
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.tm.subarray(index).sdp_leaf_node
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"commanding {subarray_name} to Off")
            subarray.command_inout("Off")
        self._log(f"commanding {self._sdp_master_name} to Off")
        sdp_master_ln = con_config.get_device_proxy(self._sdp_master_ln_name)
        sdp_master_ln.command_inout("Off")


class SdpLnAssignResourcesStep(SdpAssignResourcesStep):
    """Implementation of Assign Resources Step for SDP LN."""

    def do_assign_resources(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        composition: types.Composition,
        sb_id: str,
    ):
        """Domain logic for assigning resources to a subarray in sdp LN.

        This implements the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration paramaters
        :param sb_id: a generic id to identify a sb to assign resources
        """
        # currently ignore composition as all types will be standard
        subarray_name = self._tel.tm.subarray(sub_array_id).sdp_leaf_node
        subarray = con_config.get_device_proxy(subarray_name)
        config = self.observation.generate_sdp_assign_resources_config().as_json
        # config = json.dumps(ASSIGN_MID_JSON)
        # we retry this command three times in case there is a transitory race
        # condition


        result_code, unique_id = subarray.command_inout("AssignResources", config)
        self.unique_id = unique_id

        self._log(f"commanding {subarray_name} with AssignResources: {config} ")

    def undo_assign_resources(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in sdp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.tm.subarray(sub_array_id).sdp_leaf_node
        subarray = con_config.get_device_proxy(subarray_name)

        # we retry this command three times in case there is a transitory race
        # condition

        @retry(nr_of_reties=3)
        def command():
            subarray.command_inout("ReleaseAllResources")

        self._log(f"Commanding {subarray_name} to ReleaseAllResources")
        command()

    def set_wait_for_do_assign_resources(self, sub_array_id: int) -> MessageBoardBuilder | None:
        """
        Domain logic specifying what needs to be waited for
        subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
        """
        try:
            brd = get_message_board_builder()
            subarray_name = self._tel.sdp.subarray(sub_array_id)
            brd.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to("IDLE")
            brd.set_waiting_on(subarray_name).for_attribute("longRunningCommandResult").to_become_equal_to((f"{self.unique_id}","0"))
            return brd
        except Exception:
            brd.set_waiting_on(subarray_name).for_attribute("longRunningCommandResult").to_become_equal_to((f"{self.unique_id}","3"))
            self._log("Error propagation true")

    def set_wait_for_doing_assign_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifyig what needs to be done for waiting
        for subarray to be scanning.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
        """
        brd = get_message_board_builder()
        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("RESOURCING")
        return brd

    def set_wait_for_undo_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited
        for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
        """
        brd = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        brd.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to("EMPTY")
        return brd


class SdpLnConfigureStep(SdpConfigureStep):
    """Implementation of Configure Scan Step for SDP LN."""

    def do_configure(
        self,
        sub_array_id: int,
        configuration: types.ScanConfiguration,
        sb_id: str,
        duration: float,
    ):
        """Domain logic for configuring a scan on subarray in sdp LN.

        This implements the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param sb_id: a generic ide to identify a sb to assign resources
        :param configuration: The assign resources configuration paramaters
        :param duration: scan duration for the do method
        """
        # scan duration needs to be a memorised for future objects
        # that mnay require it
        Memo(scan_duration=duration)
        subarray_name = self._tel.tm.subarray(sub_array_id).sdp_leaf_node
        subarray = con_config.get_device_proxy(subarray_name)
        config = self.observation.generate_sdp_scan_config().as_json
        # we retry this command three times in case there is a transitory race
        # condition

        @retry(nr_of_reties=3)
        def command():
            subarray.command_inout("Configure", config)

        self._log(f"commanding {subarray_name} with Configure: {config} ")
        command()

    def undo_configure(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in sdp LN.

        This implments the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.tm.subarray(sub_array_id).sdp_leaf_node
        subarray = con_config.get_device_proxy(subarray_name)
        # we retry this command three times in case there is a transitory race
        # condition

        @retry(nr_of_reties=3)
        def command():
            subarray.command_inout("End")

        self._log(f"commanding {subarray_name} with End command")
        command()


class SDPLnScanStep(SDPScanStep):

    """Implementation of Scan Step for SDP LN."""

    def do_scan(self, sub_array_id: int):
        """Domain logic for running a scan on subarray in sdp.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control

        :raises Exception: Raise exception in do method of scan command
        """
        scan_config = self.observation.generate_run_scan_conf().as_json
        scan_duration = Memo().get("scan_duration")
        subarray_name = self._tel.tm.subarray(sub_array_id).sdp_leaf_node
        subarray = con_config.get_device_proxy(subarray_name)
        # we retry this command three times in case there is a transitory race
        # condition

        @retry(nr_of_reties=3)
        def command():
            subarray.command_inout("Scan", scan_config)
            sleep(scan_duration)
            subarray.command_inout("EndScan")

        self._log(f"commanding {subarray_name} with End command")
        self._log(f"Commanding {subarray_name} to Scan with {scan_config}")
        try:
            command()
        except Exception as exception:
            logger.exception(exception)
            raise exception

    def set_wait_for_do_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """This is a no-op as there is no scanning command

        :param sub_array_id: The index id of the subarray to control
        :return: message board builder
        """
        return get_message_board_builder()

    def undo_scan(self, sub_array_id: int):
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        """

    def set_wait_for_doing_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifyig what needs to be done for
        waiting for subarray to be scanning.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "SCANNING", ignore_first=True
        )
        return builder

    def set_wait_for_undo_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        :return: message board builder
        """
        return get_message_board_builder()


class SDPLnEntryPoint(CompositeEntryPoint):
    """Derived Entrypoint scoped to SDP LN element."""

    nr_of_subarrays = 2

    def __init__(self, observation: Observation = None) -> None:
        """
        Init Object

        :param observation: An instance of the Observation class or None.
            If None, a new instance of Observation will be created.
        """
        super().__init__()
        if not observation:
            observation = Observation()
        self.observation = observation
        self.set_online_step = NoOpStep()
        self.start_up_step = StartUpLnStep(self.nr_of_subarrays)
        self.assign_resources_step = SdpLnAssignResourcesStep(observation)
        self.configure_scan_step = SdpLnConfigureStep(observation)
        self.scan_step = SDPLnScanStep(observation)


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
