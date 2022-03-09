"""Domain logic for the sdp."""
import logging
from typing import Union
import os

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    NoOpStep,
    MessageBoardBuilder,
)
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.event_handling.builders import get_message_board_builder


logger = logging.getLogger(__name__)
SCAN_DURATION = 1


class LogEnabled:
    """class that allows for logging if set by env var"""

    def __init__(self) -> None:
        self._live_logging = bool(os.getenv("DEBUG"))
        self._tel = names.TEL()

    def _log(self, mssage: str):
        if self._live_logging:
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


class SDPEntryPoint(CompositeEntryPoint):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2

    def __init__(self) -> None:
        """Init Object"""
        super().__init__()
        self.set_online_step = NoOpStep()
        self.start_up_step = StartUpStep(self.nr_of_subarrays)
