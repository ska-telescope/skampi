from ska_tmc_cdm.messages.central_node.mccs import MCCSAllocate
from .base import encoded
from ska_tmc_cdm.messages.subarray_node.configure.mccs import (
    MCCSConfiguration,
    StnConfiguration,
    SubarrayBeamConfiguration,
    SubarrayBeamTarget,
)

from .target_spec import TargetSpecs

class MCCSConfig():
    def _generate_low_mccs_assign_resources_config(self):

        subarray_beam_ids = [1]
        station_ids = [[1, 2]]
        channel_blocks = [3]


        return MCCSAllocate(
            station_ids = station_ids,
        channel_blocks = channel_blocks,
        subarray_beam_ids = subarray_beam_ids,
        )

    @encoded
    def generate_low_mccs_assign_resources_config(self):
        return self._generate_low_mccs_assign_resources_config()

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