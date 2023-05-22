"""Domain logic for the sdp."""
import logging
import os
from time import sleep
from typing import Any, List, cast

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import base

# pylint :disable=E0611
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    MessageBoardBuilder,
    NoOpStep,
)
from ska_ser_skallop.utils.singleton import Memo

from ..mvp_model.states import ObsState
from ..obsconfig.config import Observation

logger = logging.getLogger(__name__)


class LogEnabled:
    """class that allows for logging if set by env var"""

    def __init__(self) -> None:
        self._live_logging = bool(os.getenv("DEBUG_ENTRYPOINT"))
        self._tel = names.TEL()

    def _log(self, mssage: str):
        if self._live_logging:
            logger.info(mssage)


class StartUpStep(base.StartUpStep, LogEnabled):
    """Implementation of Startup step for SDP"""

    def __init__(self, nr_of_subarrays: int) -> None:
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays
        self._sdp_master_name = self._tel.sdp.master

    def do_startup(self):
        """Domain logic for starting up a telescope on the interface to SDP.

        This implments the set_telescope_to_running method on the entry_point.
        """
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.sdp.subarray(index)
            subarray = con_config.get_device_proxy(
                self._tel.sdp.subarray(index)
            )
            self._log(f"commanding {subarray_name} to On")
            subarray.command_inout("On")
        self._log(f"commanding {self._sdp_master_name} to On")
        sdp_master = con_config.get_device_proxy(self._sdp_master_name)
        sdp_master.command_inout("On")

    def set_wait_for_do_startup(self) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited
        for before startup of sdp is done.
        :return: brd
        """
        brd = get_message_board_builder()

        brd.set_waiting_on(self._tel.sdp.master).for_attribute(
            "state"
        ).to_become_equal_to("ON", ignore_first=False)
        # subarrays
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.sdp.subarray(index)
            brd.set_waiting_on(subarray_name).for_attribute(
                "state"
            ).to_become_equal_to("ON", ignore_first=False)
        return brd

    def set_wait_for_doing_startup(self) -> MessageBoardBuilder:
        """
        Not implemented.

        :raises NotImplementedError: Raises the error
                when implementation is not done.
        """
        raise NotImplementedError()

    def set_wait_for_undo_startup(self) -> MessageBoardBuilder:
        """
        Domain logic for what needs to be waited for switching the sdp off.

        :return: brd
        """
        brd = get_message_board_builder()
        brd.set_waiting_on(self._tel.sdp.master).for_attribute(
            "state"
        ).to_become_equal_to("OFF", ignore_first=False)
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.sdp.subarray(index)
            brd.set_waiting_on(subarray_name).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
        return brd

    def undo_startup(self):
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
        """
        Init object.

        :param observation: An instance of the Observation class or None.
            If None, a new instance of Observation will be created.
        """
        super().__init__()
        self._tel = names.TEL()
        self.observation = observation

    def do_assign_resources(
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
        config = (
            self.observation.generate_sdp_assign_resources_config().as_json
        )
        self._log(
            f"commanding {subarray_name} with AssignResources: {config} "
        )
        subarray.command_inout("AssignResources", config)

    def undo_assign_resources(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in sdp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"Commanding {subarray_name} to ReleaseAllResources")
        subarray.command_inout("ReleaseAllResources")

    def set_wait_for_do_assign_resources(
        self, sub_array_id: int
    ) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for
        subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
        """
        brd = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        brd.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")
        return brd

    def set_wait_for_doing_assign_resources(
        self, sub_array_id: int
    ) -> MessageBoardBuilder:
        """
        Domain logic specifyig what needs to be done for waiting
        for subarray to be scanning.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
        """
        brd = get_message_board_builder()
        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("RESOURCING")
        return brd

    def set_wait_for_undo_resources(
        self, sub_array_id: int
    ) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited
        for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
        """
        brd = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        brd.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "EMPTY", ignore_first=False
        )
        return brd


class SdpConfigureStep(base.ConfigureStep, LogEnabled):
    """Implementation of Configure Scan Step for SDP."""

    def __init__(self, observation: Observation) -> None:
        """
        Init object.
        :param observation: An instance of the Observation class or None.
            If None, a new instance of Observation will be created.

        """
        super().__init__()
        self._tel = names.TEL()
        self.observation = observation

    def do_configure(
        self,
        sub_array_id: int,
        configuration: types.ScanConfiguration,
        sb_id: str,
        duration: float,
    ):
        """Domain logic for configuring a scan on subarray in sdp.

        This implments the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param configuration: The assign resources configuration paramaters
        :param sb_id: a generic ide to identify a sb to assign resources
        :param duration: duration of scan
        """
        # scan duration needs to be a memorised for future
        # objects that mnay require it
        Memo(scan_duration=duration)
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        config = self.observation.generate_sdp_scan_config().as_json
        self._log(f"commanding {subarray_name} with Configure: {config} ")
        subarray.set_timeout_millis(6000)
        subarray.command_inout("Configure", config)

    def undo_configure(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in sdp.

        This implments the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with End command")
        subarray.command_inout("End")

    def set_wait_for_do_configure(
        self, sub_array_id: int
    ) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited
        for configuring a scan is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("READY")
        return builder

    def set_wait_for_doing_configure(
        self, sub_array_id: int
    ) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for
        a subarray to be in a state of configuring.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to(["CONFIGURING", "READY"])
        return builder

    def set_wait_for_undo_configure(
        self, sub_array_id: int
    ) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited
        for subarray clear scan config is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
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
        """
        Init object.

        :param observation: An instance of the Observation class or None.
            If None, a new instance of Observation will be created.
        """
        super().__init__()
        self._tel = names.TEL()
        self.observation = observation

    def do_scan(self, sub_array_id: int):
        """Domain logic for running a scan on subarray in sdp.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control

        :raises Exception: Raise exception in do method of scan command
        """
        scan_config = self.observation.generate_sdp_run_scan().as_json
        scan_duration = cast(float, Memo().get("scan_duration"))
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"Commanding {subarray_name} to Scan with {scan_config}")
        try:
            subarray.command_inout("Scan", scan_config)
            sleep(scan_duration)
            current_state = subarray.read_attribute("obsState")
            if current_state.value == ObsState.SCANNING:
                subarray.command_inout("EndScan")
        except Exception as exception:
            logger.exception(exception)
            raise exception

    def set_wait_for_do_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """This is a no-op as there is no scanning command

        :param sub_array_id: The index id of the subarray to control
        :return: message board_builder
        """
        return get_message_board_builder()

    def undo_scan(self, sub_array_id: int):
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        """

    def set_wait_for_doing_scan(
        self, sub_array_id: int
    ) -> MessageBoardBuilder:
        """
        Domain logic specifyig what needs to be done for waiting
        for subarray to be scanning.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)

        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("SCANNING", ignore_first=True)
        return builder

    def set_wait_for_undo_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        :return: message board builder
        """
        return get_message_board_builder()


