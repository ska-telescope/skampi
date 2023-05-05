from ska_tmc_cdm.messages.central_node.mccs import MCCSAllocate

from .base import encoded


class MCCSConfig:
    def _generate_low_mccs_assign_resources_config(self):
        subarray_beam_ids = [1]
        station_ids = [[1, 2]]
        channel_blocks = [3]

        return MCCSAllocate(
            station_ids=station_ids,
            channel_blocks=channel_blocks,
            subarray_beam_ids=subarray_beam_ids,
        )

    @encoded
    def generate_low_mccs_assign_resources_config(self):
        return self._generate_low_mccs_assign_resources_config()
