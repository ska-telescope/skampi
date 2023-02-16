from ska_tmc_cdm.messages.subarray_node.configure.mccs import (
    MCCSConfiguration,
    StnConfiguration,
    SubarrayBeamConfiguration,
    SubarrayBeamTarget,
)

from .base import encoded
from .target_spec import TargetSpecs


class MCCSConfig(TargetSpecs):
    def _generate_mccs_scan_config(self):
        station_configs = [StnConfiguration(station_id=1), StnConfiguration(station_id=2)]
        target = SubarrayBeamTarget(
            reference_frame="HORIZON", target_name="DriftScan", az=180.0, el=45.0
        )
        subarray_beam_configs = [
            SubarrayBeamConfiguration(
                subarray_beam_id=1,
                station_ids=[1, 2],
                channels=[[0, 8, 1, 1], [8, 8, 2, 1], [24, 16, 2, 1]],
                update_rate=0.0,
                target=target,
                antenna_weights=[1.0, 1.0, 1.0],
                phase_centre=[0.0, 0.0],
            )
        ]
        return MCCSConfiguration(
            station_configs=station_configs, subarray_beam_configs=subarray_beam_configs
        )

    @encoded
    def generate_mccs_scan_config(self):
        return self._generate_mccs_scan_config()
