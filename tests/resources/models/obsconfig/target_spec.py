from collections import OrderedDict
from typing import NamedTuple

from ska_tmc_cdm.messages.subarray_node.configure.core import ReceiverBand, Target

from .base import SchedulingBlock


class TargetSpec(NamedTuple):
    target: Target
    scan_type: str
    band: ReceiverBand
    channelisation: str
    polarisation: str
    field: str
    processing: str
    dishes: str


DEFAULT_TARGET_SPECS = OrderedDict(
    {
        "target:a": TargetSpec(
            Target("12:29:06.699 degrees", "02:03:08.598 degrees"),
            "target:a",
            ReceiverBand.BAND_2,
            "vis_channels",
            "all",
            "field_a",
            "test-receive-addresses",
            "two",
        ),
        ".default": TargetSpec(
            Target("12:29:06.699 degrees", "02:03:08.598 degrees"),
            ".default",
            ReceiverBand.BAND_2,
            "vis_channels",
            "all",
            "field_a",
            "test-receive-addresses",
            "two",
        ),
    }
)


class Scan:
    def __init__(self) -> None:
        self._instance_count = 0

    def _init_scan(self):
        self._instance_count = 0

    def _inc(self):
        self._instance_count += 1

    def get_scan_id(self, backwards: bool = False):
        self._inc()
        if backwards:
            return {"id": self._instance_count}
        return {
            "interface": "https://schema.skao.int/ska-tmc-scan/2.0",
            "scan_id": self._instance_count,
        }


class TargetSpecs(SchedulingBlock, Scan):
    def __init__(self, target_specs: dict[str, TargetSpec] | None = None) -> None:
        super().__init__()
        self._init_scan()
        self.target_specs = DEFAULT_TARGET_SPECS

        if target_specs is not None:
            self.add_target_specs(target_specs)

    def add_target_specs(self, target_specs: dict[str, TargetSpec]):
        self.target_specs = {**self.target_specs, **target_specs}

    def get_target_spec(self, target_id: str | None = None):
        if target_id is not None:
            return self.target_specs[target_id]
        return list(self.target_specs.values())[0]

    @property
    def next_target_id(self) -> str:
        return list(self.target_specs.keys())[0]
