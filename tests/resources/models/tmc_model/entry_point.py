"""Domain logic for the tmc."""
import logging
from typing import Union, List
import os
import json
from time import sleep

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.utils.singleton import Memo
from ska_ser_skallop.mvp_control.configuration import composition as comp
from ska_ser_skallop.mvp_control.configuration import configuration as conf
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    NoOpStep,
    MessageBoardBuilder,
)
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.event_handling.builders import get_message_board_builder


logger = logging.getLogger(__name__)


class LogEnabled:
    """class that allows for logging if set by env var"""

    def __init__(self) -> None:
        self._live_logging = bool(os.getenv("DEBUG"))
        self._tel = names.TEL()

    def _log(self, mssage: str):
        if self._live_logging:
            logger.info(mssage)


# TODO implement start up
class StartUpStep(base.ObservationStep, LogEnabled):
    """Implementation of Startup step for SDP"""

    def __init__(self, nr_of_subarrays: int) -> None:
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays

    def do(self):
        """Domain logic for starting up a telescope on the interface to TMC.

        This implements the set_telescope_to_running method on the entry_point.
        """
        raise NotImplementedError()

    def set_wait_for_do(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic specifying what needs to be waited for before startup of telescope is done."""
        brd = get_message_board_builder()
        # TODO set what needs to be waited before start up completes
        return brd

    def set_wait_for_doing(self) -> Union[MessageBoardBuilder, None]:
        """Not implemented."""
        raise NotImplementedError()

    def set_wait_for_undo(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic for what needs to be waited for switching the telescope off."""
        brd = get_message_board_builder()
        # TODO set what needs to be waited before start up completes
        return brd

    def undo(self):
        """Domain logic for switching the telescope off using tmc."""


class AssignResourcesStep(base.AssignResourcesStep, LogEnabled):
    """Implementation of Assign Resources Step."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()

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
        subarray_name = self._tel.tm.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        standard_composition = comp.generate_standard_comp(
            sub_array_id, dish_ids, sb_id
        )
        tmc_standard_composition = json.dumps(json.loads(standard_composition)["sdp"])
        self._log(
            f"commanding {subarray_name} with AssignResources: {tmc_standard_composition} "
        )
        # TODO verify command correctness
        subarray.command_inout("AssignResources", tmc_standard_composition)

    def undo(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in sdp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.tm.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"Commanding {subarray_name} to ReleaseResources")
        # TODO verify command correctness
        subarray.command_inout("ReleaseResources")

    def set_wait_for_do(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        brd = get_message_board_builder()
        # TODO determine what needs to be waited for
        return brd

    def set_wait_for_doing(self, sub_array_id: int) -> MessageBoardBuilder:
        """Not implemented."""
        raise NotImplementedError()

    def set_wait_for_undo(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        brd = get_message_board_builder()
        # TODO determine what needs to be waited for
        return brd


class ConfigureStep(base.ConfigureStep, LogEnabled):
    """Implementation of Configure Scan Step for SDP."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()

    def do(
        self,
        sub_array_id: int,
        dish_ids: List[int],
        configuration: types.ScanConfiguration,
        sb_id: str,
        duration: float,
    ):
        """Domain logic for configuring a scan on subarray in sdp.

        This implements the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration paramaters
        :param sb_id: a generic ide to identify a sb to assign resources
        """
        # scan duration needs to be a memorized for future objects that may require it
        # Memo(scan_duration=duration)
        # subarray_name = self._tel.tm.subarray(sub_array_id)
        # subarray = con_config.get_device_proxy(subarray_name)
        # standard_configuration = conf.generate_standard_conf(
        #     sub_array_id, sb_id, duration
        # )
        # tmc_standard_configuration = json.dumps(
        #     json.loads(standard_configuration)["sdp"]
        # )
        # self._log(
        #     f"commanding {subarray_name} with Configure: {tmc_standard_configuration} "
        # )
        # TODO determine correct  command
        #  subarray.command_inout("Configure", tmc_standard_configuration)
        raise NotImplementedError()

    def undo(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in sdp.

        This implments the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        # subarray_name = self._tel.tm.subarray(sub_array_id)
        # subarray = con_config.get_device_proxy(subarray_name)
        # self._log(f"commanding {subarray_name} with End command")
        # TODO determine correct  command
        # subarray.command_inout("End")
        raise NotImplementedError()

    def set_wait_for_do(
        self, sub_array_id: int, receptors: List[int]
    ) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for configuring a scan is done.

        :param sub_array_id: The index id of the subarray to control
        """
        # builder = get_message_board_builder()

        # return builder
        raise NotImplementedError()

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
        # TODO determine what needs to be waited for
        return builder


class ScanStep(base.ScanStep, LogEnabled):

    """Implementation of Scan Step for SDP."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()

    def do(self, sub_array_id: int):
        """Domain logic for running a scan on subarray in sdp.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        # scan_config = json.dumps({"id": 1})
        # scan_duration = Memo().get("scan_duration")
        # subarray_name = self._tel.tm.subarray(sub_array_id)
        # subarray = con_config.get_device_proxy(subarray_name)
        # self._log(f"Commanding {subarray_name} to Scan with {scan_config}")
        raise NotImplementedError()
        # try:
        #     subarray.command_inout("Scan", scan_config)
        #     sleep(scan_duration)
        #     subarray.command_inout("EndScan")
        # except Exception as exception:
        #     logger.exception(exception)
        #     raise exception

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
        # TODO  determine what needs to be waited for
        # subarray_name = self._tel.tm.subarray(sub_array_id)
        # builder.set_waiting_on(subarray_name).for_attribute(
        #     "obsState"
        # ).to_become_equal_to("SCANNING")
        return builder

    def set_wait_for_undo(
        self, sub_array_id: int, receptors: List[int]
    ) -> Union[MessageBoardBuilder, None]:
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        """
        return None


class TMCEntryPoint(CompositeEntryPoint):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2

    def __init__(self) -> None:
        """Init Object"""
        super().__init__()
        self.set_online_step = NoOpStep()
        self.start_up_step = StartUpStep(self.nr_of_subarrays)
        self.assign_resources_step = AssignResourcesStep()
        self.configure_scan_step = ConfigureStep()
        self.scan_step = ScanStep()
