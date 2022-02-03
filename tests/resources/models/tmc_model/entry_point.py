import json
import logging
from typing import Any, List
import os

from ska_ser_skallop.connectors.configuration import get_device_proxy
from ska_ser_skallop.mvp_control.configuration import composition as comp
from ska_ser_skallop.mvp_control.configuration import configuration as conf
from ska_ser_skallop.mvp_control.configuration.types import ScanConfiguration
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.utils import env
from ska_ser_skallop.utils.singleton import Singleton


# from ska_ser_skallop.utils.nrgen import get_int_id
from ..mvp_model.synched_entry_point import SynchedEntryPoint

logger = logging.getLogger(__name__)


class TMCEntryPoint(SynchedEntryPoint, metaclass=Singleton):

    nr_of_subarrays = 3

    def __init__(self) -> None:
        super().__init__()
        if env.telescope_type_is_mid():
            central_node_name = names.Mid.tm.central_node
        else:
            central_node_name = names.Low.tm.central_node
        self.central_node = get_device_proxy(central_node_name, fast_load=True)
        self._live_logging = bool(os.getenv("DEBUG"))

    def _log(self, mssage: str):
        if self._live_logging:
            logger.info(mssage)

    def set_waiting_for_offline_components_to_become_online(self):
        pass

    def set_offline_components_to_online(self):
        pass

    def set_telescope_to_running(self):
        if env.telescope_type_is_mid():
            self._log("commanding central_node to TelescopeOn")
            self.central_node.command_inout("TelescopeOn")
        elif env.telescope_type_is_low():
            self._log("commanding central_node to TelescopeOn")
            self.central_node.command_inout("StartUpTelescope")

    def set_telescope_to_standby(self):
        if env.telescope_type_is_mid():
            self._log("commanding central_node to TelescopeOff")
            self.central_node.command_inout("TelescopeOff")
        elif env.telescope_type_is_low():
            self._log("commanding central_node to StandByTelescope")
            self.central_node.command_inout("StandByTelescope")

    @staticmethod
    def _get_subarray(sub_array_id: int):
        if env.telescope_type_is_mid():
            return get_device_proxy(str(names.Mid.tm.subarray(sub_array_id)))
        return get_device_proxy(str(names.Low.tm.subarray(sub_array_id)))

    def tear_down_subarray(self, sub_array_id: int):
        configuration = comp.generate_tear_down_all_resources(sub_array_id)
        self._log(f"commanding central_node to ReleaseResources: {configuration}")
        self.central_node.command_inout("ReleaseResources", configuration)

    def compose_subarray(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        composition: Any,
        sb_id: str,
    ):
        if isinstance(composition, conf_types.Composition):
            if composition.conf_type == conf_types.CompositionType.STANDARD:
                resource_config = comp.generate_standard_comp(
                    sub_array_id, dish_ids, sb_id
                )
                self._log(
                    f"commanding central_node to AssignResources: {resource_config}"
                )
                self.central_node.command_inout("AssignResources", resource_config)
                return
        raise NotImplementedError(
            f"allocate using composition {composition} not implemented"
        )

    def configure_subarray(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        configuration: ScanConfiguration,
        sb_id: str,
        duration: float,
    ):
        subarray = self._get_subarray(sub_array_id)
        if isinstance(configuration, conf_types.ScanConfiguration):
            if configuration.conf_type == conf_types.ScanConfigurationType.STANDARD:
                scan_config = conf.generate_standard_conf(sub_array_id, sb_id, duration)
                self._log(f"commanding {subarray.name()} to Configure: {scan_config}")
                subarray.command_inout("Configure", scan_config)

    def clear_configuration(self, sub_array_id: int):
        subarray = self._get_subarray(sub_array_id)
        self._log(f"commanding {subarray.name()} to End SB (clear scan config)")
        subarray.command_inout("End")

    def abort_subarray(self, sub_array_id: int):
        subarray = self._get_subarray(sub_array_id)
        self._log(f"commanding {subarray.name()} to Abort")
        subarray.command_inout("Abort")

    def reset_subarray(self, sub_array_id: int):
        subarray = self._get_subarray(sub_array_id)
        self._log(f"commanding {subarray.name()} to Reset")
        subarray.command_inout("ObsReset")

    def scan(self, sub_array_id: int):
        # scan_id = get_int_id()
        scan_id = 1
        scan_id = json.dumps(
            {
                "interface": "https://schema.skao.intg/ska-tmc-scan/2.0",
                "transaction_id": "txn-....-00001",
                "scan_id": scan_id,
            }
        )
        subarray = self._get_subarray(sub_array_id)
        self._log(f"commanding {subarray.name()} to Scan with {scan_id}")
        subarray.command_inout("Scan", scan_id)
