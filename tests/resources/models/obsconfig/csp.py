from ska_tmc_cdm.messages.subarray_node.configure.csp import (
    CBFConfiguration,
    CommonConfiguration,
    CSPConfiguration,
    FSPConfiguration,
    FSPFunctionMode,
    SubarrayConfiguration,
    BeamConfiguration,
    LowCBFConfiguration,
    StationConfiguration,
    StnBeamConfiguration,
    TimingBeamConfiguration, 
)

from .base import encoded
from .target_spec import TargetSpecs


class CSPconfig(TargetSpecs):
    csp_subarray_id = "dummy name"
    csp_scan_configure_schema = "https://schema.skao.int/ska-csp-configure/2.0"
    config_id = "sbi-mvp01-20200325-00001-science_A"

    def _generate_low_csp_assign_resources_config(self):
        interface = "https://schema.skao.int/ska-low-csp-assignresources/2.0"
        common = {
            "subarray_id": 1
        }
        lowcbf = {
            "resources": [
                {
                    "device": "fsp_01",
                    "shared": True,
                    "fw_image": "pst",
                    "fw_mode": "unused"
                },
                {
                    "device": "p4_01",
                    "shared": True,
                    "fw_image": "p4.bin",
                    "fw_mode": "p4"
                }
            ]
        }
        return CSPConfiguration(
            interface=interface,
            common=common,
            lowcbf=lowcbf
        )

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
            zoom_window_tuning=650000,
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

    def _generate_low_csp_scan_config(self, target_id: str | None = None, subarray_id: int = 1):
        mode: FSPFunctionMode = FSPFunctionMode.CORR
        if target_id:
            spec = self.target_specs[target_id]
        else:
            target_id, spec = list(self.target_specs.items())[0]
        stn_beams = StnBeamConfiguration(
            beam_id=1, freq_ids=[64, 65, 66, 67, 68, 69, 70, 71], boresight_dly_poly="url"
        )
        stations = StationConfiguration(
            stns=[[1, 0], [2, 0], [3, 0], [4, 0]], stn_beams=[stn_beams]
        )
        beams = BeamConfiguration(
            pst_beam_id=13,
            stn_beam_id=1,
            offset_dly_poly="url",
            stn_weights=[0.9, 1.0, 1.0, 0.9],
            jones="url",
            dest_chans=[128, 256],
            rfi_enable=[True, True, True],
            rfi_static_chans=[1, 206, 997],
            rfi_dynamic_chans=[242, 1342],
            rfi_weighted=0.87,
        )
        timing_beams = TimingBeamConfiguration(beams=[beams])
        return CSPConfiguration(
            self.csp_scan_configure_schema,
            SubarrayConfiguration(self.csp_subarray_id),
            CommonConfiguration(self.config_id, spec.band, subarray_id),
            lowcbf=LowCBFConfiguration(stations, timing_beams),
        )

    @encoded
    def generate_low_csp_scan_config(
        self, target_id: str | None = None, subarray_id: int = 1
    ):
        return self._generate_low_csp_scan_config(target_id, subarray_id)
