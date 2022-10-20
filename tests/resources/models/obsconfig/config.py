from ska_tmc_cdm.messages.central_node.assign_resources import (
    AssignResourcesRequest,
)
from ska_tmc_cdm.messages.subarray_node.configure import ConfigureRequest
from .sdp_config import SdpConfig
from .dishes import Dishes
from .csp import CSPconfig
from .tmc_config import TmcConfig
from .base import encoded


class Observation(SdpConfig, CSPconfig, Dishes, TmcConfig):

    assign_resources_schema = "https://schema.skao.int/ska-tmc-assignresources/2.1"

    def generate_assign_resources_config(self, subarray_id: int = 1):
        assign_request = AssignResourcesRequest()
        assign_request.interface = self.assign_resources_schema
        assign_request.sdp_config = (
            self.generate_sdp_assign_resources_config().as_object
        )
        assign_request.subarray_id = subarray_id
        assign_request.dish = self.get_dish_allocation_from_target_spec()
        return assign_request

    def generate_scan_config(
        self, target_id: str | None = None, scan_duration: float = 6
    ):
        return ConfigureRequest(
            pointing=self.get_pointing_configuration(target_id),
            dish=self.get_dish_configuration(target_id),
            sdp=self.generate_sdp_scan_config(target_id).as_object,
            csp=self.generate_csp_scan_config(target_id).as_object,
            tmc=self.generate_tmc_scan_config(scan_duration),
        )

    @encoded
    def generate_run_scan_conf(self):
        self.get_scan_id()
