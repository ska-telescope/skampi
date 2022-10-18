from datetime import timedelta, datetime
from typing import Any, Literal
from collections import OrderedDict
import json
from typing import NamedTuple
from astropy import units as u

from ska_tmc_cdm.messages.subarray_node.configure.core import ReceiverBand
from ska_tmc_cdm.messages.central_node.assign_resources import (
    AssignResourcesRequest,
    DishAllocation,
)
from ska_tmc_cdm.messages.central_node.sdp import (
    ScanType,
    Channel,
    ProcessingBlockConfiguration,
    SDPConfiguration,
    SDPWorkflow,
)
from ska_tmc_cdm.messages.subarray_node.configure import (
    ConfigureRequest,
    PointingConfiguration,
    DishConfiguration,
    SDPConfiguration as SDPScanConfiguration,
    TMCConfiguration,
)
from ska_tmc_cdm.messages.central_node.sdp import ScanType
from ska_tmc_cdm.messages.subarray_node.configure.core import Target, ReceiverBand
from ska_tmc_cdm.messages.subarray_node.configure.csp import (
    CSPConfiguration,
    FSPConfiguration,
    FSPFunctionMode,
    CBFConfiguration,
    SubarrayConfiguration,
    CommonConfiguration,
)
from ska_tmc_cdm.schemas import CODEC

from .channeling import generate_channel_map


class SB(NamedTuple):
    eb: str
    pb: str


def load_nex_sb():
    date = datetime.now()
    unique = f"{date.year}{date.month}{date.day}-{str(int(date.timestamp()))[5:]}"
    pb = f"pb-mvp01-{unique}"
    eb = f"eb-mvp01-{unique}"
    return SB(eb, pb)


DishID = Literal[
    "0001",
    "0002",
    "0003",
    "0004",
    "0005",
    "0006",
    "0008",
    "0009",
    "0010",
    "0011",
    "0012",
]


def generate_scan_type(
    scan_type_id: str,
    target: Target,
    channels: list[Channel],
    reference_frame: str = "ICRS",
):
    return ScanType(
        **{
            "ra": target.coord.ra.to_string(unit=u.degree, sep=":"),  # type: ignore
            "dec": target.coord.dec.to_string(unit=u.degree, sep=":"),  # type: ignore
            "scan_type_id": scan_type_id,
            "reference_frame": reference_frame,
            "channels": channels,
        }
    )


class ObservationSpec(NamedTuple):
    target: Target
    scan_type_id: str
    band: ReceiverBand


class ProcessingSpec(NamedTuple):
    workflow: SDPWorkflow
    parameters: dict[Any, Any] = dict()


class Scan:
    def __init__(self, band: ReceiverBand, target: Target) -> None:
        self.band = band
        self.target = target
        self._instance_count = 0

    def _inc(self):
        self._instance_count += 1

    def get_scan_id(self):
        self._inc()
        return {"scan_id": self._instance_count}


