from typing import TypedDict, cast

from ska_tmc_cdm.messages.subarray_node.configure.csp import (
    CBFConfiguration,
    CommonConfiguration,
    CSPConfiguration,
    FSPConfiguration,
    FSPFunctionMode,
    SubarrayConfiguration,
)

from .base import encoded
from .target_spec import TargetSpecs


class CSPrunScanConfig(TypedDict):
    scan_id: int
    interface: str


class CSPconfig(TargetSpecs):
    csp_subarray_id = "dummy name"
    csp_scan_configure_schema = "https://schema.skao.int/ska-csp-configure/2.0"

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
        return CSPConfiguration(
            interface=interface, common=common, lowcbf=lowcbf
        )

    @encoded
    def generate_low_csp_assign_resources_config(self):
        return self._generate_low_csp_assign_resources_config()

    def _generate_csp_scan_config(
        self, target_id: str | None = None, subarray_id: int = 1
    ):
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
            zoom_window_tuning=650000,
        )
        return CSPConfiguration(
            self.csp_scan_configure_schema,
            SubarrayConfiguration(self.csp_subarray_id),
            CommonConfiguration(self.eb_id, spec.band, subarray_id),
            CBFConfiguration([fsp1, fsp2]),
        )

    @encoded
    def generate_csp_scan_config(
        self, target_id: str | None = None, subarray_id: int = 1
    ):
        return self._generate_csp_scan_config(target_id, subarray_id)

    def generate_csp_run_scan_config(
        self, target_id: str | None = None, subarray_id: int = 1
    ) -> CSPrunScanConfig:
        config = self.get_scan_id()
        csp_run_scan_config = cast(
            CSPrunScanConfig,
            {
                **config,
                **{
                    "interface": "https://schema.skao.int/ska-mid-csp-scan/2.0"
                },
            },
        )
        return csp_run_scan_config
