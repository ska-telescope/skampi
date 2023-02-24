"""Domain logic for the sdp."""
import logging
from typing import Union, List, Any
import os
from time import sleep

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.utils.singleton import Memo
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    NoOpStep,
    MessageBoardBuilder,
)
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.event_handling.builders import get_message_board_builder

from resources.models.obsconfig import Observation
from resources.models.obsconfig.sdp_config import ProcessingSpec, VIS_RECEIVE_SCRIPT
from resources.models.obsconfig.target_spec import VIS_REC_SPEC

from ..obsconfig.channelisation import VIS_REC_CHANNELS
from ..obsconfig.config import Observation


logger = logging.getLogger(__name__)


class LogEnabled:
    """class that allows for logging if set by env var"""

    def __init__(self) -> None:
        self._live_logging = bool(os.getenv("DEBUG_ENTRYPOINT"))
        self._tel = names.TEL()

    def _log(self, mssage: str):
        # TODO: change back once things work
        #  this is needed to log the configuration string
        # if self._live_logging:
        logger.info(mssage)


class StartUpStep(base.ObservationStep, LogEnabled):
    """Implementation of Startup step for SDP"""

    def __init__(self, nr_of_subarrays: int) -> None:
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays
        self._sdp_master_name = self._tel.sdp.master

    def do(self):
        """Domain logic for starting up a telescope on the interface to SDP.

        This implments the set_telescope_to_running method on the entry_point.
        """
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.sdp.subarray(index)
            subarray = con_config.get_device_proxy(self._tel.sdp.subarray(index))
            self._log(f"commanding {subarray_name} to On")
            subarray.command_inout("On")
        self._log(f"commanding {self._sdp_master_name} to On")
        sdp_master = con_config.get_device_proxy(self._sdp_master_name)
        sdp_master.command_inout("On")

    def set_wait_for_do(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic specifying what needs to be waited for before startup of sdp is done."""
        brd = get_message_board_builder()

        brd.set_waiting_on(self._tel.sdp.master).for_attribute(
            "state"
        ).to_become_equal_to("ON")
        # subarrays
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.sdp.subarray(index)
            brd.set_waiting_on(subarray_name).for_attribute("state").to_become_equal_to(
                "ON", ignore_first=False
            )
        return brd

    def set_wait_for_doing(self) -> Union[MessageBoardBuilder, None]:
        """Not implemented."""
        raise NotImplementedError()

    def set_wait_for_undo(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic for what needs to be waited for switching the sdp off."""
        brd = get_message_board_builder()
        brd.set_waiting_on(self._tel.sdp.master).for_attribute(
            "state"
        ).to_become_equal_to("OFF", ignore_first=False)
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.sdp.subarray(index)
            brd.set_waiting_on(subarray_name).for_attribute("state").to_become_equal_to(
                "OFF", ignore_first=False
            )
        return brd

    def undo(self):
        """Domain logic for switching the sdp off."""
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.sdp.subarray(index)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"commanding {subarray_name} to Off")
            subarray.command_inout("Off")
        self._log(f"commanding {self._sdp_master_name} to Off")
        sdp_master = con_config.get_device_proxy(self._sdp_master_name)
        sdp_master.command_inout("Off")


class SdpAssignResourcesStep(base.AssignResourcesStep, LogEnabled):
    """Implementation of Assign Resources Step for SDP."""

    def __init__(self, observation: Observation) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()
        self.observation = observation

    def do(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        composition: types.Composition,  # pylint: disable=
        sb_id: str,
    ):
        """Domain logic for assigning resources to a subarray in sdp.

        This implements the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration paramaters
        :param sb_id: a generic id to identify a sb to assign resources
        """
        # currently ignore composition as all types will be standard
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        config = self.observation.generate_sdp_assign_resources_config().as_json
        self._log(f"commanding {subarray_name} with AssignResources: {config} ")
        subarray.command_inout("AssignResources", config)

    def undo(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in sdp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"Commanding {subarray_name} to ReleaseAllResources")
        subarray.command_inout("ReleaseAllResources")

    def set_wait_for_do(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        brd = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        brd.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "IDLE"
        )
        return brd

    def set_wait_for_doing(self, sub_array_id: int) -> MessageBoardBuilder:
        """Not implemented."""
        raise NotImplementedError()

    def set_wait_for_undo(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        brd = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        brd.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "EMPTY"
        )
        return brd


