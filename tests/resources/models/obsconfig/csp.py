from typing import TypedDict, cast

from ska_tmc_cdm.messages.central_node.csp import CSPConfiguration as CSPAssignConfiguration
from ska_tmc_cdm.messages.subarray_node.configure.csp import (
    CBFConfiguration,
    CommonConfiguration,
    CSPConfiguration,
    FSPConfiguration,
    FSPFunctionMode,
    SubarrayConfiguration,
)

from tests.resources.models.obsconfig.target_spec import ArraySpec, BaseTargetSpec

from .base import encoded
from .dishes import Dishes
from .target_spec import TargetSpecs


class CSPrunScanConfig(TypedDict):
    scan_id: int
    interface: str


class CSPconfig(Dishes, TargetSpecs):
    csp_subarray_id = "dummy name"
    csp_scan_configure_schema = "https://schema.skao.int/ska-csp-configure/2.0"
    csp_assign_resources_schema = "https://schema.skao.int/ska-csp-assignresources/2.2"

    def __init__(
        self,
        base_target_specs: dict[str, BaseTargetSpec] | None = None,
        array: ArraySpec | None = None,
    ) -> None:
        Dishes.__init__(self, base_target_specs, array)
        TargetSpecs.__init__(self, base_target_specs, array)

    def _generate_low_csp_assign_resources_config(self):
        interface = "https://schema.skao.int/ska-low-csp-assignresources/2.0"
        common = {"subarray_id": 1}
        lowcbf = {
            "resources": [
                {
                    "device": "fsp_01",
                    "shared": True,
                    "fw_image": "pst",
                    "fw_mode": "unused",
                },
                {
                    "device": "p4_01",
                    "shared": True,
                    "fw_image": "p4.bin",
                    "fw_mode": "p4",
                },
            ]
        }
        return CSPAssignConfiguration(interface=interface, common=common, lowcbf=lowcbf)

    @encoded
    def generate_low_csp_assign_resources_config(self):
        return self._generate_low_csp_assign_resources_config()

    def _generate_csp_scan_config(self, target_id: str | None = None, subarray_id: int = 1):
        mode: FSPFunctionMode = FSPFunctionMode.CORR
        if target_id:
            spec = self.target_specs[target_id]
        else:
            target_id, spec = list(self.target_specs.items())[0]
        fsps = [1, 2]
        fsp1 = FSPConfiguration(
            fsp_id=fsps[0],
            function_mode=mode,
            frequency_slice_id=fsps[0],
            integration_factor=1,
            zoom_factor=0,
            channel_averaging_map=[(0, 2), (744, 0)],
            output_link_map=[(0, 0), (200, 1)],
            channel_offset=0,
        )
        fsp2 = FSPConfiguration(
            fsp_id=fsps[1],
            function_mode=FSPFunctionMode.CORR,
            frequency_slice_id=fsps[0],
            integration_factor=1,
            zoom_factor=1,
            channel_averaging_map=[(0, 2), (744, 0)],
            output_link_map=[(0, 4), (200, 5)],
            channel_offset=744,
            zoom_window_tuning=1050000,
        )
        return CSPConfiguration(
            self.csp_scan_configure_schema,
            SubarrayConfiguration(self.csp_subarray_id),
            CommonConfiguration(self.eb_id, spec.band, subarray_id),
            CBFConfiguration([fsp1, fsp2]),
        )

    @encoded
    def generate_csp_scan_config(self, target_id: str | None = None, subarray_id: int = 1):
        return self._generate_csp_scan_config(target_id, subarray_id)

    @encoded
    def generate_csp_assign_resources_config(self, subarray_id: int = 1):
        return {
            "interface": self.csp_assign_resources_schema,
            "subarray_id": subarray_id,
            "dish": {"receptor_ids": self.dish_allocation.receptor_ids},
        }

    def generate_csp_run_scan_config(
        self, target_id: str | None = None, subarray_id: int = 1
    ) -> CSPrunScanConfig:
        config = self.get_scan_id()
        csp_run_scan_config = cast(
            CSPrunScanConfig,
            {
                **config,
                **{"interface": "https://schema.skao.int/ska-csp-scan/2.0"},
            },
        )
        return csp_run_scan_config
