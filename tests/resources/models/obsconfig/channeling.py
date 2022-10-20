from typing import NamedTuple, Tuple, TypedDict
from ska_tmc_cdm.messages.subarray_node.configure.core import ReceiverBand


class Link(NamedTuple):
    start: int
    index_nr: int


class Channel(TypedDict):
    count: int
    start: int
    stride: int
    freq_min: float
    freq_max: float
    link_map: list[Tuple[int, int]]


class ChannelMap(TypedDict):
    channels: list[Channel]


def generate_channel_map(band: ReceiverBand) -> ChannelMap:
    linkmapping = [
        Link(0, 0),
        Link(200, 1),
        Link(744, 2),
        Link(944, 3),
        Link(2000, 4),
        Link(2200, 5),
    ]
    linkmapping = [tuple([link.start, link.index_nr]) for link in linkmapping]
    channel1 = Channel(
        count=744,
        start=0,
        stride=2,
        freq_min=350000000.0,
        freq_max=368000000.0,
        link_map=linkmapping[:4],
    )
    channel2 = Channel(
        count=744,
        start=2000,
        stride=1,
        freq_min=360000000.0,
        freq_max=368000000.0,
        link_map=linkmapping[4:],
    )
    return ChannelMap(channels=[channel1, channel2])
