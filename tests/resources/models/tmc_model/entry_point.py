"""Domain logic for the tmc."""
import json
import logging
import os
from typing import List, Union
from time import sleep
from ska_ser_skallop.utils.singleton import Memo
from ska_ser_skallop.mvp_control.configuration import configuration as conf
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    MessageBoardBuilder,
)

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


class StartUpStep(base.ObservationStep, LogEnabled):
    """Implementation of Startup step for SDP"""

    def __init__(
        self, nr_of_subarrays: int = 3, receptors: list[int] = [1, 2, 3, 4]
    ) -> None:
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays
        self.receptors = receptors

    def do(self):
        """Domain logic for starting up a telescope on the interface to TMC.

        This implements the set_telescope_to_running method on the entry_point.
        """
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name, fast_load=True)
        self._log(f"Commanding {central_node_name} with TelescopeOn")
        central_node.command_inout("TelescopeOn")

    def set_wait_for_do(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic specifying what needs to be waited for before startup of telescope is done."""
        brd = get_message_board_builder()
        # set sdp master and sdp subarray to be waited before startup completes
        brd.set_waiting_on(self._tel.sdp.master).for_attribute(
            "state"
        ).to_become_equal_to("ON", ignore_first=False)
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.sdp.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("ON")
        # set csp controller and csp subarray to be waited before startup completes
        brd.set_waiting_on(self._tel.csp.controller).for_attribute(
            "state"
        ).to_become_equal_to("ON", ignore_first=False)
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.csp.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("ON", ignore_first=False)
        # we wait for cbf vccs to be in proper initialised state
        brd.set_waiting_on(self._tel.csp.cbf.controller).for_attribute(
            "reportVccState"
        ).to_become_equal_to(["[0, 0, 0, 0]", "[0 0 0 0]"], ignore_first=False)
        # set dish master to be waited before startup completes
        if self._tel.skamid:
            for dish in self._tel.skamid.dishes(self.receptors):
                brd.set_waiting_on(dish).for_attribute("state").to_become_equal_to(
                    "ON", ignore_first=False
                )
        # set centralnode telescopeState waited before startup completes
        brd.set_waiting_on(self._tel.tm.central_node).for_attribute(
            "telescopeState"
        ).to_become_equal_to("ON", ignore_first=False)
        return brd

    def set_wait_for_doing(self) -> Union[MessageBoardBuilder, None]:
        """Not implemented."""
        raise NotImplementedError()

    def set_wait_for_undo(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic for what needs to be waited for switching the telescope off."""
        brd = get_message_board_builder()
        # TODO set what needs to be waited before start up completes
        brd.set_waiting_on(self._tel.sdp.master).for_attribute(
            "state"
        ).to_become_equal_to("OFF", ignore_first=False)
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.sdp.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("OFF")
        brd.set_waiting_on(self._tel.csp.controller).for_attribute(
            "state"
        ).to_become_equal_to("OFF", ignore_first=False)
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.csp.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
        # set dish master to be waited before startup completes
        if self._tel.skamid:
            for dish in self._tel.skamid.dishes(self.receptors):
                brd.set_waiting_on(dish).for_attribute("state").to_become_equal_to(
                    "STANDBY", ignore_first=False
                )
        # set centralnode telescopeState waited before startup completes
        brd.set_waiting_on(self._tel.tm.central_node).for_attribute(
            "telescopeState"
        ).to_become_equal_to("STANDBY", ignore_first=False)
        return brd

    def undo(self):
        """Domain logic for switching the telescope off using tmc."""
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name, fast_load=True)
        self._log(f"Commanding {central_node_name} with TelescopeOff")
        central_node.command_inout("TelescopeOff")


