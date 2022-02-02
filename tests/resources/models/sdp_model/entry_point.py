import imp
from typing import List
import json
import os
from ..mvp_model.synched_entry_point import SynchedEntryPoint

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.configuration import composition as comp

import logging

logger = logging.getLogger(__name__)


class SDPEntryPoint(SynchedEntryPoint):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2

    def __init__(self) -> None:
        super().__init__()
        self._tel = names.TEL()
        self._sdp_master_name = self._tel.sdp.master
        self._live_logging = True if os.getenv("DEBUG") else False

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
        pass

    def compose_subarray(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        composition: types.Composition,
        sb_id: str,
    ):
        self._tel = names.TEL()
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
        pass

    def reset_subarray(self, sub_array_id: int):
        pass

    def scan(self, sub_array_id: int):
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
