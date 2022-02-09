"""Domain logic for the cbf."""
from typing import List
import logging
import json
import os

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.configuration import configuration as conf
from ..mvp_model import waiting

from ..mvp_model.synched_entry_point import SynchedEntryPoint

logger = logging.getLogger(__name__)


class CBFEntryPoint(SynchedEntryPoint):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2

    def __init__(self) -> None:
        super().__init__()
        self._tel = names.TEL()
        self.cbf_controller = con_config.get_device_proxy(self._tel.csp.cbf.controller)
        self._live_logging = bool(os.getenv("DEBUG"))

    def _log(self, mssage: str):
        if self._live_logging:
            logger.info(mssage)

    def set_offline_components_to_online(self):
        pass

    def set_waiting_for_offline_components_to_become_online(
        self,
    ):
        return None

    def set_telescope_to_running(self):
        self.cbf_controller.command_inout("On")
        # cbf low needs to start up subarrays individually
        if self._tel.skalow:
            subarray = con_config.get_device_proxy(self._tel.csp.cbf.subarray(1))
            subarray.command_inout(("On"))

    def abort_subarray(self, sub_array_id: int):
        pass

    def set_waiting_for_assign_resources(
        self,
        sub_array_id: int,
    ) -> waiting.MessageBoardBuilder:
        builder = waiting.get_message_board_builder()
        self._tel = names.TEL()
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")

        return builder

    def compose_subarray(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        composition: types.Composition,
        sb_id: str,
    ):
        self._tel = names.TEL()
        if self._tel.skamid:
            subarray_name = self._tel.skamid.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"commanding {subarray_name} with AddReceptors: {dish_ids} ")
            subarray.command_inout("AddReceptors", dish_ids)
        elif self._tel.skalow:
            subarray_name = self._tel.skalow.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            cbf_low_configuration = json.dumps(cbf_low_assign_resources)
            self._log(
                f"commanding {subarray_name} with AssignResources: {cbf_low_configuration} "
            )
            subarray.command_inout("AssignResources", cbf_low_configuration)

    def set_waiting_for_configure(
        self, sub_array_id: int, receptors: List[int]
    ) -> waiting.MessageBoardBuilder:
        builder = waiting.get_message_board_builder()
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("READY")
        return builder

    def configure_subarray(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        configuration: types.ScanConfiguration,
        sb_id: str,
        duration: float,
    ):
        self._tel = names.TEL()
        if self._tel.skamid:
            subarray_name = self._tel.skamid.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            standard_configuration = conf.generate_standard_conf(
                sub_array_id, sb_id, duration
            )
            cbf_config = json.loads(standard_configuration)["csp"]["cbf"]
            common = json.loads(standard_configuration)["csp"]["common"]
            cbf_config["common"] = common
            cbf_standard_configuration = json.dumps(
                {"cbf": cbf_config, "common": common}
            )
            self._log(
                f"commanding {subarray_name} with ConfigureScan: {cbf_standard_configuration} "
            )
            subarray.command_inout("ConfigureScan", cbf_standard_configuration)
        if self._tel.skalow:
            subarray_name = self._tel.skalow.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            cbf_low_configuration = json.dumps(cbf_low_configure_scan)
            self._log(
                f"commanding {subarray_name} with ConfigureScan: {cbf_low_configuration} "
            )
            subarray.command_inout("ConfigureScan", cbf_low_configuration)

    def set_waiting_for_clear_configure(
        self, sub_array_id: int, receptors: List[int]
    ) -> waiting.MessageBoardBuilder:
        builder = waiting.get_message_board_builder()
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")
        return builder

    def clear_configuration(self, sub_array_id: int):
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with command GoToIdle")
        subarray.command_inout("GoToIdle")

    def reset_subarray(self, sub_array_id: int):
        pass

    def scan(self, sub_array_id: int):
        pass

    def set_telescope_to_standby(self):
        #  mid uses standby
        if self._tel.skamid:
            self.cbf_controller.command_inout("Off")
        else:
            self.cbf_controller.command_inout("Off")
            # low needs to manually switch off subarray 1
            subarray = con_config.get_device_proxy(self._tel.csp.cbf.subarray(1))
            subarray.command_inout(("Off"))

    def set_waiting_for_release_resources(
        self,
        sub_array_id: int,
    ) -> waiting.MessageBoardBuilder:
        builder = waiting.get_message_board_builder()
        self._tel = names.TEL()
        if self._tel.skamid:
            subarray_name = self._tel.skamid.csp.cbf.subarray(sub_array_id)
            builder.set_waiting_on(subarray_name).for_attribute(
                "obsState"
            ).to_become_equal_to("EMPTY")

        return builder

    def tear_down_subarray(self, sub_array_id: int):
        self._tel = names.TEL()
        if self._tel.skamid:
            subarray_name = self._tel.skamid.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"commanding {subarray_name} with RemoveAllReceptors")
            subarray.command_inout("RemoveAllReceptors")
        if self._tel.skalow:
            subarray_name = self._tel.skalow.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"commanding {subarray_name} with ReleaseAllResources")
            subarray.command_inout("ReleaseAllResources")


