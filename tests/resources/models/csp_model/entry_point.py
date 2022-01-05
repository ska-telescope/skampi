from typing import List

from ..mvp_model.synched_entry_point import SynchedEntryPoint

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.configuration import types


class CSPEntryPoint(SynchedEntryPoint):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2

    def __init__(self) -> None:
        super().__init__()
        self._tel = names.TEL()
        self.csp_master = con_config.get_device_proxy(self._tel.csp.master)

    def set_telescope_to_running(self):
        self.csp_master.command_inout("On")
        for index in range(1, self.nr_of_subarrays + 1):
            subarray = con_config.get_device_proxy(self._tel.csp.subarray(index))
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
        pass

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
        self.csp_master.command_inout("Off")
        for index in range(1, self.nr_of_subarrays + 1):
            subarray = con_config.get_device_proxy(self._tel.csp.subarray(index))
            subarray.command_inout("Off")

    def tear_down_subarray(self, sub_array_id: int):
        pass
