"""Domain logic for the tmc."""
import json
import logging
import os
from typing import List, Union

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from ska_ser_skallop.mvp_control.configuration import composition as comp
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    MessageBoardBuilder,
    NoOpStep,
)

logger = logging.getLogger(__name__)


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
        self.nr_of_subarrays = 3

    def do(self):
        """Domain logic for starting up a telescope on the interface to TMC.

        This implements the set_telescope_to_running method on the entry_point.
        """
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name)
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
        # set centralnode telescopeState waited before startup completes
        brd.set_waiting_on(self._tel.tm.central_node).for_attribute(
            "telescopeState"
        ).to_become_equal_to("STANDBY", ignore_first=False)
        return brd

    def undo(self):
        """Domain logic for switching the telescope off using tmc."""
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name)
        self._log(f"Commanding {central_node_name} with TelescopeOff")
        central_node.command_inout("TelescopeOff")


# TODO: Implement AssignResources and ReleaseResources
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
        # subarray_name = self._tel.tm.subarray(sub_array_id)
        # subarray = con_config.get_device_proxy(subarray_name)
        # standard_composition = comp.generate_standard_comp(
        #     sub_array_id, dish_ids, sb_id
        # )
        # tmc_standard_composition = json.dumps(json.loads(standard_composition)["sdp"])
        # self._log(
        #     f"commanding {subarray_name} with AssignResources: {tmc_standard_composition} "
        # )
        # # TODO verify command correctness
        # subarray.command_inout("AssignResources", tmc_standard_composition)
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name)
        # standard_composition = comp.generate_standard_comp(
        #    sub_array_id, dish_ids, sb_id
        # )
        # standard_composition = comp.generate_standard_comp(
        #     sub_array_id , [1] , sb_id
        # )
        # std_composition = json.loads(comp.generate_standard_comp(
        #    sub_array_id, dish_ids, sb_id
        # ))
        # std_composition["dish"]["receptor_ids"]=["0001"]
        # standard_composition=json.dumps(std_composition)
        #
        #
        self._log(f"Commanding {central_node_name} with AssignRescources")
        tmc_mid_assign_configuration = json.dumps(tmc_mid_assign_resources)
        central_node.command_inout("AssignResources", tmc_mid_assign_configuration)

    def undo(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in sdp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        # subarray_name = self._tel.tm.subarray(sub_array_id)
        # subarray = con_config.get_device_proxy(subarray_name)
        # self._log(f"Commanding {subarray_name} to ReleaseResources")
        # # TODO verify command correctness
        # subarray.command_inout("ReleaseResources")
        central_node_name = self._tel.tm.central_node
        central_node = con_config.get_device_proxy(central_node_name)
        # tear_down_composition = comp.generate_tear_down_all_resources(
        #    sub_array_id
        # )
        self._log(f"Commanding {central_node_name} with ReleaseRescources")
        tmc_mid_release_configuration = json.dumps(tmc_mid_release_resources)
        central_node.command_inout("ReleaseResources", tmc_mid_release_configuration)

    def set_wait_for_do(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        brd = get_message_board_builder()
        # index=1
        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")
        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")
        
        brd.set_waiting_on(self._tel.tm.subarray(sub_array_id)).for_attribute("obsState"
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
        # index=1
        brd.set_waiting_on(self._tel.sdp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("EMPTY")
        brd.set_waiting_on(self._tel.csp.subarray(sub_array_id)).for_attribute(
            "obsState"
        ).to_become_equal_to("EMPTY")
        
        brd.set_waiting_on(self._tel.tm.subarray(sub_array_id)).for_attribute("obsState"
        ).to_become_equal_to("EMPTY")

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


class CSPSetOnlineStep(base.ObservationStep, LogEnabled):
    """Domain logic for setting csp to online"""

    def __init__(self, nr_of_subarrays: int) -> None:
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays

    def do(self):
        """Domain logic for setting devices in csp to online."""
        controller_name = self._tel.csp.controller
        controller = con_config.get_device_proxy(controller_name)
        self._log(f"Setting adminMode for {controller_name} to '0' (ONLINE)")
        controller.write_attribute("adminmode", 0)
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.csp.subarray(index)
            subarray = con_config.get_device_proxy(subarray_name)
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
        controller = con_config.get_device_proxy(controller_name)
        self._log(f"Setting adminMode for {controller_name} to '1' (OFFLINE)")
        controller.write_attribute("adminmode", 1)
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.csp.subarray(index)
            subarray = con_config.get_device_proxy(subarray_name)
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

    def __init__(self) -> None:
        """Init Object"""
        super().__init__()
        self.set_online_step = CSPSetOnlineStep(self.nr_of_subarrays)  # Temporary fix
        self.start_up_step = StartUpStep(self.nr_of_subarrays)
        self.assign_resources_step = AssignResourcesStep()
        self.configure_scan_step = ConfigureStep()
        self.scan_step = ScanStep()


tmc_mid_assign_resources = {
  "interface": "https://schema.skao.int/ska-tmc-assignresources/2.0",
  "transaction_id": "txn-local-20220526-0001",
  "subarray_id": 1,
  "dish": {
    "receptor_ids": [
      "0001",
      "0002",
      "0003",
      "0004"
    ]
  },
  "sdp": {
    "interface": "https://schema.skao.int/ska-sdp-assignres/0.3",
    "eb_id": "eb-mvp01-20200325-09059",
    "max_length": 100.0,
    "scan_types": [
      {
        "scan_type_id": "science_A",
        "reference_frame": "ICRS",
        "ra": "02:42:40.771",
        "dec": "-00:00:47.84",
        "channels": [
          {
            "count": 744,
            "start": 0,
            "stride": 2,
            "freq_min": 350000000.0,
            "freq_max": 368000000.0,
            "link_map": [
              [
                0,
                0
              ],
              [
                200,
                1
              ],
              [
                744,
                2
              ],
              [
                944,
                3
              ]
            ]
          },
          {
            "count": 744,
            "start": 2000,
            "stride": 1,
            "freq_min": 360000000.0,
            "freq_max": 368000000.0,
            "link_map": [
              [
                2000,
                4
              ],
              [
                2200,
                5
              ]
            ]
          }
        ]
      },
      {
        "scan_type_id": "calibration_B",
        "reference_frame": "ICRS",
        "ra": "12:29:06.699",
        "dec": "02:03:08.598",
        "channels": [
          {
            "count": 744,
            "start": 0,
            "stride": 2,
            "freq_min": 350000000.0,
            "freq_max": 368000000.0,
            "link_map": [
              [
                0,
                0
              ],
              [
                200,
                1
              ],
              [
                744,
                2
              ],
              [
                944,
                3
              ]
            ]
          },
          {
            "count": 744,
            "start": 2000,
            "stride": 1,
            "freq_min": 360000000.0,
            "freq_max": 368000000.0,
            "link_map": [
              [
                2000,
                4
              ],
              [
                2200,
                5
              ]
            ]
          }
        ]
      }
    ],
    "processing_blocks": [
      {
        "pb_id": "pb-mvp01-20200325-09059",
        "workflow": {
          "kind": "realtime",
          "name": "test_receive_addresses",
          "version": "0.3.6"
        },
        "parameters": {
          
        }
      }
    ]
  }
}

tmc_mid_release_resources = {
    "interface": "https://schema.skao.int/ska-tmc-releaseresources/2.0",
    "transaction_id": "txn-local-20210203-0001",
    "subarray_id": 1,
    "release_all": True,
    "receptor_ids": []
}
