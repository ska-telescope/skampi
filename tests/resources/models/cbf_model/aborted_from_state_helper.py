import logging
import os
from typing import Literal

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import \
    get_new_message_board_builder
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.event_waiting.wait import wait, wait_for
from ska_ser_skallop.subscribing.configuration import reset_configurations

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

AbortedFromStateType = Literal["from_scanning","from_ready","from_configuring","from_idle","from_resourcing", "unknown"]
class AbortedStateHelper(LogEnabled):

    def __init__(self) -> None:
        super().__init__()
        self._state: AbortedFromStateType = "unknown"

    def set_going_into_aborted(self, sub_array_id: int):
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        state = subarray.read_attribute("obsstate").value
        self._set_state_from_current_state(state)
        if self._state in ["from_scanning","from_configuring"]:
            self._wait_for_subarray_to_be_ready(sub_array_id)
            self._end_subarray(sub_array_id)
        elif self._state == "from_ready":
            self._end_subarray(sub_array_id)


    def _wait_for_subarray_to_be_ready(self,  subarray_id: int):
        subarray_name = self._tel.csp.cbf.subarray(subarray_id)
        reset_configurations()
        builder = get_new_message_board_builder()
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("READY")
        with wait_for(builder, live_logging=True):
            pass
        builder.board.__init__()

    def _set_state_from_current_state(self, state: ObsState):
        if state == ObsState.RESOURCING:
            self._state = "from_resourcing"
        elif state == ObsState.IDLE:
            self._state = "from_idle"
        elif state == ObsState.CONFIGURING:
            self._state = "from_configuring"
        elif state == ObsState.READY:
            self._state = "from_ready"
        elif state == ObsState.SCANNING:
            self._state = "from_scanning"

    @property
    def state(self) -> AbortedFromStateType:
        return self._state
    
    @state.setter
    def state(self, state: ObsState):
        if state == ObsState.RESOURCING:
            self._state = "from_resourcing"
        elif state == ObsState.IDLE:
            self._state = "from_idle"
        elif state == ObsState.CONFIGURING:
            self._state = "from_configuring"
        elif state == ObsState.READY:
            self._state = "from_ready"
        elif state == ObsState.SCANNING:
            self._state = "from_scanning"

    def _end_subarray(self, subarray_id: int):
        subarray_name = self._tel.csp.cbf.subarray(subarray_id)
        subarray = con_config.get_device_proxy(subarray_name)
        reset_configurations()
        builder = get_new_message_board_builder()
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE", ignore_first=False)
        with wait_for(builder, live_logging=True):
            self._log(f"commanding {subarray_name} with command End")
            subarray.command_inout("End")
        builder.board.__init__()

    def _reset_subarray(self, subarray_id: int):
        subarray_name = self._tel.csp.cbf.subarray(subarray_id)
        subarray = con_config.get_device_proxy(subarray_name)
        reset_configurations()
        builder = get_new_message_board_builder()
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE", ignore_first=False)
        with wait_for(builder, live_logging=True):
            self._log(f"commanding {subarray_name} with command ObsReset")
            subarray.command_inout("ObsReset")
        builder.board.__init__()

    def _abort_subarray(self, subarray_id: int):
        subarray_name = self._tel.csp.cbf.subarray(subarray_id)
        subarray = con_config.get_device_proxy(subarray_name)
        reset_configurations()
        builder = get_new_message_board_builder()
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("ABORTED", ignore_first=False)
        with wait_for(builder, live_logging=True):
            self._log(f"commanding {subarray_name} with command Abort")
            subarray.command_inout("Abort")
        builder.board.__init__()


    def prepare_for_restarting(self, subarray_id: int):
       # if self._state in ["from_ready","from_scanning","from_configuring"]:
       #     self._reset_subarray(subarray_id)
       #     self._abort_subarray(subarray_id)
       pass