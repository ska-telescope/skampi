from typing import Any
from ska_tmc_cdm.messages.central_node.sdp import ChannelConfiguration, Channel
from .target_spec import TargetSpecs

DEFAULT_CHANNELS = {
    "vis_channels": ChannelConfiguration(
        channels_id="vis_channels",
        spectral_windows=[
            Channel(
                spectral_window_id="fsp_1_channels",
                count=4,
                start=0,
                stride=2,
                freq_min=0.35e9,
                freq_max=0.368e9,
                link_map=[[0, 0], [200, 1], [744, 2], [944, 3]],
            )
        ],
    )
}


class Channelization(TargetSpecs):
    def __init__(
        self,
        additional_channels: list[ChannelConfiguration] | None = None,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.channels = DEFAULT_CHANNELS
        if additional_channels is not None:
            self.channels = {
                **self.channels,
                **{
                    additional_channel.channels_id: additional_channel
                    for additional_channel in additional_channels
                },
            }

    def get_channelisation_from_target_specs(self):
        unique_keys = {target.channelisation for target in self.target_specs.values()}
        return [self.channels[key] for key in unique_keys]
