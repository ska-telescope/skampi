"""Domain logic for the sdp."""
import logging
from time import sleep
from typing import List
import json
import os

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.configuration import composition as comp
from ska_ser_skallop.mvp_control.configuration import configuration as conf
from ska_ser_skallop.event_handling.builders import get_message_board_builder

from ..mvp_model.synched_entry_point import (
    SynchedEntryPoint,
    waiting,
)

logger = logging.getLogger(__name__)
SCAN_DURATION = 1


class SDPEntryPoint(SynchedEntryPoint):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2

    def __init__(self) -> None:
        super().__init__()
        self._tel = names.TEL()
        self._sdp_master_name = self._tel.sdp.master
        self._live_logging = True if os.getenv("DEBUG") else False

    def set_offline_components_to_online(self):
        pass

    def set_waiting_for_offline_components_to_become_online(
        self,
    ):
        return None

    def _log(self, mssage: str):
        if self._live_logging:
            logger.info(mssage)

    def set_telescope_to_running(self):
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.sdp.subarray(index)
            subarray = con_config.get_device_proxy(self._tel.sdp.subarray(index))
            self._log(f"commanding {subarray_name} to On")
            subarray.command_inout("On")
        self._log(f"commanding {self._sdp_master_name} to On")
        sdp_master = con_config.get_device_proxy(self._sdp_master_name)
        sdp_master.command_inout("On")

    def abort_subarray(self, sub_array_id: int):
        pass

    def clear_configuration(self, sub_array_id: int):
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with End command")
        subarray.command_inout("End")

    def compose_subarray(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        composition: types.Composition,
        sb_id: str,
    ):
        # currently ignore composition as all types will be standard
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        standard_composition = comp.generate_standard_comp(
            sub_array_id, dish_ids, sb_id
        )
        sdp_standard_composition = json.dumps(json.loads(standard_composition)["sdp"])
        self._log(
            f"commanding {subarray_name} with AssignResources: {sdp_standard_composition} "
        )
        subarray.command_inout("AssignResources", sdp_standard_composition)

    def configure_subarray(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        configuration: types.ScanConfiguration,
        sb_id: str,
        duration: float,
    ):
        self._tel = names.TEL()
        global SCAN_DURATION  # pylint: disable=global-statement
        SCAN_DURATION = duration
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
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

    def reset_subarray(self, sub_array_id: int):
        pass

    def set_telescope_to_standby(self):
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.sdp.subarray(index)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"commanding {subarray_name} to Off")
            subarray.command_inout("Off")
        self._log(f"commanding {self._sdp_master_name} to Off")
        sdp_master = con_config.get_device_proxy(self._sdp_master_name)
        sdp_master.command_inout("Off")

    def tear_down_subarray(self, sub_array_id: int):
        self._tel = names.TEL()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"Commanding {subarray_name} to ReleaseResources")
        subarray.command_inout("ReleaseResources")

    def set_waiting_for_clear_configure(
        self, sub_array_id: int, receptors: List[int]
    ) -> waiting.MessageBoardBuilder:
        """[summary]

        :param sub_array_id: [description]
        :type sub_array_id: int
        :return: [description]
        :rtype: waiting.MessageBoardBuilder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")
        return builder

    def set_waiting_until_scanning(
        self, sub_array_id: int, receptors: List[int]
    ) -> waiting.MessageBoardBuilder:
        """[summary]

        :param sub_array_id: [description]
        :type sub_array_id: int
        :param receptors: [description]
        :type receptors: List[int]
        :return: [description]
        :rtype: waiting.MessageBoardBuilder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("SCANNING")
        return builder

    def scan(self, sub_array_id: int):
        """[summary]

        :param sub_array_id: [description]
        :type sub_array_id: int
        :return: [description]
        :rtype: [type]
        """
        scan_config = json.dumps({"id": 1})
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"Commanding {subarray_name} to Scan with {scan_config}")
        try:
            subarray.command_inout("Scan", scan_config)
            sleep(SCAN_DURATION)
            subarray.command_inout("EndScan")
        except Exception as exception:
            logger.exception(exception)
            raise exception
