from typing import Any, NamedTuple, cast
from ska_tmc_cdm.messages.central_node.sdp import (
    BeamConfiguration,
    EBScanTypeBeam,
    EBScanType,
    PolarisationConfiguration,
    FieldConfiguration,
    PhaseDir,
    ScriptConfiguration,
    ProcessingBlockConfiguration,
    ChannelConfiguration,
    ExecutionBlockConfiguration,
    SDPConfiguration,
)
from ska_tmc_cdm.messages.subarray_node.configure import (
    SDPConfiguration as SDPScanConfiguration,
)
from .target_spec import TargetSpecs
from .base import encoded
from .channelisation import Channelization
from .dishes import Dishes


class Beamgrouping(NamedTuple):
    id: str
    configuration: BeamConfiguration
    types: dict[str, EBScanTypeBeam]


DEFAULT_FIELDS = {
    "field_a": FieldConfiguration(
        field_id="field_a",
        pointing_fqdn="...",
        phase_dir=PhaseDir(
            ra=[123.0],
            dec=[-60.0],
            reference_time="...",
            reference_frame="ICRF3",
        ),
    )
}

DEFAULT_POLARISATIONS = {
    "all": PolarisationConfiguration(
        polarisations_id="all", corr_type=["XX", "XY", "YY", "YX"]
    )
}

DEFAULT_BEAMS = {
    "vis0": Beamgrouping(
        "vis0",
        BeamConfiguration(beam_id="vis0", function="visibilities"),
        {
            "default_beam_type": EBScanTypeBeam(
                channels_id="vis_channels", polarisations_id="all"
            ),
            "field_a_beam_type": EBScanTypeBeam(field_id="field_a"),
        },
    ),
}


def DEFAULT_SCAN_TYPES(owner: "ScanTypes"):
    return {
        ".default": EBScanType(
            scan_type_id=".default",
            beams={"vis0": owner.beams["vis0"].types["default_beam_type"]},
        ),
        "target:a": EBScanType(
            scan_type_id="target:a",
            beams={"vis0": owner.beams["vis0"].types["field_a_beam_type"]},
            derive_from=".default",
        ),
    }