class SdpConfigureStep(base.ConfigureStep, LogEnabled):
    """Implementation of Configure Scan Step for SDP."""

    def __init__(self, observation: Observation) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()
        self.observation = observation

    def do(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        configuration: types.ScanConfiguration,
        sb_id: str,
        duration: float,
    ):
        """Domain logic for configuring a scan on subarray in sdp.

        This implments the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration paramaters
        :param sb_id: a generic ide to identify a sb to assign resources
        """
        # scan duration needs to be a memorised for future objects that mnay require it
        Memo(scan_duration=duration)
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        config = self.observation.generate_sdp_scan_config().as_json
        self._log(f"commanding {subarray_name} with Configure: {config} ")
        subarray.command_inout("Configure", config)

    def undo(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in sdp.

        This implments the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with End command")
        subarray.command_inout("End")

    def set_wait_for_do(
        self, sub_array_id: int, receptors: List[int]
    ) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for configuring a scan is done.

        :param sub_array_id: The index id of the subarray to control
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("READY")
        return builder

    def set_wait_for_doing(
        self, sub_array_id: int, receptors: List[int]
    ) -> MessageBoardBuilder:
        """Not implemented."""
        raise NotImplementedError()

    def set_wait_for_undo(
        self, sub_array_id: int, receptors: List[int]
    ) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray clear scan config is done.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")
        return builder


class SDPScanStep(base.ScanStep, LogEnabled):

    """Implementation of Scan Step for SDP."""

    def __init__(self, observation: Observation) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()
        self.observation = observation

    def do(self, sub_array_id: int):
        """Domain logic for running a scan on subarray in sdp.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        scan_config = self.observation.generate_sdp_run_scan().as_json
        scan_duration = Memo().get("scan_duration")
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"Commanding {subarray_name} to Scan with {scan_config}")
        try:
            subarray.command_inout("Scan", scan_config)
            sleep(scan_duration)
            subarray.command_inout("EndScan")
        except Exception as exception:
            logger.exception(exception)
            raise exception

    def set_wait_for_do(
        self, sub_array_id: int, receptors: List[int]
    ) -> Union[MessageBoardBuilder, None]:
        """This is a no-op as there is no scanning command

        :param sub_array_id: The index id of the subarray to control
        """

    def undo(self, sub_array_id: int):
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        """

    def set_wait_for_doing(
        self, sub_array_id: int, receptors: List[int]
    ) -> Union[MessageBoardBuilder, None]:
        """Domain logic specifyig what needs to be done for waiting for subarray to be scanning.

        :param sub_array_id: The index id of the subarray to control
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("SCANNING", ignore_first=True)
        return builder

    def set_wait_for_undo(
        self, sub_array_id: int, receptors: List[int]
    ) -> Union[MessageBoardBuilder, None]:
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        """
        return None


class VisRecObservation(Observation):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.target_specs = VIS_REC_SPEC
        self.channel_configurations = VIS_REC_CHANNELS
        self.processing_specs = {"vis-receive": ProcessingSpec(
            script=VIS_RECEIVE_SCRIPT,
            parameters={
                "image": "artefact.skao.int/ska-sdp-realtime-receive-modules",
                "version": "3.6.0",
                "plasmaEnabled": "true",
                "reception": {
                    "layout": "/mnt/data/low-layout.json",
                    "num_channels": 13824,
                    "channels_per_stream": 6912,
                    "continuous_mode": "true",
                    "transport_protocol": "tcp",
                    "payloads_in_flight": 3,
                    "disable_astropy_iers_autodownload": "true",
                },
                "pvc": {"name": "shared"},
                "plasma_parameters": {
                    "initContainers": [
                        {
                            "name": "existing-output-remover",
                            "image": "artefact.skao.int/ska-sdp-realtime-receive-processors:0.4.0",
                            "command": ["rm", "-rf", "/mnt/data/output*.ms"],
                            "volumeMounts": [
                                {"mountPath": "/mnt/data", "name": "shared"}
                            ],
                        },
                        {
                            "name": "start-telmodel",
                            "image": "python:3.10-slim",
                            "command": [
                                "/bin/bash",
                                "-c",
                                "pip install --extra-index-url=https://artefact.skao.int/repository/pypi-internal/simple ska-telmodel==1.4.1 pyyaml; rm -f /mnt/data/low-layout.json ; ska-telmodel cat instrument/ska1_low/layout/low-layout.json > /mnt/data/low-layout.json",
                            ],
                            "volumeMounts": [
                                {"mountPath": "/mnt/data", "name": "shared"}
                            ],
                        },
                    ],
                    "extraContainers": [
                        {
                            "name": "plasma-processor",
                            "image": "artefact.skao.int/ska-sdp-realtime-receive-processors:0.4.0",
                            "args": [
                                "--max-payloads",
                                "12",
                                "--readiness-file",
                                "/tmp/processor_ready",
                                "output.ms",
                            ],
                            "volumeMounts": [
                                {
                                    "name": "plasma-storage-volume",
                                    "mountPath": "/plasma",
                                },
                                {"mountPath": "/mnt/data", "name": "shared"},
                            ],
                            "readinessProbe": {
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5,
                                "exec": {"command": ["cat", "/tmp/processor_ready"]},
                            },
                        }
                    ],
                },
            },
        )}


class SDPEntryPoint(CompositeEntryPoint, LogEnabled):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2
    obs_to_use = None

    def __init__(self, observation: Observation | None = None) -> None:
        """Init Object"""
        super().__init__()
        if not self.obs_to_use:
            if not observation:
                self.obs_to_use = Observation()
            else:
                self.obs_to_use = observation
        self.observation = self.obs_to_use
        self.set_online_step = NoOpStep()
        self.start_up_step = StartUpStep(self.nr_of_subarrays)
        self.assign_resources_step = SdpAssignResourcesStep(self.observation)
        self.configure_scan_step = SdpConfigureStep(self.observation)
        self.scan_step = SDPScanStep(self.observation)