class AssignResourcesStep(base.AssignResourcesStep, LogEnabled):
    """Implementation of Assign Resources Step."""

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
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name, fast_load=True)

        config = self.observation.generate_assign_resources_config(sub_array_id).as_json

        self._log(f"Commanding {central_node_name} with AssignRescources: {config}")

        central_node.command_inout("AssignResources", config)

    def undo(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in sdp.

        This implements the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name, fast_load=True)
        config = (
            self.observation.generate_release_all_resources_config_for_central_node(
                sub_array_id
            )
        )
        self._log(f"Commanding {central_node_name} with ReleaseResources {config}")
        central_node.command_inout("ReleaseResources", config)

    def set_wait_for_do(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        brd = get_message_board_builder()

        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")
        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")

        brd.set_waiting_on(self._tel.tm.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")
        return brd

    def set_wait_for_doing(self, sub_array_id: int) -> MessageBoardBuilder:
        """Not implemented."""
        raise NotImplementedError()

    def set_wait_for_undo(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        brd = get_message_board_builder()
        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("EMPTY")
        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("EMPTY")

        brd.set_waiting_on(self._tel.tm.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("EMPTY")

        return brd


class ConfigureStep(base.ConfigureStep, LogEnabled):
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

        This implements the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration parameters
        :param sb_id: a generic ide to identify a sb to assign resources
        """
        # scan duration needs to be a memorized for future objects that may require it
        # Memo(scan_duration=duration)
        subarray_name = self._tel.tm.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        config = self.observation.generate_scan_config().as_json
        self._log(f"commanding {subarray_name} with Configure: {config} ")

        subarray.command_inout("Configure", config)

    def undo(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in sdp.

        This implements the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.tm.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with End command")
        subarray.command_inout("End")

    def set_wait_for_do(
        self, sub_array_id: int, receptors: List[int]
    ) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for configuring a scan is done.

        :param sub_array_id: The index id of the subarray to control
        """
        brd = get_message_board_builder()

        # return builder
        brd = get_message_board_builder()

        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("READY")
        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("READY")
        brd.set_waiting_on(self._tel.tm.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("READY")
        return brd

    def set_wait_for_doing(
        self, sub_array_id: int, receptors: List[int]
    ) -> MessageBoardBuilder:
        """Not implemented."""
        brd = get_message_board_builder()

        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("CONFIGURING")
        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("CONFIGURING")

        brd.set_waiting_on(self._tel.tm.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("CONFIGURING")
        return brd

    def set_wait_for_undo(
        self, sub_array_id: int, receptors: List[int]
    ) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray clear scan config is done.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        """
        brd = get_message_board_builder()
        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")
        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")
        brd.set_waiting_on(self._tel.tm.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")

        return brd


class ScanStep(base.ScanStep, LogEnabled):
    """Implementation of Scan Step for TMC."""

    def __init__(self, observation: Observation) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()
        self.observation = observation

    def do(self, sub_array_id: int):
        """Domain logic for configuring a scan on subarray in sdp.

        This implements the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration parameters
        :param sb_id: a generic ide to identify a sb to assign resources
        """
        scan_config = json.dumps({"interface":"https://schema.skao.intg/ska-tmc-scan/2.0","transaction_id":"txn-....-00001","scan_id":1}) # may be modified
        scan_duration = Memo().get("scan_duration")
        subarray_name = self._tel.tm.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"Commanding {subarray_name} to Scan with {scan_config}")
        try:
            subarray.command_inout("Scan", scan_config)
            sleep(scan_duration)
            subarray.command_inout("EndScan")
        except Exception as exception:
            logger.exception(exception)
            raise exception

        # scan_config = self.observation.generate_run_scan_conf().as_json
        # scan_duration = Memo().get("scan_duration")
        # subarray_name = self._tel.tm.subarray(sub_array_id).sdp_leaf_node  # type: ignore
        # subarray = con_config.get_device_proxy(subarray_name)  # type: ignore
        # self._log(f"Commanding {subarray_name} to Scan with {scan_config}")
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
        brd = get_message_board_builder()
        subarray_name = self._tel.tm.subarray(sub_array_id)
        brd.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("READY")
        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("READY")
        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("READY")
        return brd

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
        brd = get_message_board_builder()
        subarray_name = self._tel.tm.subarray(sub_array_id)
        brd.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("SCANNING")
        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("SCANNING")
        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("SCANNING")
        return brd

    def set_wait_for_undo(
        self, sub_array_id: int, receptors: List[int]
    ) -> Union[MessageBoardBuilder, None]:
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        """
        return None


class CSPSetOnlineStep(base.ObservationStep, LogEnabled):
    """Domain logic for setting csp to online"""

    def __init__(self, nr_of_subarrays: int) -> None:
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays

    def do(self):
        """Domain logic for setting devices in csp to online."""
        controller_name = self._tel.csp.controller
        controller = con_config.get_device_proxy(controller_name, fast_load=True)
        self._log(f"Setting adminMode for {controller_name} to '0' (ONLINE)")
        controller.write_attribute("adminmode", 0)
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.csp.subarray(index)
            subarray = con_config.get_device_proxy(subarray_name, fast_load=True)
            self._log(f"Setting adminMode for {subarray_name} to '0' (ONLINE)")
            subarray.write_attribute("adminmode", 0)

    def set_wait_for_do(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic for waiting for setting to online to be complete."""
        controller_name = self._tel.csp.controller
        builder = get_message_board_builder()
        builder.set_waiting_on(controller_name).for_attribute(
            "adminMode"
        ).to_become_equal_to("ONLINE", ignore_first=False)
        builder.set_waiting_on(controller_name).for_attribute(
            "state"
        ).to_become_equal_to(["OFF", "ON"], ignore_first=False)
        for index in range(1, self.nr_of_subarrays + 1):
            subarray = self._tel.csp.subarray(index)
            builder.set_waiting_on(subarray).for_attribute(
                "adminMode"
            ).to_become_equal_to("ONLINE", ignore_first=False)
            builder.set_waiting_on(subarray).for_attribute("state").to_become_equal_to(
                ["OFF", "ON"], ignore_first=False
            )
        return builder

    def undo(self):
        """Domain logic for setting devices in csp to offline."""
        controller_name = self._tel.csp.controller
        controller = con_config.get_device_proxy(controller_name, fast_load=True)
        self._log(f"Setting adminMode for {controller_name} to '1' (OFFLINE)")
        controller.write_attribute("adminmode", 1)
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.csp.subarray(index)
            subarray = con_config.get_device_proxy(subarray_name, fast_load=True)
            self._log(f"Setting adminMode for {subarray_name} to '1' (OFFLINE)")
            subarray.write_attribute("adminmode", 1)

    def set_wait_for_undo(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic for waiting for setting to offline to be complete."""
        controller_name = self._tel.csp.controller
        builder = get_message_board_builder()
        builder.set_waiting_on(controller_name).for_attribute(
            "adminMode"
        ).to_become_equal_to("OFFLINE", ignore_first=False)
        for index in range(1, self.nr_of_subarrays + 1):
            subarray = self._tel.csp.subarray(index)
            builder.set_waiting_on(subarray).for_attribute(
                "adminMode"
            ).to_become_equal_to("OFFLINE", ignore_first=False)
        return builder

    def set_wait_for_doing(self) -> MessageBoardBuilder:
        """Not implemented."""
        raise NotImplementedError()


class TMCEntryPoint(CompositeEntryPoint):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2
    nr_of_receptors = 4
    receptors = [1, 2, 3, 4]

    def __init__(self, observation: Observation | None = None) -> None:
        """Init Object"""
        super().__init__()
        if not observation:
            observation = Observation()
        self.observation = observation
        self.set_online_step = CSPSetOnlineStep(self.nr_of_subarrays)  # Temporary fix
        self.start_up_step = StartUpStep(self.nr_of_subarrays, self.receptors)
        self.assign_resources_step = AssignResourcesStep(observation)
        self.configure_scan_step = ConfigureStep(observation)
        self.scan_step = ScanStep(observation)