class SDPAbortStep(base.AbortStep, LogEnabled):

    """Implementation of Abort Step for SDP."""

    def do_abort(self, sub_array_id: int):
        """Domain logic for running a abort on subarray in sdp.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with Abort command")
        subarray.command_inout("Abort")

    def set_wait_for_do_abort(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for abort is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("ABORTED", ignore_first=True)
        return builder


class SDPObsResetStep(base.ObsResetStep, LogEnabled):

    """Implementation of ObsReset Step for SDP."""

    def set_wait_for_do_obsreset(
        self, sub_array_id: int
    ) -> MessageBoardBuilder:
        """Domain logic for running a obsreset on subarray in sdp.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE", ignore_first=True)
        return builder

    def do_obsreset(self, sub_array_id: int):
        """
        Domain logic specifying what needs to be waited for obsreset is done.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with ObsReset command")
        subarray.command_inout("Obsreset")

    def undo_obs_reset(self, sub_array_id: int):
        """
        Domain logic for releasing resources on a subarray in sdp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"Commanding {subarray_name} to ReleaseAllResources")
        subarray.command_inout("ReleaseAllResources")

    def set_wait_for_undo_obsreset(
        self, sub_array_id: int
    ) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited
        for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
        """
        brd = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        brd.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("EMPTY")
        return brd


class SDPRestart(base.RestartStep, LogEnabled):
    def do_restart(self, sub_array_id: int):
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with Restart command")
        subarray.command_inout("Restart")

    def set_wait_for_do_restart(
        self, sub_array_id: int, _: Any = None
    ) -> MessageBoardBuilder:
        builder = get_message_board_builder()
        subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("EMPTY", ignore_first=True)
        return builder


class SDPEntryPoint(CompositeEntryPoint, LogEnabled):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2
    obs_to_use = None

    def __init__(self, observation: Observation | None = None) -> None:
        """
        Init Object

        :param observation: An instance of the Observation class or None.
            If None, a new instance of Observation will be created.
        """
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
        self.abort_step = SDPAbortStep()
        self.obsreset_step = SDPObsResetStep()
        self.restart_step = SDPRestart()
