from typing import List
import json
from ..mvp_model.synched_entry_point import SynchedEntryPoint

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.configuration import composition as comp


class SDPEntryPoint(SynchedEntryPoint):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2

    def __init__(self) -> None:
        super().__init__()
        self._tel = names.TEL()
        self.sdp_master = con_config.get_device_proxy(self._tel.sdp.master)

    def set_telescope_to_running(self):
        self.sdp_master.command_inout("On")
        for index in range(1, self.nr_of_subarrays + 1):
            subarray = con_config.get_device_proxy(self._tel.sdp.subarray(index))
            subarray.command_inout("On")

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
        subarray = con_config.get_device_proxy(self._tel.sdp.subarray(sub_array_id))
        standard_composition = comp.generate_standard_comp(
            sub_array_id, dish_ids, sb_id
        )
        sdp_standard_composition = json.dumps(json.loads(standard_composition)["sdp"])
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
            subarray = con_config.get_device_proxy(self._tel.sdp.subarray(index))
            subarray.command_inout("Off")
        self.sdp_master.command_inout("Off")

    def tear_down_subarray(self, sub_array_id: int):
        self._tel = names.TEL()
        subarray = con_config.get_device_proxy(self._tel.sdp.subarray(sub_array_id))
        subarray.command_inout("ReleaseResources")