cbf_low_assign_resources = {
    "common": {"subarrayID": 1},
    "lowcbf": {
        "stations": [
            {"station_id": 1, "sub_station_id": 1},
            {"station_id": 3, "sub_station_id": 1},
            {"station_id": 3, "sub_station_id": 2},
        ],
        "station_beams": [
            {
                "station_beam_id": 1,
                "channels": [1, 2, 3, 4, 5, 6, 7, 8],
                "pst_beams": [{"pst_beam_id": 1}, {"pst_beam_id": 2}],
            },
            {
                "station_beam_id": 2,
                "channels": [9, 10, 11, 12, 13, 14, 15],
                "pst_beams": [{"pst_beam_id": 3}],
            },
        ],
    },
}

cbf_low_configure_scan = {
    "id": 1,
    "scanId": 1,
    "stationType": 0,
    "common": {"id": 1},
    "lowcbf": {
        "jones_source": "tango://host:port/domain/family/member",
        "station_beams": [
            {
                "station_beam_id": 1,
                "station_delay_src": "tango://host:port/domain/family/member",
                "visibility_dest": [
                    {"dest_ip": "10.0.2.1", "dest_mac": "02:00:00:00:02:01"}
                ],
                "pst_beams": [
                    {
                        "pst_beam_id": 1,
                        "pst_beam_delay_src": "tango://host:port/domain/family/member",
                        "pst_beam_dest": [
                            {
                                "dest_ip": "10.0.3.1",
                                "dest_mac": "02:00:00:00:03:01",
                                "channels": 200,
                            },
                            {
                                "dest_ip": "10.0.3.2",
                                "dest_mac": "02:00:00:00:03:02",
                                "channels": 500,
                            },
                        ],
                    },
                    {
                        "pst_beam_id": 2,
                        "pst_beam_delay_src": "tango://host:port/domain/family/member",
                        "pst_beam_dest": [
                            {
                                "dest_ip": "10.0.3.3",
                                "dest_mac": "02:00:00:00:03:03",
                                "channels": 200,
                            },
                            {
                                "dest_ip": "10.0.3.4",
                                "dest_mac": "02:00:00:00:03:04",
                                "channels": 500,
                            },
                        ],
                    },
                ],
            },
            {
                "station_beam_id": 2,
                "station_delay_src": "tango://host:port/domain/family/member",
                "visibility_dest": [
                    {"dest_ip": "10.0.3.3", "dest_mac": "02:00:00:00:03:03"}
                ],
                "pst_beams": [
                    {
                        "pst_beam_id": 3,
                        "pst_beam_delay_src": "tango://host:port/domain/family/member",
                        "pst_beam_dest": [
                            {
                                "dest_ip": "10.0.2.5",
                                "dest_mac": "02:00:00:00:02:05",
                                "channels": 200,
                            },
                            {
                                "dest_ip": "10.0.2.6",
                                "dest_mac": "02:00:00:00:02:06",
                                "channels": 500,
                            },
                        ],
                    }
                ],
            },
        ],
    },
}
