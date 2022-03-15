"""Domain logic for the csp."""
import logging
from typing import Union, List
import os
import json
from time import sleep

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    MessageBoardBuilder,
)
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.event_handling.builders import get_message_board_builder


logger = logging.getLogger(__name__)

# scan duration needs to be a singleton in order to keep track of scan
# settings between configure scan and run scan
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
    """Implementation of Startup step for CSP"""

    def __init__(self, nr_of_subarrays: int) -> None:
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays
        self.csp_controller = con_config.get_device_proxy(self._tel.csp.controller)

    def do(self):
        """Domain logic for starting up a telescope on the interface to csp.

        This implments the set_telescope_to_running method on the entry_point.
        """
        if self._tel.skamid:
            # mid csp is already on but requires subarray sto be switched on
            for index in range(1, self.nr_of_subarrays + 1):
                subarray = con_config.get_device_proxy(self._tel.csp.subarray(index))
                subarray.command_inout("On")
        else:
            self.csp_controller.command_inout("On")

    def set_wait_for_do(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic specifying what needs to be waited for before startup of csp is done."""
        brd = get_message_board_builder()

        brd.set_waiting_on(self._tel.csp.controller).for_attribute(
            "state"
        ).to_become_equal_to("ON", ignore_first=False)
        # subarrays
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.csp.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("ON", ignore_first=False)
        return brd

    def set_wait_for_doing(self) -> Union[MessageBoardBuilder, None]:
        """Not implemented."""
        raise NotImplementedError()

    def set_wait_for_undo(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic for what needs to be waited for switching the csp off."""
        brd = get_message_board_builder()
        if self._tel.skalow:
            # mid csp remains on
            brd.set_waiting_on(self._tel.csp.controller).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
        # subarrays
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.csp.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
        return brd

    def undo(self):
        """Domain logic for switching the sdp off."""
        if self._tel.skamid:
            # mid csp is already on but requires subarray sto be switched on
            for index in range(1, self.nr_of_subarrays + 1):
                subarray = con_config.get_device_proxy(self._tel.csp.subarray(index))
                subarray.command_inout("Off")
        else:
            self.csp_controller.command_inout("Off")


class CspAsignResourcesStep(base.AssignResourcesStep, LogEnabled):
    """Implementation of Assign Resources Step for CSP."""

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
        """Domain logic for assigning resources to a subarray in csp.

        This implments the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration paramaters
        :param sb_id: a generic ide to identify a sb to assign resources
        """
        if self._tel.skalow:
            subarray_name = self._tel.skalow.csp.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            csp_low_configuration = json.dumps(csp_low_assign_resources)
            self._log(
                f"commanding {subarray_name} with AssignResources: {csp_low_configuration} "
            )
            subarray.command_inout("AssignResources", csp_low_configuration)
        else:
            raise NotImplementedError()

    def undo(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in csp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        if self._tel.skalow:
            subarray_name = self._tel.skalow.csp.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"commanding {subarray_name} with ReleaseAllResources")
            subarray.command_inout("ReleaseAllResources")
        else:
            raise NotImplementedError()

    def set_wait_for_do(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        builder = get_message_board_builder()
        self._tel = names.TEL()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")

        return builder

    def set_wait_for_doing(self, sub_array_id: int) -> MessageBoardBuilder:
        """Not implemented."""
        raise NotImplementedError()

    def set_wait_for_undo(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        builder = get_message_board_builder()
        self._tel = names.TEL()
        if self._tel.skamid:
            subarray_name = self._tel.skamid.csp.subarray(sub_array_id)
            builder.set_waiting_on(subarray_name).for_attribute(
                "obsState"
            ).to_become_equal_to("EMPTY")

        return builder


class CspConfigureStep(base.ConfigureStep, LogEnabled):
    """Implementation of Configure Scan Step for CSP."""

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
        """Domain logic for configuring a scan on subarray in csp.

        This implments the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration paramaters
        :param sb_id: a generic ide to identify a sb to assign resources
        """
        # scan duration needs to be a singleton in order to keep track of scan
        # settings between configure scan and run scan
        global SCAN_DURATION  # pylint: disable=global-statement
        SCAN_DURATION = duration
        if self._tel.skalow:
            subarray_name = self._tel.skalow.csp.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            cbf_low_configuration = json.dumps(csp_low_configure_scan)
            self._log(
                f"commanding {subarray_name} with Configure: {cbf_low_configuration} "
            )
            subarray.command_inout("Configure", cbf_low_configuration)
        else:
            raise NotImplementedError()

    def undo(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in csp.

        This implments the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with command GoToIdle")
        subarray.command_inout("GoToIdle")

    def set_wait_for_do(
        self, sub_array_id: int, receptors: List[int]
    ) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for configuring a scan is done.

        :param sub_array_id: The index id of the subarray to control
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.subarray(sub_array_id)
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
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("IDLE")
        return builder


class CspScanStep(base.ScanStep, LogEnabled):

    """Implementation of Scan Step for CBF."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()

    def do(self, sub_array_id: int):
        """Domain logic for running a scan on subarray in csp.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        scan_config_arg = json.dumps({"scan_id": 1})
        self._tel = names.TEL()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"Commanding {subarray_name} to Scan with {scan_config_arg}")
        try:
            subarray.command_inout("Scan", scan_config_arg)
            sleep(SCAN_DURATION)
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
        subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("SCANNING")
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
        if self._tel.skalow:
            controller_name = self._tel.skalow.csp.controller
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
        if self._tel.skalow:
            controller_name = self._tel.skalow.csp.controller
            builder = get_message_board_builder()
            builder.set_waiting_on(controller_name).for_attribute(
                "adminMode"
            ).to_become_equal_to("ONLINE", ignore_first=False)
            for index in range(1, self.nr_of_subarrays + 1):
                subarray = self._tel.csp.subarray(index)
                builder.set_waiting_on(subarray).for_attribute(
                    "adminMode"
                ).to_become_equal_to("ONLINE", ignore_first=False)
            return builder
        return None

    def undo(self):
        """Domain logic for setting devices in csp to offline."""
        if self._tel.skalow:
            controller_name = self._tel.skalow.csp.controller
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
        if self._tel.skalow:
            controller_name = self._tel.skalow.csp.controller
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
        return None

    def set_wait_for_doing(self) -> MessageBoardBuilder:
        """Not implemented."""
        raise NotImplementedError()


class CSPEntryPoint(CompositeEntryPoint):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2

    def __init__(self) -> None:
        """Init Object"""
        super().__init__()
        self.set_online_step = CSPSetOnlineStep(self.nr_of_subarrays)
        self.start_up_step = StartUpStep(self.nr_of_subarrays)
        self.assign_resources_step = CspAsignResourcesStep()
        self.configure_scan_step = CspConfigureStep()
        self.scan_step = CspScanStep()


csp_low_assign_resources = {
    "interface": "https://schema.skao.int/ska-low-csp-assignresources/2.0",
    "common": {"subarray_id": 1},
    "lowcbf": {
        "stations": [
            {"station_id": 1, "sub_station_id": 1},
            {"station_id": 3, "sub_station_id": 1},
            {"station_id": 3, "sub_station_id": 2},
        ],
        "station_beams": [
            {
                "station_beam_id": 1,
                "channels": [1, 2, 3, 4, 5, 6, 7, 8],
                "pst_beams": [{"pst_beam_id": 1}, {"pst_beam_id": 2}],
            },
            {
                "station_beam_id": 2,
                "channels": [9, 10, 11, 12, 13, 14, 15],
                "pst_beams": [{"pst_beam_id": 3}],
            },
        ],
    },
}

csp_low_configure_scan = {
    "interface": "https://schema.skao.int/ska-csp-configure/2.0",
    "id": 1,
    "scanId": 1,
    "stationType": 0,
    "common": {
        "subarray_id": 1,
        "config_id": "sbi-mvp01-20200325-00001-science_A",
    },
    "lowcbf": {
        "jones_source": "tango://host:port/domain/family/member",
        "station_beams": [
            {
                "station_beam_id": 1,
                "station_delay_src": "tango://host:port/domain/family/member",
                "visibility_dest": [
                    {"dest_ip": "10.0.2.1", "dest_mac": "02:00:00:00:02:01"}
                ],
                "pst_beams": [
                    {
                        "pst_beam_id": 1,
                        "pst_beam_delay_src": "tango://host:port/domain/family/member",
                        "pst_beam_dest": [
                            {
                                "dest_ip": "10.0.3.1",
                                "dest_mac": "02:00:00:00:03:01",
                                "channels": 200,
                            },
                            {
                                "dest_ip": "10.0.3.2",
                                "dest_mac": "02:00:00:00:03:02",
                                "channels": 500,
                            },
                        ],
                    },
                    {
                        "pst_beam_id": 2,
                        "pst_beam_delay_src": "tango://host:port/domain/family/member",
                        "pst_beam_dest": [
                            {
                                "dest_ip": "10.0.3.3",
                                "dest_mac": "02:00:00:00:03:03",
                                "channels": 200,
                            },
                            {
                                "dest_ip": "10.0.3.4",
                                "dest_mac": "02:00:00:00:03:04",
                                "channels": 500,
                            },
                        ],
                    },
                ],
            },
            {
                "station_beam_id": 2,
                "station_delay_src": "tango://host:port/domain/family/member",
                "visibility_dest": [
                    {"dest_ip": "10.0.3.3", "dest_mac": "02:00:00:00:03:03"}
                ],
                "pst_beams": [
                    {
                        "pst_beam_id": 3,
                        "pst_beam_delay_src": "tango://host:port/domain/family/member",
                        "pst_beam_dest": [
                            {
                                "dest_ip": "10.0.2.5",
                                "dest_mac": "02:00:00:00:02:05",
                                "channels": 200,
                            },
                            {
                                "dest_ip": "10.0.2.6",
                                "dest_mac": "02:00:00:00:02:06",
                                "channels": 500,
                            },
                        ],
                    }
                ],
            },
        ],
    },
}