class Observation:

    assign_resources_schema = "https://schema.skao.int/ska-tmc-assignresources/2.0"
    sdp_assign_resources_schema = "https://schema.skao.int/ska-sdp-assignres/0.4"
    sdp_configure_scan_schema = "https://schema.skao.int/ska-sdp-configure/0.3"
    csp_scan_configure_schema = "https://schema.skao.int/ska-csp-configure/2.0"
    csp_subarray_id = "science period 23"

    def __init__(
        self,
        subarray_id: int = 1,
        dishes: list[DishID] | None = None,
        target_specs: list[ObservationSpec] | None = None,
        processing_specs: list[ProcessingSpec] | None = None,
    ) -> None:
        if not dishes:
            dishes = ["0001", "0002"]
        self._dishes = dishes
        self._dish_allocation = DishAllocation(self._dishes)
        if not target_specs:
            target_specs = [
                ObservationSpec(
                    Target("02:42:40.771 degrees", "-00:00:47.84 degrees"),
                    "science_A",
                    ReceiverBand.BAND_2,
                ),
                ObservationSpec(
                    Target("12:29:06.699 degrees", "02:03:08.598 degrees"),
                    "calibration_B",
                    ReceiverBand.BAND_2,
                ),
            ]
        if not processing_specs:
            processing_specs = [
                ProcessingSpec(
                    SDPWorkflow(
                        kind="realtime", name="test_receive_addresses", version="0.3.6"
                    )
                )
            ]
        eb_id, pb_id = load_nex_sb()
        self._eb_id = eb_id
        self._pb_id = pb_id
        self._subarray_id = subarray_id
        self._processing_blocks = [
            ProcessingBlockConfiguration(
                pb_id=pb_id,
                workflow=processing_spec.workflow,
                parameters=processing_spec.parameters,
            )
            for processing_spec in processing_specs
        ]
        # NB this is dummy code and needs to be updates
        channel_map = generate_channel_map(ReceiverBand.BAND_2)
        channels = [Channel(**channel) for channel in channel_map["channels"]]
        self._scan_types = [
            generate_scan_type(target_spec.scan_type_id, target_spec.target, channels)
            for target_spec in target_specs
        ]

        self._target_specs = OrderedDict(
            {
                target_spec.scan_type_id: Scan(target_spec.band, target_spec.target)
                for target_spec in target_specs
            }
        )
        self._next_scan: Scan | None = None

    def generate_sdp_assign_resources_config(
        self, max_length: float = 100.0
    ) -> SDPConfiguration:
        return SDPConfiguration(
            interface=self.sdp_assign_resources_schema,
            max_length=max_length,
            eb_id=self._eb_id,
            processing_blocks=self._processing_blocks,
            scan_types=self._scan_types,
        )

    def generate_sdp_assign_resources_config_as_json(
        self, max_length: float = 100.0
    ) -> str:
        return CODEC.dumps(self.generate_sdp_assign_resources_config(max_length))

    def generate_sdp_assign_resources_config_as_dict(
        self, max_length: float = 100.0
    ) -> dict[str, Any]:
        return json.loads(self.generate_sdp_assign_resources_config_as_json(max_length))

    def generate_assign_resources_config(self):
        assign_request = AssignResourcesRequest()
        assign_request.interface = self.assign_resources_schema
        assign_request.subarray_id = self._subarray_id
        assign_request.dish = self._dish_allocation
        assign_request.sdp_config = self.generate_sdp_assign_resources_config()
        return assign_request

    def generate_assign_resources_config_as_json(self) -> str:
        return CODEC.dumps(self.generate_assign_resources_config())

    def generate_assign_resources_config_as_dict(self) -> dict[str, Any]:
        return json.loads(self.generate_assign_resources_config_as_json())

    def generate_sdp_scan_config(self, target_id: str | None):
        if target_id:
            assert self._target_specs[target_id], "unknown target id specified"
        else:
            target_id = list(self._target_specs.keys())[0]
        return SDPScanConfiguration(
            interface=self.sdp_configure_scan_schema, scan_type=target_id
        )

    def generate_sdp_scan_config_as_json(self, target_id: str | None) -> str:
        return CODEC.dumps(self.generate_sdp_scan_config(target_id))

    def generate_sdp_scan_config_as_dict(self, target_id: str | None) -> str:
        return json.loads(self.generate_sdp_scan_config_as_json(target_id))

    def generate_csp_scan_config(
        self,
        mode: FSPFunctionMode = FSPFunctionMode.CORR,
        fsps: list[int] | None = None,
        target_id: str | None = None,
    ):
        # TODO update fsps to be derived instead of hard coded
        if target_id:
            scan = self._target_specs[target_id]
        else:
            target_id, scan = list(self._target_specs.items())[0]
        if not fsps:
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
            CommonConfiguration(self._eb_id, scan.band, self._subarray_id),
            CBFConfiguration([fsp1, fsp2]),
        )

    def generate_csp_scan_config_as_json(
        self,
        mode: FSPFunctionMode = FSPFunctionMode.CORR,
        fsps: list[int] | None = None,
        target_id: str | None = None,
    ) -> str:
        return CODEC.dumps(self.generate_csp_scan_config(mode, fsps, target_id))

    def generate_csp_scan_config_as_dict(
        self,
        mode: FSPFunctionMode = FSPFunctionMode.CORR,
        fsps: list[int] | None = None,
        target_id: str | None = None,
    ):
        return json.loads(self.generate_csp_scan_config_as_json(mode, fsps, target_id))

    def generate_scan_config(
        self,
        mode: FSPFunctionMode = FSPFunctionMode.CORR,
        fsps: list[int] | None = None,
        target_id: str | None = None,
        scan_duration: float = 6,
    ):
        if not fsps:
            fsps = [1, 2]
        if target_id:
            scan = self._target_specs[target_id]
        else:
            target_id, scan = list(self._target_specs.items())[0]

        pointing = PointingConfiguration(scan.target)
        sdp_scan_config = self.generate_sdp_scan_config(target_id)
        dish_configuration = DishConfiguration(scan.band)
        csp_configuration = self.generate_csp_scan_config(mode, fsps, target_id)
        tm_config = TMCConfiguration(timedelta(seconds=scan_duration))
        return ConfigureRequest(
            pointing,
            dish_configuration,
            sdp_scan_config,
            csp_configuration,
            tmc=tm_config,
        )

    def generate_scan_config_as_json(
        self,
        mode: FSPFunctionMode = FSPFunctionMode.CORR,
        fsps: list[int] | None = None,
        target_id: str | None = None,
        scan_duration: float = 6,
    ) -> str:
        return CODEC.dumps(
            self.generate_scan_config(mode, fsps, target_id, scan_duration)
        )

    def generate_scan_config_as_dict(
        self,
        mode: FSPFunctionMode = FSPFunctionMode.CORR,
        fsps: list[int] | None = None,
        target_id: str | None = None,
        scan_duration: float = 6,
    ) -> dict[Any, Any]:
        return json.loads(
            self.generate_scan_config_as_json(mode, fsps, target_id, scan_duration)
        )
