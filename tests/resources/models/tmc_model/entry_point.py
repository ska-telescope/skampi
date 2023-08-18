"""Domain logic for the tmc."""
import copy
import json
import logging
import os
from time import sleep
from typing import Any, List

from resources.utils.validation import CommandException, command_success
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from ska_ser_skallop.event_handling.handlers import WaitForLRCComplete
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    MessageBoardBuilder,
)
from ska_ser_skallop.utils.nrgen import get_id
from ska_ser_skallop.utils.singleton import Memo

from ..csp_model.entry_point import CSPWaitReadyStep
from ..mvp_model.env import Observation
from ..mvp_model.object_with_obsconfig import HasObservation
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


class WithCommandID:
    def __init__(self) -> None:
        self._long_running_command_subscriber = None

    @property
    def long_running_command_subscriber(self) -> WaitForLRCComplete | None:
        return Memo().get("long_running_command_subscriber")

    @long_running_command_subscriber.setter
    def long_running_command_subscriber(self, subscriber: WaitForLRCComplete):
        Memo(long_running_command_subscriber=subscriber)


class StartUpStep(base.StartUpStep, LogEnabled):
    """Implementation of Startup step for TMC"""

    def __init__(self, nr_of_subarrays: int = 3, receptors: list[int] = [1, 2, 3, 4]) -> None:
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays
        self.receptors = receptors

    def do_startup(self):
        """Domain logic for starting up a telescope on the interface to TMC.

        This implements the set_telescope_to_running method on the entry_point.
        """
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name, fast_load=True)
        self._log(f"Commanding {central_node_name} with TelescopeOn")
        central_node.command_inout("TelescopeOn")

    def set_wait_for_do_startup(self) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for
         before startup of telescope is done.

         :return: brd
        """
        brd = get_message_board_builder()
        # set sdp master and sdp subarray to be waited before startup completes
        brd.set_waiting_on(self._tel.sdp.master).for_attribute("state").to_become_equal_to(
            "ON", ignore_first=False
        )
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.sdp.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("ON", ignore_first=False)
        # set csp controller and csp subarray to be waited
        # before startup completes
        brd.set_waiting_on(self._tel.csp.controller).for_attribute("state").to_become_equal_to(
            "ON", ignore_first=False
        )
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.csp.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("ON", ignore_first=False)
        # we wait for cbf vccs to be in proper initialised state
        if self._tel.skamid:
            brd.set_waiting_on(self._tel.csp.cbf.controller).for_attribute(
                "reportVccState"
            ).to_become_equal_to(["[0, 0, 0, 0]", "[0 0 0 0]"], ignore_first=False)
        # set dish master to be waited before startup completes
        if self._tel.skamid:
            for receptor_id in self.receptors:
                dish = f"ska00{receptor_id}/elt/master"
                brd.set_waiting_on(dish).for_attribute("state").to_become_equal_to(
                    "ON", ignore_first=False
                )
        # set centralnode telescopeState waited before startup completes
        brd.set_waiting_on(self._tel.tm.central_node).for_attribute(
            "telescopeState"
        ).to_become_equal_to("ON", ignore_first=False)
        return brd

    def set_wait_for_doing_startup(self) -> MessageBoardBuilder:
        """
        Not implemented.

        :raises NotImplementedError: Raises the error when
                implementation is not done.
        """
        raise NotImplementedError()

    def set_wait_for_undo_startup(self) -> MessageBoardBuilder:
        """
        Domain logic for what needs to be waited
         for switching the telescope off.

         :return: brd
        """
        brd = get_message_board_builder()
        # TODO set what needs to be waited before start up completes
        brd.set_waiting_on(self._tel.sdp.master).for_attribute("state").to_become_equal_to(
            "OFF", ignore_first=False
        )
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.sdp.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
        # set dish master to be waited before startup completes
        if self._tel.skamid:
            brd.set_waiting_on(self._tel.csp.controller).for_attribute("state").to_become_equal_to(
                "OFF", ignore_first=False
            )
            for index in range(1, self.nr_of_subarrays + 1):
                brd.set_waiting_on(self._tel.csp.subarray(index)).for_attribute(
                    "state"
                ).to_become_equal_to("OFF", ignore_first=False)
            for receptor_id in self.receptors:
                dish = f"ska00{receptor_id}/elt/master"
                brd.set_waiting_on(dish).for_attribute("state").to_become_equal_to(
                    "STANDBY", ignore_first=False
                )
            # set centralnode telescopeState waited before startup completes
            brd.set_waiting_on(self._tel.tm.central_node).for_attribute(
                "telescopeState"
            ).to_become_equal_to("STANDBY", ignore_first=False)
        elif self._tel.skalow:
            brd.set_waiting_on(self._tel.tm.central_node).for_attribute(
                "telescopeState"
            ).to_become_equal_to(["OFF", "UNKNOWN"], ignore_first=False)
        return brd

    def undo_startup(self):
        """Domain logic for switching the telescope off using tmc."""
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name, fast_load=True)
        self._log(f"Commanding {central_node_name} with TelescopeOff")
        central_node.command_inout("TelescopeOff")


class AssignResourcesErrorStep(base.AssignResourcesStep, LogEnabled, WithCommandID):
    """Implementation of Assign Resources Step for TMC"""

    def __init__(self, observation: Observation) -> None:
        """
        Init object.

        :param observation: An instance of the Observation class or None.
            If None, a new instance of Observation will be created.
        """
        super().__init__()
        self._tel = names.TEL()
        self.observation = observation

    def _generate_unique_pb_ids(self, config_json: dict[str, Any]):
        """This method will generate unique eb and sb ids.
        Update it in config json
        :param config_json: Config json for Assign Resource command
        """
        for pb in config_json["sdp"]["processing_blocks"]:
            pb["pb_id"] = get_id("pb-test-********-*****")

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
        :raises CommandException: raises command exception
        """
        # currently ignore composition as all types will be standard
        assert self.long_running_command_subscriber
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name, fast_load=True)
        if self._tel.skamid:
            config = self.observation.generate_assign_resources_config(sub_array_id).as_json
        elif self._tel.skalow:
            # TODO Low json from CDM is not available.
            # Once it is available pull json from CDM
            config_json = copy.deepcopy(ASSIGN_RESOURCE_JSON_LOW)
            self._generate_unique_pb_ids(config_json)
            config = json.dumps(config_json)

        self._log(f"Commanding {central_node_name} with AssignRescources: {config}")

        command_id = central_node.command_inout("AssignResources", config)

        if command_success(command_id):
            self.long_running_command_subscriber.set_command_id(command_id)
        else:
            self.long_running_command_subscriber.unsubscribe_all()
            raise CommandException(command_id)

    def undo_assign_resources(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in sdp.

        This implements the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :raises CommandException: raises command exception
        """
        assert self.long_running_command_subscriber
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name, fast_load=True)
        if self._tel.skamid:
            config = self.observation.generate_release_all_resources_config_for_central_node(  # noqa: disable=E501
                sub_array_id
            )
        elif self._tel.skalow:
            # TODO Low json from CDM is not available.
            # Once it is available pull json from CDM
            config = json.dumps(RELEASE_RESOURCE_JSON_LOW)
        self._log(f"Commanding {central_node_name} with ReleaseResources {config}")
        command_id = central_node.command_inout("ReleaseResources", config)

        if command_success(command_id):
            self.long_running_command_subscriber.set_command_id(command_id)
        else:
            self.long_running_command_subscriber.unsubscribe_all()
            raise CommandException(command_id)

    def set_wait_for_do_assign_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited
         for subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
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
        central_node_name = self._tel.tm.central_node
        self.long_running_command_subscriber = brd.set_wait_for_long_running_command_on(
            central_node_name
        )
        return brd

    def set_wait_for_doing_assign_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifyig what needs to be done
         for waiting for subarray to be scanning.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
        """
        brd = get_message_board_builder()
        subarray_name = self._tel.tm.subarray(sub_array_id)
        brd.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "RESOURCING"
        )
        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
            # ).to_become_equal_to("RESOURCING")
        ).to_become_equal_to("IDLE")
        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("RESOURCING")
        central_node_name = self._tel.tm.central_node
        self.long_running_command_subscriber = brd.set_wait_for_long_running_command_on(
            central_node_name
        )
        return brd

    def set_wait_for_undo_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited
         for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
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
        central_node_name = self._tel.tm.central_node
        self.long_running_command_subscriber = brd.set_wait_for_long_running_command_on(
            central_node_name
        )
        return brd


