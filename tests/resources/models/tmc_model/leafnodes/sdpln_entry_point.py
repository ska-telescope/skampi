"""Domain logic for the sdp."""
import logging
import os
import json
import copy
from time import sleep
from typing import List

from resources.utils.validation import CommandException, command_success
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from ska_ser_skallop.event_handling.handlers import WaitForLRCComplete
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    MessageBoardBuilder,
    NoOpStep,
)
from ska_ser_skallop.utils.singleton import Memo

from tests.resources.models.obsconfig.config import Observation

from ...obsconfig.config import Observation
from ...sdp_model.entry_point import (
    SdpAssignResourcesStep,
    SdpConfigureStep,
    SDPScanStep,
    StartUpStep,
)
from .utils import retry

logger = logging.getLogger(__name__)


class WithCommandID:
    def __init__(self) -> None:
        self._long_running_command_subscriber = None

    @property
    def long_running_command_subscriber(self) -> WaitForLRCComplete | None:
        return Memo().get("long_running_command_subscriber")

    @long_running_command_subscriber.setter
    def long_running_command_subscriber(self, subscriber: WaitForLRCComplete):
        Memo(long_running_command_subscriber=subscriber)


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


class SdpLnAssignResourcesStep(SdpAssignResourcesStep, WithCommandID):
    """Implementation of Assign Resources Step for SDP LN."""

    def __init__(self, observation: Observation) -> None:
        """
        Init object.

        :param observation: An instance of the Observation class or None.
            If None, a new instance of Observation will be created.
        """
        super().__init__(observation)
        self.unique_id: str | None = None

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
        # config = self.observation.generate_sdp_assign_resources_config().as_json
        
        config_json = copy.deepcopy(ASSIGN_RESOURCE_JSON_LOW)
        # we retry this command three times in case there is a transitory race
        # condition
        config = json.dumps(config_json)
        command_id = subarray.command_inout("AssignResources", config)
        if command_success(command_id):
            self.long_running_command_subscriber.set_command_id(command_id)
        else:
            self.long_running_command_subscriber.unsubscribe_all()
            raise CommandException(command_id)
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

        command_id = subarray.command_inout("ReleaseAllResources")
        if command_success(command_id):
            self.long_running_command_subscriber.set_command_id(command_id)
        else:
            self.long_running_command_subscriber.unsubscribe_all()
            raise CommandException(command_id)

        self._log(f"Commanding {subarray_name} to ReleaseAllResources")

    def set_wait_for_do_assign_resources(self, sub_array_id: int) -> MessageBoardBuilder | None:
        """
        Domain logic specifying what needs to be waited for
        subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
        """

        brd = get_message_board_builder()
        subarray_name = self._tel.tm.subarray(sub_array_id).sdp_leaf_node
        brd.set_waiting_on(subarray_name).for_attribute("sdpSubarrayObsState").to_become_equal_to(
            "IDLE"
        )
        self.long_running_command_subscriber = brd.set_wait_for_long_running_command_on(
            subarray_name
        )
        return brd

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
        subarray_name = self._tel.tm.subarray(sub_array_id).sdp_leaf_node
        brd.set_waiting_on(subarray_name).for_attribute("sdpSubarrayObsState").to_become_equal_to(
            "EMPTY", ignore_first=False
        )
        self.long_running_command_subscriber = brd.set_wait_for_long_running_command_on(
            subarray_name
        )
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
