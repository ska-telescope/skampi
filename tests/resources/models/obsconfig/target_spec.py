from collections import OrderedDict


from ska_tmc_cdm.messages.subarray_node.configure.core import ReceiverBand, Target

from .base import SchedulingBlock


class BaseTargetSpec():

    def __init__(
        self, target: Target,
        scan_type: str,
        band: ReceiverBand,
        channelisation: str,
        polarisation: str,
        field: str,
        processing: str,
    ) -> None:
        self.target = target
        self.scan_type = scan_type
        self.band = band
        self.channelisation = channelisation
        self.polarisation = polarisation
        self.field = field
        self.processing = processing


class TargetSpec(BaseTargetSpec):


    def __init__(
        self, target: Target,
        scan_type: str,
        band: ReceiverBand,
        channelisation: str,
        polarisation: str,
        field: str,
        processing: str,
        dishes: str | list[str],
    ) -> None:
        super().__init__(target, scan_type, band, channelisation, polarisation, field, processing)
        self.dishes = dishes

def upgrade_base_target_spec(base_target_spec: BaseTargetSpec, dishes: str | list[str]) ->TargetSpec:
    return TargetSpec(
        base_target_spec.target,
        base_target_spec.scan_type,
        base_target_spec.band,
        base_target_spec.channelisation,
        base_target_spec.polarisation,
        base_target_spec.field,
        base_target_spec.processing,
        dishes,
    )


DEFAULT_TARGET_SPECS = OrderedDict(
    {
        "target:a": BaseTargetSpec(
            Target("12:29:06.699 degrees", "02:03:08.598 degrees"),
            "target:a",
            ReceiverBand.BAND_2,
            "vis_channels",
            "all",
            "field_a",
            "test-receive-addresses",
        ),
        ".default": BaseTargetSpec(
            Target("12:29:06.699 degrees", "02:03:08.598 degrees"),
            ".default",
            ReceiverBand.BAND_2,
            "vis_channels",
            "all",
            "field_a",
            "test-receive-addresses",
        ),
    }
)

class ArraySpec:

    def __init__(self, receptors: str | list[str]) -> None:
        self.receptors = receptors

DEFAULT_ARRAY_SPEC = ArraySpec(receptors="two")

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
    _target_spec_initialized = False

    def __init__(self, base_target_specs: dict[str, BaseTargetSpec] | None = None, array: ArraySpec | None = None) -> None:
        if not self._target_spec_initialized:
            self._target_spec_initialized = True
            SchedulingBlock.__init__(self)
            Scan.__init__(self)
            self._init_scan()
            if array:
                self._array = array
            else:
                self._array = DEFAULT_ARRAY_SPEC

            if base_target_specs:
                self._base_target_specs = base_target_specs
            else:
                self._base_target_specs = DEFAULT_TARGET_SPECS
            self._next_index = 0
        if array:
            self._array = array
        if base_target_specs:
            self._base_target_specs = base_target_specs


    @property
    def target_specs(self) -> dict[str, TargetSpec]:
        return { key: upgrade_base_target_spec(spec,self._array.receptors) for key, spec in self._base_target_specs.items()}


    def add_target_specs(self, base_target_specs: dict[str, BaseTargetSpec]):
        self._target_specs = OrderedDict({**self.target_specs, **base_target_specs})

    def get_target_spec(self, target_id: str | None = None):
        if target_id is not None:
            return self.target_specs[target_id]
        return list(self.target_specs.values())[0]

    @property
    def next_target_id(self) -> str:
        return list(self.target_specs.keys())[self._next_index]
    
    @property
    def next_target(self) -> TargetSpec:
        key = list(self.target_specs.keys())[self._next_index]
        return self.target_specs[key]
    

    def update_target_specs(
        self,
        target: Target | None = None,
        scan_type: str | None = None,
        band: ReceiverBand | None = None,
        channelisation: str | None = None,
        polarisation: str | None = None,
        field: str | None = None,
        processing: str | None = None,
        dishes: str | list[str] | None = None
    ):
        for key in self._base_target_specs.keys():
            if band:
                self._base_target_specs[key].band = band
            if target:
                self._base_target_specs[key].target = target
            if scan_type:
                self._base_target_specs[key].scan_type = scan_type
            if channelisation:
                self._base_target_specs[key].channelisation = channelisation
            if polarisation:
                self._base_target_specs[key].polarisation = polarisation
            if processing:
                self._base_target_specs[key].processing = processing
            if field:
                self._base_target_specs[key].field = field
        if dishes:
            self._array.receptors = dishes
            
    
