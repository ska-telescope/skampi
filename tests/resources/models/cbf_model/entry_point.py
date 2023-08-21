"""Domain logic for the cbf."""
import json
import logging
import os
from time import sleep
from typing import List

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from ska_ser_skallop.mvp_control.configuration import configuration as conf
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    MessageBoardBuilder,
)

from ..mvp_model.object_with_obsconfig import HasObservation

logger = logging.getLogger(__name__)

# scan duration needs to be a singleton in order to keep track of scan
# settings between configure scan and run scan
SCAN_DURATION = 4


class LogEnabled:
    """class that allows for logging if set by env var"""

    def __init__(self) -> None:
        self._live_logging = bool(os.getenv("DEBUG_ENTRYPOINT"))
        self._tel = names.TEL()

    def _log(self, mssage: str):
        if self._live_logging:
            logger.info(mssage)


class StartUpStep(base.StartUpStep, LogEnabled):
    """Implementation of Startup step for CSP"""

    def __init__(self, nr_of_subarrays: int) -> None:
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays
        self.cbf_controller = con_config.get_device_proxy(self._tel.csp.cbf.controller)

    def do_startup(self):
        """Domain logic for starting up a telescope on the interface to CBF.

        This implments the set_telescope_to_running method on the entry_point.
        """
        self.cbf_controller.command_inout("On")
        if self._tel.skalow:
            # cbf low needs to start up subarrays individually
            for index in range(1, self.nr_of_subarrays + 1):
                subarray = con_config.get_device_proxy(self._tel.csp.cbf.subarray(index))
                subarray.command_inout("On")

    def set_wait_for_do_startup(self) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited
        for before startup of cbf is done.
        :return: brd
        """
        brd = get_message_board_builder()

        brd.set_waiting_on(self._tel.csp.cbf.controller).for_attribute("state").to_become_equal_to(
            "ON", ignore_first=False
        )
        # subarrays
        for index in range(1, self.nr_of_subarrays + 1):
            brd.set_waiting_on(self._tel.csp.cbf.subarray(index)).for_attribute(
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
        if self._tel.skamid:
            brd.set_waiting_on(self._tel.csp.cbf.controller).for_attribute(
                "state"
            ).to_become_equal_to("OFF", ignore_first=False)
            # subarrays
            for index in range(1, self.nr_of_subarrays + 1):
                brd.set_waiting_on(self._tel.csp.cbf.subarray(index)).for_attribute(
                    "state"
                ).to_become_equal_to("OFF", ignore_first=False)
        return brd

    def undo_startup(self):
        """Domain logic for switching the cbf off."""
        if self._tel.skamid:
            self.cbf_controller.command_inout("Off")
            if self._tel.skalow:
                for index in range(1, self.nr_of_subarrays + 1):
                    subarray_name = self._tel.csp.cbf.subarray(index)
                    subarray = con_config.get_device_proxy(subarray_name)
                    self._log(f"commanding {subarray_name} to Off")
                    subarray.command_inout("Off")
        # we skip tests if telescope low


class CbfAsignResourcesStep(base.AssignResourcesStep, LogEnabled, HasObservation):
    """Implementation of Assign Resources Step for cbf."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        HasObservation.__init__(self)

    def do_assign_resources(
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
            config = self.observation.dish_allocation.receptor_ids
            subarray_name = self._tel.skamid.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"commanding {subarray_name} with AddReceptors: {config} ")
            subarray.command_inout("AddReceptors", config)
        elif self._tel.skalow:
            subarray_name = self._tel.skalow.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            cbf_low_configuration = json.dumps(cbf_low_assign_resources)
            self._log(
                f"commanding {subarray_name} with AssignResources:" f" {cbf_low_configuration} "
            )
            subarray.command_inout("AssignResources", cbf_low_configuration)

    def undo_assign_resources(self, sub_array_id: int):
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

    def set_wait_for_do_assign_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for
        subarray assign resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "IDLE", ignore_first=False
        )

        return builder

    def set_wait_for_doing_assign_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Not implemented.

        :param sub_array_id: The index id of the subarray to control
        :raises NotImplementedError: Raises the error
                when implementation is not done.
        """
        raise NotImplementedError()

    def set_wait_for_undo_resources(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for
        subarray releasing resources is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        if self._tel.skamid:
            subarray_name = self._tel.skamid.csp.cbf.subarray(sub_array_id)
            builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
                "EMPTY", ignore_first=False
            )

        return builder


class CbfConfigureStep(base.ConfigureStep, LogEnabled, HasObservation):
    """Implementation of Configure Scan Step for CBF."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()

    def do_configure(
        self,
        sub_array_id: int,
        configuration: types.ScanConfiguration,
        sb_id: str,
        duration: float,
    ):
        """Domain logic for configuring a scan on subarray in cbf.

        This implments the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param configuration: The assign resources configuration paramaters
        :param sb_id: a generic ide to identify a sb to assign resources
        :param duration: duration for scan
        """
        # scan duration needs to be a singleton in order to keep track of scan
        # settings between configure scan and run scan
        global SCAN_DURATION  # pylint: disable=global-statement
        SCAN_DURATION = duration
        if self._tel.skamid:
            subarray_name = self._tel.skamid.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            standard_configuration = conf.generate_standard_conf(sub_array_id, sb_id, duration)
            cbf_config = json.loads(standard_configuration)["csp"]["cbf"]
            common = json.loads(standard_configuration)["csp"]["common"]
            cbf_config["common"] = common
            cbf_standard_configuration = json.dumps({"cbf": cbf_config, "common": common})
            self._log(
                f"commanding {subarray_name} with ConfigureScan:" f" {cbf_standard_configuration} "
            )
            subarray.command_inout("ConfigureScan", cbf_standard_configuration)
        if self._tel.skalow:
            subarray_name = self._tel.skalow.csp.cbf.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            cbf_low_configuration = json.dumps(cbf_low_configure_scan)
            self._log(
                f"commanding {subarray_name} with ConfigureScan:" f" {cbf_low_configuration} "
            )
            subarray.command_inout("ConfigureScan", cbf_low_configuration)

    def undo_configure(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in cbf.

        This implments the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with command GoToIdle")
        subarray.command_inout("GoToIdle")

    def set_wait_for_do_configure(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited
        for configuring a scan is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to("READY")
        return builder

    def set_wait_for_doing_configure(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Not implemented.

        :param sub_array_id: The index id of the subarray to control
        :raises NotImplementedError: Raises the error when
                implementation is not done.
        """
        raise NotImplementedError()

    def set_wait_for_undo_configure(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifying what needs to be waited for
        subarray clear scan config is done.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to("IDLE")
        return builder


class CbfScanStep(base.ScanStep, LogEnabled):

    """Implementation of Scan Step for CBF."""

    def __init__(self) -> None:
        """Init object."""
        super().__init__()
        self._tel = names.TEL()

    def do_scan(self, sub_array_id: int):
        """Domain logic for running a scan on subarray in cbf.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control

        :raises Exception: Raise exception if the scan command fails
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

    def set_wait_for_do_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        This is a no-op as there is no scanning command

        :param sub_array_id: The index id of the subarray to control
        :return: message board builder
        """
        return get_message_board_builder()

    def undo_scan(self, sub_array_id: int):
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        """

    def set_wait_for_doing_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """
        Domain logic specifyig what needs to be done for waiting
        for subarray to be scanning.

        :param sub_array_id: The index id of the subarray to control
        :return: builder
        """
        builder = get_message_board_builder()
        subarray_name = self._tel.csp.cbf.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute("obsState").to_become_equal_to(
            "SCANNING"
        )
        return builder

    def set_wait_for_undo_scan(self, sub_array_id: int) -> MessageBoardBuilder:
        """This is a no-op as no undo for scan is needed

        :param sub_array_id: The index id of the subarray to control
        :return: None
        """
        return get_message_board_builder()


class CBFSetOnlineStep(base.SetOnlineStep, LogEnabled):
    """Domain logic for setting csp to online"""

    def __init__(self, nr_of_subarrays: int) -> None:
        super().__init__()
        self.nr_of_subarrays = nr_of_subarrays

    def do_set_online(self):
        """Domain logic for setting devices in csp to online."""
        controller_name = self._tel.csp.cbf.controller
        controller = con_config.get_device_proxy(controller_name)
        self._log(f"Setting adminMode for {controller_name} to '0' (ONLINE)")
        controller.write_attribute("adminMode", 0)
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.csp.cbf.subarray(index)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"Setting adminMode for {subarray_name} to '0' (ONLINE)")
            subarray.write_attribute("adminMode", 0)

    def set_wait_for_do_set_online(self) -> MessageBoardBuilder:
        """
        Domain logic for waiting for setting to online to be complete.

        :return: builder
        """
        controller_name = self._tel.csp.cbf.controller
        builder = get_message_board_builder()
        builder.set_waiting_on(controller_name).for_attribute("adminMode").to_become_equal_to(
            "ONLINE", ignore_first=False
        )
        builder.set_waiting_on(controller_name).for_attribute("state").to_become_equal_to(
            ["OFF", "ON"], ignore_first=False
        )
        for index in range(1, self.nr_of_subarrays + 1):
            subarray = self._tel.csp.cbf.subarray(index)
            builder.set_waiting_on(subarray).for_attribute("adminMode").to_become_equal_to(
                "ONLINE", ignore_first=False
            )
            builder.set_waiting_on(subarray).for_attribute("state").to_become_equal_to(
                ["OFF", "ON"], ignore_first=False
            )
        return builder

    def undo_set_online(self):
        """Domain logic for setting devices in csp to offline."""
        controller_name = self._tel.csp.cbf.controller
        controller = con_config.get_device_proxy(controller_name)
        self._log(f"Setting adminMode for {controller_name} to '1' (OFFLINE)")
        controller.write_attribute("adminMode", 1)
        for index in range(1, self.nr_of_subarrays + 1):
            subarray_name = self._tel.csp.cbf.subarray(index)
            subarray = con_config.get_device_proxy(subarray_name)
            self._log(f"Setting adminMode for {subarray_name} to '1' (OFFLINE)")
            subarray.write_attribute("adminMode", 1)

    def set_wait_for_undo_set_online(self) -> MessageBoardBuilder:
        """
        Domain logic for waiting for setting to offline to be complete.

        :return: builder
        """
        controller_name = self._tel.csp.cbf.controller
        builder = get_message_board_builder()
        builder.set_waiting_on(controller_name).for_attribute("adminMode").to_become_equal_to(
            "OFFLINE", ignore_first=False
        )
        for index in range(1, self.nr_of_subarrays + 1):
            subarray = self._tel.csp.cbf.subarray(index)
            builder.set_waiting_on(subarray).for_attribute("adminMode").to_become_equal_to(
                "OFFLINE", ignore_first=False
            )
        return builder

    def set_wait_for_doing_set_online(self) -> MessageBoardBuilder:
        """
        Not implemented.

        :raises NotImplementedError: Raises the error when
                implementation is not done.
        """
        raise NotImplementedError()


class CBFEntryPoint(CompositeEntryPoint, HasObservation):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2

    def __init__(self) -> None:
        """Init Object"""
        super().__init__()
        self.set_online_step = CBFSetOnlineStep(self.nr_of_subarrays)
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
        "resources": [
            {
                "device": "fsp_01",
                "shared": True,
                "fw_image": "pst",
                "fw_mode": "unused",
            },
            {
                "device": "p4_01",
                "shared": True,
                "fw_image": "p4.bin",
                "fw_mode": "p4",
            },
        ]
    },
}


cbf_low_release_resources = (
    {
        "lowcbf": {
            "resources": [
                {"device": "device"},
            ]
        },
    },
)

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
                "visibility_dest": [{"dest_ip": "10.0.2.1", "dest_mac": "02:00:00:00:02:01"}],
                "pst_beams": [
                    {
                        "pst_beam_id": 1,
                        "pst_beam_delay_src": ("tango://host:port/domain/family/member"),
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
                "visibility_dest": [{"dest_ip": "10.0.3.3", "dest_mac": "02:00:00:00:03:03"}],
                "pst_beams": [],
            },
        ],
    },
}
