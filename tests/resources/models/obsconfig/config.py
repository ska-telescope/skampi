import json
from typing import Any, cast

from ska_tmc_cdm.messages.central_node.assign_resources import AssignResourcesRequest
from ska_tmc_cdm.messages.subarray_node.configure import ConfigureRequest

from .base import encoded
from .csp import CSPconfig
from .dishes import Dishes
from .sdp_config import SdpConfig
from .tmc_config import TmcConfig


class Observation(SdpConfig, CSPconfig, Dishes, TmcConfig):

    assign_resources_schema = "https://schema.skao.int/ska-tmc-assignresources/2.1"

    def _generate_assign_resources_config(self, subarray_id: int = 1):
        assign_request = AssignResourcesRequest(
            subarray_id=subarray_id,
            dish_allocation=self.dish_allocation,
            sdp_config=self.generate_sdp_assign_resources_config().as_object,
            interface=self.assign_resources_schema,
        )
        return assign_request

    def _generate_scan_config(
        self, target_id: str | None = None, scan_duration: float = 6
    ):
        if target_id is None:
            target_id = self.next_target_id
        return ConfigureRequest(
            pointing=self.get_pointing_configuration(target_id),
            dish=self.get_dish_configuration(target_id),
            sdp=self.generate_sdp_scan_config(target_id).as_object,
            csp=self.generate_csp_scan_config(target_id).as_object,
            tmc=self.generate_tmc_scan_config(scan_duration),
        )

    @encoded
    def generate_assign_resources_config(self, subarray_id: int = 1):
        return self._generate_assign_resources_config(subarray_id)

    def generate_release_all_resources_config_for_central_node(
        self, subarray_id: int = 1
    ) -> str:
        config = {
            "interface": "https://schema.skao.int/ska-tmc-releaseresources/2.1",
            "transaction_id": "txn-....-00001",
            "subarray_id": subarray_id,
            "release_all": "true",
            "receptor_ids": [],
        }

        return json.dumps(config)

    @encoded
    def generate_scan_config(
        self, target_id: str | None = None, scan_duration: float = 6
    ):
        return self._generate_scan_config(target_id, scan_duration)

    @encoded
    def generate_run_scan_conf(self):
        return self.get_scan_id()

    def generate_scan_config_parsed_for_csp(
        self,
        target_id: str | None = None,
        subarray_id: int = 1,
        scan_duration: float = 6,
    ) -> str:
        config = cast(
            dict[str, Any], self.generate_scan_config(target_id, scan_duration).as_dict
        )
        csp_config = config["csp"]
        csp_config["pointing"] = config["pointing"]
        return json.dumps(csp_config)
