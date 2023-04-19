from typing import Any

from ska_tmc_cdm.messages.central_node.sdp import Channel, ChannelConfiguration

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
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._channel_configurations = DEFAULT_CHANNELS
        if additional_channels is not None:
            self._channel_configurations = {
                **self._channel_configurations,
                **{
                    additional_channel.channels_id: additional_channel
                    for additional_channel in additional_channels
                },
            }

    def add_channel_configuration(
        self, config_name: str, spectral_windows: list[Channel]
    ):
        assert (
            self._channel_configurations.get(config_name) is None
        ), f"configuration {config_name} already exists."
        self._channel_configurations[config_name] = ChannelConfiguration(
            channels_id=config_name, spectral_windows=spectral_windows
        )

    @property
    def channel_configurations(self) -> list[str]:
        return list(self._channel_configurations.keys())

    @channel_configurations.setter
    def channel_configurations(self, new_config):
        if not isinstance(new_config, dict):
            raise ValueError("Channel configuration needs to be a dictionary")
        self._channel_configurations = new_config

    def get_channel_configuration(
        self, config_name: str
    ) -> ChannelConfiguration:
        assert (
            self._channel_configurations.get(config_name) is not None
        ), f"configuration {config_name} does not exist."
        return self._channel_configurations[config_name]

    @property
    def target_spec_channels(self):
        return {target.channelisation for target in self.target_specs.values()}

    @property
    def channels(self) -> list[ChannelConfiguration]:
        unique_keys = self.target_spec_channels
        return [
            channel_config
            for channel_config in [
                self._channel_configurations.get(key) for key in unique_keys
            ]
            if channel_config
        ]
