"""Domain logic for the cbf."""
import logging
from typing import Union, List
import os
import json
from time import sleep

from ska_ser_skallop.mvp_control.describing import mvp_names as names
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
        self.cbf_controller = con_config.get_device_proxy(self._tel.csp.cbf.controller)

    def do(self):
        """Domain logic for starting up a telescope on the interface to CBF.

        This implments the set_telescope_to_running method on the entry_point.
        """
        self.cbf_controller.command_inout("On")
        if self._tel.skalow:
            # cbf low needs to start up subarrays individually
            for index in range(1, self.nr_of_subarrays + 1):
                subarray = con_config.get_device_proxy(
                    self._tel.csp.cbf.subarray(index)
                )
                subarray.command_inout(("On"))

    def set_wait_for_do(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic specifying what needs to be waited for before startup of cbf is done."""
        brd = get_message_board_builder()

        brd.set_waiting_on(self._tel.csp.cbf.controller).for_attribute(
            "state"
        ).to_become_equal_to("ON", ignore_first=False)
        # subarrays
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.csp.cbf.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("ON", ignore_first=False)
        return brd

    def set_wait_for_doing(self) -> Union[MessageBoardBuilder, None]:
        """Not implemented."""
        raise NotImplementedError()

    def set_wait_for_undo(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic for what needs to be waited for switching the sdp off."""
        brd = get_message_board_builder()
        brd.set_waiting_on(self._tel.csp.cbf.controller).for_attribute(
            "state"
        ).to_become_equal_to("OFF", ignore_first=False)
        # subarrays
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.csp.cbf.subarray(index)).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
        return brd

    def undo(self):
        """Domain logic for switching the sdp off."""
        self.cbf_controller.command_inout("Off")
        if self._tel.skalow:
            for index in range(1, self.nr_of_subarrays + 1):
                subarray_name = self._tel.csp.cbf.subarray(index)
                subarray = con_config.get_device_proxy(subarray_name)
                self._log(f"commanding {subarray_name} to Off")
                subarray.command_inout(("Off"))


class CbfAsignResourcesStep(base.AssignResourcesStep, LogEnabled):
    """Implementation of Assign Resources Step for SDP."""

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
        """Domain logic for assigning resources to a subarray in cbf.

        This implments the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration paramaters
        :param sb_id: a generic ide to identify a sb to assign resources
        """
        if self._tel.skamid:
            subarray_name = self._tel.skamid.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"commanding {subarray_name} with AddReceptors: {dish_ids} ")
            subarray.command_inout("AddReceptors", dish_ids)
        elif self._tel.skalow:
            subarray_name = self._tel.skalow.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            cbf_low_configuration = json.dumps(cbf_low_assign_resources)
            self._log(
                f"commanding {subarray_name} with AssignResources: {cbf_low_configuration} "
            )
            subarray.command_inout("AssignResources", cbf_low_configuration)

    def undo(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in sdp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        if self._tel.skamid:
            subarray_name = self._tel.skamid.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"commanding {subarray_name} with RemoveAllReceptors")
            subarray.command_inout("RemoveAllReceptors")
        if self._tel.skalow:
            subarray_name = self._tel.skalow.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"commanding {subarray_name} with ReleaseAllResources")
            subarray.command_inout("ReleaseAllResources")

    def set_wait_for_do(self, sub_array_id: int) -> MessageBoardBuilder:
        """Domain logic specifying what needs to be waited for subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
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
        if self._tel.skamid:
            subarray_name = self._tel.skamid.csp.cbf.subarray(sub_array_id)
            builder.set_waiting_on(subarray_name).for_attribute(
                "obsState"
            ).to_become_equal_to("EMPTY")

        return builder


class CbfConfigureStep(base.ConfigureStep, LogEnabled):
    """Implementation of Configure Scan Step for CBF."""

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
        """Domain logic for configuring a scan on subarray in cbf.

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
        if self._tel.skamid:
            subarray_name = self._tel.skamid.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            standard_configuration = conf.generate_standard_conf(
                sub_array_id, sb_id, duration
            )
            cbf_config = json.loads(standard_configuration)["csp"]["cbf"]
            common = json.loads(standard_configuration)["csp"]["common"]
            cbf_config["common"] = common
            cbf_standard_configuration = json.dumps(
                {"cbf": cbf_config, "common": common}
            )
            self._log(
                f"commanding {subarray_name} with ConfigureScan: {cbf_standard_configuration} "
            )
            subarray.command_inout("ConfigureScan", cbf_standard_configuration)
        if self._tel.skalow:
            subarray_name = self._tel.skalow.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            cbf_low_configuration = json.dumps(cbf_low_configure_scan)
            self._log(
                f"commanding {subarray_name} with ConfigureScan: {cbf_low_configuration} "
            )
            subarray.command_inout("ConfigureScan", cbf_low_configuration)

    def undo(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in cbf.

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
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
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


class CbfScanStep(base.ScanStep, LogEnabled):

    """Implementation of Scan Step for CBF."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()

    def do(self, sub_array_id: int):
        """Domain logic for running a scan on subarray in cbf.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        if self._tel.skalow:
            scan_config_arg = json.dumps(cbf_low_start_scan)
            self._log(f"Commanding {subarray_name} to Scan with {scan_config_arg}")
            try:
                subarray.command_inout("Scan", scan_config_arg)
            except Exception as exception:
                logger.exception(exception)
                raise exception
        else:
            scan_config_arg = json.dumps({"scan_id": 1})
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
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
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


class CBFEntryPoint(CompositeEntryPoint):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2

    def __init__(self) -> None:
        """Init Object"""
        super().__init__()
        self.set_online_step = NoOpStep()
        self.start_up_step = StartUpStep(self.nr_of_subarrays)
        self.assign_resources_step = CbfAsignResourcesStep()
        self.configure_scan_step = CbfConfigureStep()
        self.scan_step = CbfScanStep()


cbf_low_start_scan = {
    "common": {"subarray_id": 1},
    "lowcbf": {
        "scan_id": 987654321,
        "unix_epoch_seconds": 1616971738,
        "timestamp_ns": 987654321,
        "packet_offset": 123456789,
        "scan_seconds": 2,
    },
}

cbf_low_assign_resources = {
    "common": {"subarrayID": 1},
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

cbf_low_configure_scan = {
    "id": 1,
    "scanId": 1,
    "stationType": 0,
    "common": {"id": 1},
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
                    }
                ],
            },
            {
                "station_beam_id": 2,
                "station_delay_src": "tango://host:port/domain/family/member",
                "visibility_dest": [
                    {"dest_ip": "10.0.3.3", "dest_mac": "02:00:00:00:03:03"}
                ],
                "pst_beams": [],
            },
        ],
    },
}
