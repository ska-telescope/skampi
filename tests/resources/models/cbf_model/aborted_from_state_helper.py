import logging
import os

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import (
    MessageBoardBuilder
)
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.event_waiting.wait import wait_for as wait_for
from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from ska_ser_skallop.subscribing.configuration import MessageBoard
from ska_ser_skallop.mvp_control.entry_points import configuration
from ska_ser_skallop.subscribing.configuration import patch_messageboard

from ..mvp_model.states import ObsState

logger = logging.getLogger(__name__)


class LogEnabled:
    """class that allows for logging if set by env var"""

    def __init__(self) -> None:
        self._live_logging = bool(os.getenv("DEBUG_ENTRYPOINT"))
        self._tel = names.TEL()

    def _log(self, mssage: str):
        if self._live_logging:
            logger.info(mssage)


class AbortedStateHelper(LogEnabled):
    def __init__(
        self, entry_point: EntryPoint
    ) -> None:
        super().__init__()
        self._entry_point = entry_point

    def set_entry_point(self, entry_point: EntryPoint):
        self._entry_point = entry_point

    def set_going_into_aborted(self, subarray_id: int):
        with patch_messageboard(MessageBoard()):
            subarray_name = self._tel.csp.cbf.subarray(subarray_id)
            subarray = con_config.get_device_proxy(subarray_name)
            state = subarray.read_attribute("obsstate").value
            logger.warning(f"Setting {subarray_name} to IDLE before attempting abort (current state: {state})")
            if state in [ObsState.SCANNING, ObsState.CONFIGURING, ObsState.READY]:
                logger.warning(f"First wait for {subarray_name} to be READY")
                self._wait_for_subarray_to_be_ready(subarray_id)
                logger.warning(f"Attempt to put {subarray_name} in IDLE")
                self._end_subarray(subarray_id)

    def _wait_for_subarray_to_be_ready(self, subarray_id: int):
        builder = self._entry_point.set_waiting_for_configure(subarray_id)
        with wait_for(builder, live_logging=True):
            pass

    def _end_subarray(self, subarray_id: int):
        builder = self._entry_point.set_waiting_for_clear_configure(subarray_id)
        with wait_for(builder, live_logging=True):
            self._entry_point.clear_configuration(subarray_id)
