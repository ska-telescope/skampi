from typing import List
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.describing import mvp_names as names

from ..mvp_model.synched_entry_point import SynchedEntryPoint
from ..mvp_model import waiting


class MCCSEntryPoint(SynchedEntryPoint):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2
    nr_of_antennae = 8
    nr_of_apiu = 2
    nr_of_stations = 2
    nr_of_subracks = 1
    nr_of_tiles = 4

    def __init__(self) -> None:
        super().__init__()
        tel = names.TEL()
        assert tel.skalow
        self._tel = tel.skalow
        self.mccs_controller = con_config.get_device_proxy(self._tel.mccs.master)

    def set_wating_for_start_up(self) -> waiting.MessageBoardBuilder:
        # wait for mccs controller is done by super
        builder = super().set_wating_for_start_up()
        for index in range(1, self.nr_of_antennae + 1):
            device = self._tel.mccs.antenna(index)
            builder.set_waiting_on(device).for_attribute("state").to_become_equal_to(
                "ON"
            )
        for index in range(1, self.nr_of_apiu + 1):
            device = self._tel.mccs.apiu(index)
            builder.set_waiting_on(device).for_attribute("state").to_become_equal_to(
                "ON"
            )
        for index in range(1, self.nr_of_stations + 1):
            device = self._tel.mccs.station(index)
            builder.set_waiting_on(device).for_attribute("state").to_become_equal_to(
                "ON"
            )
        for index in range(1, self.nr_of_subracks + 1):
            device = self._tel.mccs.subrack(index)
            builder.set_waiting_on(device).for_attribute("state").to_become_equal_to(
                "ON"
            )
        for index in range(1, self.nr_of_tiles + 1):
            device = self._tel.mccs.tile(index)
            builder.set_waiting_on(device).for_attribute("state").to_become_equal_to(
                "ON"
            )
        return builder

    def set_telescope_to_running(self):
        self.mccs_controller.command_inout("Startup")

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

    def set_wating_for_shut_down(self) -> waiting.MessageBoardBuilder:
        # wait for mccs controller is done by super
        builder = super().set_wating_for_shut_down()
        for index in range(1, self.nr_of_antennae + 1):
            device = self._tel.mccs.antenna(index)
            builder.set_waiting_on(device).for_attribute("state").to_become_equal_to(
                "OFF"
            )
        for index in range(1, self.nr_of_apiu + 1):
            device = self._tel.mccs.apiu(index)
            builder.set_waiting_on(device).for_attribute("state").to_become_equal_to(
                "OFF"
            )
        for index in range(1, self.nr_of_apiu + 1):
            device = self._tel.mccs.apiu(index)
            builder.set_waiting_on(device).for_attribute("state").to_become_equal_to(
                "OFF"
            )
        for index in range(1, self.nr_of_stations + 1):
            device = self._tel.mccs.station(index)
            builder.set_waiting_on(device).for_attribute("state").to_become_equal_to(
                "OFF"
            )
        for index in range(1, self.nr_of_subracks + 1):
            device = self._tel.mccs.subrack(index)
            builder.set_waiting_on(device).for_attribute("state").to_become_equal_to(
                "OFF"
            )
        for index in range(1, self.nr_of_tiles + 1):
            device = self._tel.mccs.tile(index)
            builder.set_waiting_on(device).for_attribute("state").to_become_equal_to(
                "OFF"
            )
        return builder

    def set_telescope_to_standby(self):
        self.mccs_controller.command_inout("Off")

    def tear_down_subarray(self, sub_array_id: int):
        pass