class ScanTypes(TargetSpecs):
    def __init__(
        self,
        additional_beam_groupings: list[Beamgrouping] | None = None,
        additional_scan_types: list[EBScanType] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.beams = DEFAULT_BEAMS
        self.scan_types = DEFAULT_SCAN_TYPES(self)

        if additional_beam_groupings is not None:
            self.beams = {
                **self.beams,
                **{
                    beam_grouping.id: beam_grouping
                    for beam_grouping in additional_beam_groupings
                },
            }
        if additional_scan_types is not None:
            self.additional_scan_types = {
                **self.additional_scan_types,
                **{
                    additional_scan_type.scan_type_id: additional_scan_type
                    for additional_scan_type in additional_scan_types
                },
            }

    def _get_beam_configurations_from_scantypes(self, scantypes: list[EBScanType]):
        unique_keys = {key for scantype in scantypes for key in scantype.beams.keys()}
        return [self.beams[cast(str, key)].configuration for key in unique_keys]

    def get_scan_types_from_target_specs(self):
        unique_keys = {target.scan_type for target in self.target_specs.values()}
        return [self.scan_types[key] for key in unique_keys]


class Polarisations(TargetSpecs):
    def __init__(
        self,
        additional_polarizations: list[PolarisationConfiguration] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.polarizations = DEFAULT_POLARISATIONS
        if additional_polarizations is not None:
            self.polarizations = {
                **self.polarizations,
                **{
                    additional_polarization.polarisations_id: additional_polarization
                    for additional_polarization in additional_polarizations
                },
            }

    def get_polarisations_from_target_specs(self):
        unique_keys = {target.polarisation for target in self.target_specs.values()}
        return [self.polarizations[key] for key in unique_keys]


class Fields(TargetSpecs):
    def __init__(
        self,
        additional_field_configurations: list[FieldConfiguration] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if additional_field_configurations is None:
            self.fields = DEFAULT_FIELDS

    def get_fields_from_target_specs(self):
        unique_keys = {target.field for target in self.target_specs.values()}
        return [self.fields[key] for key in unique_keys]


class ProcessingSpec(NamedTuple):
    script: ScriptConfiguration
    parameters: dict[Any, Any] = {}

    def __hash__(self):
        return hash(f"{self.script.name}")


DEFAULT_SCRIPT = ScriptConfiguration(
    kind="realtime", name="test-receive-addresses", version="0.5.0"
)


class ProcessingSpecs(TargetSpecs):
    def __init__(
        self,
        additional_processing_specs: list[ProcessingSpec] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.processing_specs = {
            "test-receive-addresses": ProcessingSpec(script=DEFAULT_SCRIPT)
        }
        if additional_processing_specs is not None:
            self.processing_specs = {
                **self.processing_specs,
                **{
                    processing_spec.script.name: processing_spec
                    for processing_spec in additional_processing_specs
                },
            }

    def get_processing_script_from_target_spec(self):
        unique_keys = {target.processing for target in self.target_specs.values()}
        return [self.processing_specs[key] for key in unique_keys]


class ProcessingBlockSpec(ProcessingSpecs):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(args, **kwargs)

    @property
    def processing_blocks(self):
        processing_specs = self.get_processing_script_from_target_spec()
        return [
            ProcessingBlockConfiguration(
                pb_id=self.pb_id,
                script=processing_spec.script,
                sbi_ids=["sbi-test-20220916-00000"],
                parameters=processing_spec.parameters,
            )
            for processing_spec in processing_specs
        ]


class ExecutionBlockSpecs(ScanTypes, Channelization, Polarisations, Fields):
    def __init__(
        self,
        context: dict[Any, Any] | None = None,
        max_length: float = 100.0,
        target_specs: dict[Any, Any] | None = None,
        additional_scan_types: list[EBScanType] | None = None,
        additional_channels: dict[str, ChannelConfiguration] | None = None,
        additional_polarizations: dict[str, PolarisationConfiguration] | None = None,
        additional_field_configurations: list[FieldConfiguration] | None = None,
    ) -> None:
        super().__init__(
            target_specs=target_specs,
            additional_scan_types=additional_scan_types,
            additional_channels=additional_channels,
            additional_polarizations=additional_polarizations,
            additional_field_configurations=additional_field_configurations,
        )
        if context is None:
            context = {}
        self._context = context
        self._max_length = max_length

    @property
    def execution_block(self):
        context = self._context
        max_length = self._max_length
        scan_types = self.get_scan_types_from_target_specs()
        beams = self._get_beam_configurations_from_scantypes(scan_types)
        channels = self.get_channelisation_from_target_specs()
        polarisations = self.get_polarisations_from_target_specs()
        fields = self.get_fields_from_target_specs()
        return ExecutionBlockConfiguration(
            eb_id=self.eb_id,
            context=context,
            max_length=max_length,
            beams=beams,
            scan_types=scan_types,
            channels=channels,
            polarisations=polarisations,
            fields=fields,
        )


class SdpConfig(Dishes, ExecutionBlockSpecs, ProcessingBlockSpec):
    sdp_assign_resources_schema = "https://schema.skao.int/ska-sdp-assignres/0.4"
    sdp_configure_scan_schema = "https://schema.skao.int/ska-sdp-configure/0.3"

    def _generate_sdp_assign_resources_config(self):
        return SDPConfiguration(
            interface=self.sdp_assign_resources_schema,
            resources=self.get_dish_resource_allocation_from_target_spec(),
            execution_block=self.execution_block,
            processing_blocks=self.processing_blocks,
        )

    def _generate_sdp_scan_config(self, target_id: str | None = None):
        if target_id:
            assert self.target_specs[target_id], "unknown target id specified"
        else:
            target_id = list(self.target_specs.keys())[0]
        return SDPScanConfiguration(
            interface=self.sdp_configure_scan_schema, scan_type=target_id
        )

    def _generate_sdp_run_scan(self):
        return self.get_scan_id(backwards=True)

    @encoded
    def generate_sdp_run_scan(self):
        return self._generate_sdp_run_scan()

    @encoded
    def generate_sdp_scan_config(self, target_id: str | None = None):
        return self._generate_sdp_scan_config(target_id)

    @encoded
    def generate_sdp_assign_resources_config(self):
        return self._generate_sdp_assign_resources_config()