class AssignResourcesStep(base.AssignResourcesStep, LogEnabled):
    """Implementation of Assign Resources Step for TMC"""

    def __init__(self, observation: Observation) -> None:
        """
        Init object.

        :param observation: An instance of the Observation class or None.
            If None, a new instance of Observation will be created.
        """
        super().__init__()
        self._tel = names.TEL()
        self.observation = observation

    def _generate_unique_eb_sb_ids(self, config_json: dict[str, Any]):
        """This method will generate unique eb and sb ids.
        Update it in config json
        :param config_json: Config json for Assign Resource command
        """
        config_json["sdp"]["execution_block"]["eb_id"] = get_id("eb-test-********-*****")
        for pb in config_json["sdp"]["processing_blocks"]:
            pb["pb_id"] = get_id("pb-test-********-*****")

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
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name, fast_load=True)
        if self._tel.skamid:
            config = self.observation.generate_assign_resources_config(sub_array_id).as_json
        elif self._tel.skalow:
            # TODO Low json from CDM is not available.
            # Once it is available pull json from CDM
            config_json = copy.deepcopy(composition)
            self._generate_unique_eb_sb_ids(config_json)
            config = json.dumps(config_json)

        self._log(f"Commanding {central_node_name} with AssignRescources: {config}")

        central_node.command_inout("AssignResources", config)

    def undo_assign_resources(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in sdp.

        This implements the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name, fast_load=True)
        if self._tel.skamid:
            config = self.observation.generate_release_all_resources_config_for_central_node(  # noqa: disable=E501
                sub_array_id
            )
        elif self._tel.skalow:
            # TODO Low json from CDM is not available.
            # Once it is available pull json from CDM
            config = json.dumps(RELEASE_RESOURCE_JSON_LOW)
        self._log(f"Commanding {central_node_name} with ReleaseResources {config}")
        central_node.command_inout("ReleaseResources", config)

    def set_wait_for_do_assign_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited
         for subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
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

    def set_wait_for_doing_assign_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifyig what needs to be done
         for waiting for subarray to be scanning.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
        """
        brd = get_message_board_builder()

        subarray_name = self._tel.tm.subarray(sub_array_id)
        brd.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "RESOURCING"
        )
        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
            # ).to_become_equal_to("RESOURCING")
        ).to_become_equal_to("IDLE")
        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("RESOURCING")

        return brd

    def set_wait_for_undo_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited
         for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
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
    """Implementation of Configure Scan Step for TMC."""

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

        This implements the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param configuration: The assign resources configuration parameters
        :param sb_id: a generic ide to identify a sb to assign resources
        :param duration: duration of scan
        """
        # scan duration needs to be a memorized for
        # future objects that may require it
        Memo(scan_duration=duration)
        subarray_name = self._tel.tm.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        if self._tel.skamid:
            config = self.observation.generate_scan_config().as_json

        elif self._tel.skalow:
            # TODO Low json from CDM is not available.
            # Once it is available pull json from CDM
            config = json.dumps(CONFIGURE_JSON_LOW)
        self._log(f"commanding {subarray_name} with Configure: {config} ")
        subarray.command_inout("Configure", config)

    def undo_configure(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in sdp.

        This implements the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.tm.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with End command")
        subarray.command_inout("End")

    def set_wait_for_do_configure(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited
         for configuring a scan is done.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
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

    def set_wait_for_doing_configure(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Not implemented.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
        """
        brd = get_message_board_builder()

        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("CONFIGURING")

        brd.set_waiting_on(self._tel.tm.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("CONFIGURING")
        return brd

    def set_wait_for_undo_configure(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray
         clear scan config is done.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
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
        """
        Init object.

        :param observation: An instance of the Observation class or None.
            If None, a new instance of Observation will be created.
        """
        super().__init__()
        self._tel = names.TEL()
        self.observation = observation

    def do_scan(self, sub_array_id: int):
        """Domain logic for running a scan on subarray in tmc.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control

        :raises Exception: Raise exception in do method of scan command
        """
        if self._tel.skamid:
            scan_config = self.observation.generate_run_scan_conf().as_json
        elif self._tel.skalow:
            # TODO Low json from CDM is not available.
            # Once it is available pull json from CDM
            scan_config = json.dumps(SCAN_JSON_LOW)
        scan_duration = Memo().get("scan_duration")
        subarray_name = self._tel.tm.subarray(sub_array_id)
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
        :return: message board builder
        """
        return get_message_board_builder()

    def undo_scan(self, sub_array_id: int):
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        """

    def set_wait_for_doing_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifyig what needs to be done for waiting
         for subarray to be scanning.

        :param sub_array_id: The index id of the subarray to control
        :return: brd
        """
        brd = get_message_board_builder()
        subarray_name = self._tel.tm.subarray(sub_array_id)
        brd.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to("SCANNING")
        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("SCANNING")
        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("SCANNING")
        return brd

    def set_wait_for_undo_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        :return: message board builder
        """
        return get_message_board_builder()


class CSPSetOnlineStep(base.SetOnlineStep, LogEnabled):
    """Domain logic for setting csp to online"""

    def __init__(self, nr_of_subarrays: int) -> None:
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays

    def do_set_online(self):
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

    def set_wait_for_do_set_online(self) -> MessageBoardBuilder:
        """
        Domain logic for waiting for setting to online to be complete.

        :return: brd
        """
        controller_name = self._tel.csp.controller
        builder = get_message_board_builder()
        builder.set_waiting_on(controller_name).for_attribute("adminMode").to_become_equal_to(
            "ONLINE", ignore_first=False
        )
        builder.set_waiting_on(controller_name).for_attribute("state").to_become_equal_to(
            ["OFF", "ON"], ignore_first=False
        )
        for index in range(1, self.nr_of_subarrays + 1):
            subarray = self._tel.csp.subarray(index)
            builder.set_waiting_on(subarray).for_attribute("adminMode").to_become_equal_to(
                "ONLINE", ignore_first=False
            )
            builder.set_waiting_on(subarray).for_attribute("state").to_become_equal_to(
                ["OFF", "ON"], ignore_first=False
            )
        return builder

    def undo_set_online(self):
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

    def set_wait_for_undo_set_online(self) -> MessageBoardBuilder:
        """
        Domain logic for waiting for setting to offline to be complete.

        :return: builder
        """
        controller_name = self._tel.csp.controller
        builder = get_message_board_builder()
        builder.set_waiting_on(controller_name).for_attribute("adminMode").to_become_equal_to(
            "OFFLINE", ignore_first=False
        )
        for index in range(1, self.nr_of_subarrays + 1):
            subarray = self._tel.csp.subarray(index)
            builder.set_waiting_on(subarray).for_attribute("adminMode").to_become_equal_to(
                "OFFLINE", ignore_first=False
            )
        return builder

    def set_wait_for_doing_set_online(self) -> MessageBoardBuilder:
        """
        Not implemented.

        :raises NotImplementedError: Raises the error when implementation
                is not done.
        """
        raise NotImplementedError()


class TMCObsResetStep(base.ObsResetStep, LogEnabled):
    def set_wait_for_do_obsreset(self, sub_array_id: int) -> MessageBoardBuilder:
        builder = get_message_board_builder()
        subarray_name = self._tel.tm.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "ABORTED", ignore_first=True
        )  # IDLE
        return builder

    def do_obsreset(self, sub_array_id: int):
        subarray_name = self._tel.tm.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with ObsReset command")
        subarray.command_inout("Obsreset")


class TMCAbortStep(base.AbortStep, LogEnabled):
    def do_abort(self, sub_array_id: int):
        subarray_name = self._tel.tm.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with Abort command")
        subarray.command_inout("Abort")

    def set_wait_for_do_abort(self, sub_array_id: int) -> MessageBoardBuilder:
        builder = get_message_board_builder()
        subarray_name = self._tel.tm.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "ABORTED", ignore_first=True
        )
        csp_subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(csp_subarray_name).for_attribute("obsState").to_become_equal_to(
            "ABORTED", ignore_first=True
        )
        sdp_subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(sdp_subarray_name).for_attribute("obsState").to_become_equal_to(
            "ABORTED", ignore_first=True
        )
        return builder

    def undo_abort(self, sub_array_id: int):
        """Domain logic for restart configuration on a subarray in tmc.

        This implements the restart method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.tm.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with Restart command")
        subarray.command_inout("Restart")

    def set_wait_for_undo_abort(self, sub_array_id: int) -> MessageBoardBuilder:
        builder = get_message_board_builder()
        subarray_name = self._tel.tm.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "EMPTY", ignore_first=True
        )
        return builder


class TMCRestart(base.RestartStep, LogEnabled):
    def do_restart(self, sub_array_id: int):
        subarray_name = self._tel.tm.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with Restart command")
        subarray.command_inout("Restart")

    def set_wait_for_do_restart(self, sub_array_id: int, _: Any = None) -> MessageBoardBuilder:
        builder = get_message_board_builder()
        subarray_name = self._tel.tm.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "EMPTY", ignore_first=False
        )
        csp_subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(csp_subarray_name).for_attribute("obsState").to_become_equal_to(
            "EMPTY", ignore_first=False
        )
        sdp_subarray_name = self._tel.sdp.subarray(sub_array_id)
        builder.set_waiting_on(sdp_subarray_name).for_attribute("obsState").to_become_equal_to(
            ["EMPTY", "IDLE"], ignore_first=False
        )
        return builder


# TODO add an implementation of obsreset
# currently we do obsreset via an restart
#  not this results in the SUT going to EMPTY and not
# IDLE
class TMCObsReset(base.ObsResetStep, TMCRestart, LogEnabled):
    def do_obsreset(self, sub_array_id: int):
        self.do_restart(sub_array_id)

    def set_wait_for_do_obsreset(self, sub_array_id: int, _: Any = None) -> MessageBoardBuilder:
        return self.set_wait_for_do_restart(sub_array_id)


class TMCWaitReadyStep(CSPWaitReadyStep):
    pass


class TMCEntryPoint(CompositeEntryPoint, HasObservation):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2
    nr_of_receptors = 4
    receptors = [1, 2, 3, 4]

    def __init__(self) -> None:
        """Init Object"""
        super().__init__()
        HasObservation.__init__(self)
        observation = self.observation
        self.set_online_step = CSPSetOnlineStep(self.nr_of_subarrays)  # Temporary fix
        self.start_up_step = StartUpStep(self.nr_of_subarrays, self.receptors)
        self.assign_resources_step = AssignResourcesStep(observation)
        self.configure_scan_step = ConfigureStep(observation)
        self.scan_step = ScanStep(observation)
        self.abort_step = TMCAbortStep()
        # TODO add an implementation of obsreset
        # currently we do obsreset via an restart
        #  not this results in the SUT going to EMPTY and not
        # IDLE
        self.obsreset_step = TMCObsReset()
        self.restart_step = TMCRestart()
        self.wait_ready = TMCWaitReadyStep(self.nr_of_subarrays)


class TMCErrorEntryPoint(CompositeEntryPoint, HasObservation):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2
    nr_of_receptors = 4
    receptors = [1, 2, 3, 4]

    def __init__(self) -> None:
        """Init Object"""
        super().__init__()
        HasObservation.__init__(self)
        observation = self.observation
        self.set_online_step = CSPSetOnlineStep(self.nr_of_subarrays)  # Temporary fix
        self.start_up_step = StartUpStep(self.nr_of_subarrays, self.receptors)
        self.assign_resources_step = AssignResourcesErrorStep(observation)
        self.wait_ready = TMCWaitReadyStep(self.nr_of_subarrays)



ASSIGN_RESOURCE_JSON_LOW = {
    "interface": "https://schema.skao.int/ska-low-tmc-assignresources/3.0",
    "transaction_id": "txn-....-00001",
    "subarray_id": 1,
    "mccs": {
        "subarray_beam_ids": [1],
        "station_ids": [[1, 2]],
        "channel_blocks": [3]
    },
    "sdp": {
        "interface": "https://schema.skao.int/ska-sdp-assignres/0.4",
        "resources": {"receptors": ["SKA001", "SKA002", "SKA003", "SKA004"]},
        "execution_block": {
            "eb_id": "eb-test-20220916-00000",
            "context": {},
            "max_length": 3600.0,
            "beams": [{"beam_id": "vis0", "function": "visibilities"}],
            "scan_types": [
                {
                    "scan_type_id": ".default",
                    "beams": {
                        "vis0": {
                            "channels_id": "vis_channels",
                            "polarisations_id": "all"
                        }
                    }
                },
                {
                    "scan_type_id": "target:a",
                    "derive_from": ".default",
                    "beams": {"vis0": {"field_id": "field_a"}}
                },
                {
                    "scan_type_id": "calibration:b",
                    "derive_from": ".default",
                    "beams": {"vis0": {"field_id": "field_b"}}
                }
            ],
            "channels": [
                {
                    "channels_id": "vis_channels",
                    "spectral_windows": [
                        {
                            "spectral_window_id": "fsp_1_channels",
                            "count": 4,
                            "start": 0,
                            "stride": 2,
                            "freq_min": 350000000.0,
                            "freq_max": 368000000.0,
                            "link_map": [[0, 0], [200, 1], [744, 2], [944, 3]]
                        }
                    ]
                }
            ],
            "polarisations": [
                {
                    "polarisations_id": "all",
                    "corr_type": ["XX", "XY", "YX", "YY"]
                }
            ],
            "fields": [
                {
                    "field_id": "field_a",
                    "phase_dir": {
                        "ra": [123.0],
                        "dec": [-60.0],
                        "reference_time": "...",
                        "reference_frame": "ICRF3"
                    },
                    "pointing_fqdn": "..."
                },
                {
                    "field_id": "field_b",
                    "phase_dir": {
                        "ra": [123.0],
                        "dec": [-60.0],
                        "reference_time": "...",
                        "reference_frame": "ICRF3"
                    },
                    "pointing_fqdn": "..."
                }
            ]
        },
        "processing_blocks": [
            {
                "pb_id": "pb-test-20220916-00000",
                "script": {
                    "kind": "realtime",
                    "name": "test-receive-addresses",
                    "version": "0.6.1"
                },
                "sbi_ids": ["sbi-test-20220916-00000"],
                "parameters": {
                    "time-to-ready": 5
                }
            }
        ]
    }
}


RELEASE_RESOURCE_JSON_LOW = {
    "interface": "https://schema.skao.int/ska-low-tmc-releaseresources/3.0",
    "transaction_id": "txn-....-00001",
    "subarray_id": 1,
    "release_all": True,
}

CONFIGURE_JSON_LOW = {
    "interface": "https://schema.skao.int/ska-low-tmc-configure/3.0",
    "transaction_id": "txn-....-00001",
    "mccs": {
        "stations": [{"station_id": 1}, {"station_id": 2}],
        "subarray_beams": [
            {
                "subarray_beam_id": 1,
                "station_ids": [1, 2],
                "update_rate": 0.0,
                "channels": [[0, 8, 1, 1], [8, 8, 2, 1], [24, 16, 2, 1]],
                "antenna_weights": [1.0, 1.0, 1.0],
                "phase_centre": [0.0, 0.0],
                "target": {
                    "reference_frame": "HORIZON",
                    "target_name": "DriftScan",
                    "az": 180.0,
                    "el": 45.0,
                },
            }
        ],
    },
    "sdp": {
        "interface": "https://schema.skao.int/ska-sdp-configure/0.4",
        "scan_type": "target:a",
    },
    "csp": {
        "interface": "https://schema.skao.int/ska-csp-configure/2.0",
        "subarray": {"subarray_name": "science period 23"},
        "common": {
            "config_id": "sbi-mvp01-20200325-00001-science_A",
        },
        "lowcbf": {
            "stations": {
                "stns": [[1, 0], [2, 0], [3, 0], [4, 0]],
                "stn_beams": [
                    {
                        "beam_id": 1,
                        "freq_ids": [64, 65, 66, 67, 68, 69, 70, 71],
                        "boresight_dly_poly": "url",
                    }
                ],
            },
            "timing_beams": {
                "beams": [
                    {
                        "pst_beam_id": 13,
                        "stn_beam_id": 1,
                        "offset_dly_poly": "url",
                        "stn_weights": [0.9, 1.0, 1.0, 0.9],
                        "jones": "url",
                        "dest_ip": ["10.22.0.1:2345", "10.22.0.3:3456"],
                        "dest_chans": [128, 256],
                        "rfi_enable": [True, True, True],
                        "rfi_static_chans": [1, 206, 997],
                        "rfi_dynamic_chans": [242, 1342],
                        "rfi_weighted": 0.87,
                    }
                ]
            },
        },
    },
    "tmc": {"scan_duration": 10.0},
}


SCAN_JSON_LOW = {
    "interface": "https://schema.skao.int/ska-low-tmc-scan/3.0",
    "transaction_id": "txn-....-00001",
    "scan_id": 1,
}
