"""Domain logic for the sdp."""
import logging
from typing import Union, List
import json
from time import sleep

from ska_ser_skallop.utils.singleton import Memo
from ska_ser_skallop.mvp_control.configuration import composition as comp
from ska_ser_skallop.mvp_control.configuration import configuration as conf
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    NoOpStep,
    MessageBoardBuilder,
)
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from ...sdp_model.entry_point import StartUpStep, SdpAssignResourcesStep, SdpConfigureStep, SDPScanStep

logger = logging.getLogger(__name__)


class StartLnUpStep(StartUpStep):
    """Implementation of Startup step for SDP LN"""

    def __init__(self, nr_of_subarrays: int) -> None:
        super().__init__(nr_of_subarrays)
        self._sdp_master_ln_name = self._tel.tm.sdp_leaf_node  # type: ignore

    def do(self):
        """Domain logic for starting up a telescope on the interface to SDP LN.

        This implments the set_telescope_to_running method on the entry_point.
        """
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.tm.subarray(index).sdp_leaf_node  # type: ignore
            subarray = con_config.get_device_proxy(subarray_name)  # type: ignore
            self._log(f"commanding {subarray_name} to On")
            subarray.command_inout("On")
        self._log(f"commanding {self._sdp_master_ln_name} to On")
        sdp_master_ln = con_config.get_device_proxy(self._sdp_master_ln_name)  # type: ignore
        sdp_master_ln.command_inout("On")

    def undo(self):
        """Domain logic for switching the SDP LN off."""
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.tm.subarray(index).sdp_leaf_node  # type: ignore
            subarray = con_config.get_device_proxy(subarray_name)  # type: ignore
            self._log(f"commanding {subarray_name} to Off")
            subarray.command_inout("Off")
        self._log(f"commanding {self._sdp_master_name} to Off")
        sdp_master_ln = con_config.get_device_proxy(self._sdp_master_ln_name)  # type: ignore
        sdp_master_ln.command_inout("Off")


class SdpLnAssignResourcesStep(SdpAssignResourcesStep):
    """Implementation of Assign Resources Step for SDP LN."""

    def do(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        composition: types.Composition,  # pylint: disable=
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
        subarray_name = self._tel.tm.subarray(sub_array_id).sdp_leaf_node  # type: ignore
        subarray = con_config.get_device_proxy(subarray_name)  # type: ignore
        standard_composition = comp.generate_standard_comp(
            sub_array_id, dish_ids, sb_id
        )
        sdp_standard_composition = json.dumps(json.loads(standard_composition)["sdp"])
        self._log(
            f"commanding {subarray_name} with AssignResources: {sdp_standard_composition} "
        )
        subarray.command_inout("AssignResources", sdp_standard_composition)

    def undo(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in sdp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.tm.subarray(sub_array_id).sdp_leaf_node  # type: ignore
        subarray = con_config.get_device_proxy(subarray_name)  # type: ignore
        self._log(f"Commanding {subarray_name} to ReleaseResources")
        subarray.command_inout("ReleaseResources")


class SdpLnConfigureStep(SdpConfigureStep):
    """Implementation of Configure Scan Step for SDP LN."""

    def do(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        configuration: types.ScanConfiguration,
        sb_id: str,
        duration: float,
    ):
        """Domain logic for configuring a scan on subarray in sdp LN.

        This implements the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration paramaters
        :param sb_id: a generic ide to identify a sb to assign resources
        """
        # scan duration needs to be a memorised for future objects that mnay require it
        Memo(scan_duration=duration)
        subarray_name = self._tel.tm.subarray(sub_array_id).sdp_leaf_node  # type: ignore
        subarray = con_config.get_device_proxy(subarray_name)  # type: ignore
        standard_configuration = conf.generate_standard_conf(
            sub_array_id, sb_id, duration
        )
        sdp_standard_configuration = json.dumps(
            json.loads(standard_configuration)["sdp"]
        )
        self._log(
            f"commanding {subarray_name} with Configure: {sdp_standard_configuration} "
        )
        subarray.command_inout("Configure", sdp_standard_configuration)

    def undo(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in sdp LN.

        This implments the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.tm.subarray(sub_array_id).sdp_leaf_node  # type: ignore
        subarray = con_config.get_device_proxy(subarray_name)  # type: ignore
        self._log(f"commanding {subarray_name} with End command")
        subarray.command_inout("End")


class SDPLnScanStep(SDPScanStep):

    """Implementation of Scan Step for SDP LN."""

    def do(self, sub_array_id: int):
        """Domain logic for running a scan on subarray in sdp.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        scan_config = json.dumps({"id": 1})
        scan_duration = Memo().get("scan_duration")
        subarray_name = self._tel.tm.subarray(sub_array_id).sdp_leaf_node  # type: ignore
        subarray = con_config.get_device_proxy(subarray_name)  # type: ignore
        self._log(f"Commanding {subarray_name} to Scan with {scan_config}")
        try:
            subarray.command_inout("Scan", scan_config)
            sleep(scan_duration)
            subarray.command_inout("EndScan")
        except Exception as exception:
            logger.exception(exception)
            raise exception

    def set_wait_for_do(
        self, sub_array_id: int, receptors: List[int]
    ) -> Union[MessageBoardBuilder, None]:
        """This is a no-op as there is no scanning command

        :param sub_array_id: The index id of the subarray to control
        """

    def undo(self, sub_array_id: int):
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        """

    def set_wait_for_doing(
        self, sub_array_id: int, receptors: List[int]
    ) -> Union[MessageBoardBuilder, None]:
        """Domain logic specifyig what needs to be done for waiting for subarray to be scanning.

        :param sub_array_id: The index id of the subarray to control
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("SCANNING", ignore_first=True)
        return builder

    def set_wait_for_undo(
        self, sub_array_id: int, receptors: List[int]
    ) -> Union[MessageBoardBuilder, None]:
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        """
        return None


class SDPLnEntryPoint(CompositeEntryPoint):
    """Derived Entrypoint scoped to SDP LN element."""

    nr_of_subarrays = 2

    def __init__(self) -> None:
        """Init Object"""
        super().__init__()
        self.set_online_step = NoOpStep()
        self.start_up_step = StartLnUpStep(self.nr_of_subarrays)
        self.assign_resources_step = SdpLnAssignResourcesStep()
        self.configure_scan_step = SdpLnConfigureStep()
        self.scan_step = SDPLnScanStep()
