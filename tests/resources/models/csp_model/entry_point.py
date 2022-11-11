"""Domain logic for the csp."""
import json
import logging
import os
from time import sleep
from typing import List, Union

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import base
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    MessageBoardBuilder,
)
from ska_ser_skallop.utils.singleton import Memo

from ..obsconfig.config import Observation


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
        self.csp_controller.command_inout("On", [])

    def set_wait_for_do(self) -> Union[MessageBoardBuilder, None]:
        """Domain logic specifying what needs to be waited for before startup of csp is done."""
        brd = get_message_board_builder()
        brd.set_waiting_on(self._tel.csp.controller).for_attribute(
            "state"
        ).to_become_equal_to("ON", ignore_first=False)
        # Note we do not wait for controller on skalow as it seems it does not change state
        # subarrays
        if self._tel.skamid:
            # we wait for cbf vccs to be in proper initialised state
            brd.set_waiting_on(self._tel.csp.cbf.controller).for_attribute(
                "reportVccState"
            ).to_become_equal_to(["[0, 0, 0, 0]", "[0 0 0 0]"], ignore_first=False)
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
        # controller
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
        """Domain logic for switching the csp off."""
        self.csp_controller.command_inout("Off", [])


class CspAsignResourcesStep(base.AssignResourcesStep, LogEnabled):
    """Implementation of Assign Resources Step for CSP."""

    def __init__(self, observation: Observation) -> None:
        """Init object."""
        super().__init__()
        self.observation = observation
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
            subarray.set_timeout_millis(6000)
            subarray.command_inout("AssignResources", csp_low_configuration)
        elif self._tel.skamid:
            subarray_name = self._tel.skamid.csp.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            config = self.observation.generate_assign_resources_config().as_json
            self._log(f"commanding {subarray_name} with AssignResources: {config} ")
            subarray.set_timeout_millis(6000)
            subarray.command_inout("AssignResources", config)

    def undo(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in csp.

        This implments the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        subarray_name = self._tel.csp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"commanding {subarray_name} with ReleaseAllResources")
        subarray.set_timeout_millis(6000)
        subarray.command_inout("ReleaseAllResources")

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
        subarray_name = self._tel.csp.subarray(sub_array_id)
        builder.set_waiting_on(subarray_name).for_attribute(
            "obsState"
        ).to_become_equal_to("EMPTY")

        return builder


class CspConfigureStep(base.ConfigureStep, LogEnabled):
    """Implementation of Configure Scan Step for CSP."""

    def __init__(self, observation: Observation) -> None:
        """Init object."""
        super().__init__()
        self.observation = observation
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
        # scan duration needs to be a memorised for future objects that mnay require it
        Memo(scan_duration=duration)
        if self._tel.skalow:
            subarray_name = self._tel.skalow.csp.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            cbf_low_configuration = json.dumps(csp_low_configure_scan)
            self._log(
                f"commanding {subarray_name} with Configure: {cbf_low_configuration} "
            )
            subarray.set_timeout_millis(6000)
            subarray.command_inout("Configure", cbf_low_configuration)
        elif self._tel.skamid:
            subarray_name = self._tel.skamid.csp.subarray(sub_array_id)
            subarray = con_config.get_device_proxy(subarray_name)
            csp_mid_configuration = self.observation.generate_csp_scan_config().as_json
            self._log(
                f"commanding {subarray_name} with Configure: {csp_mid_configuration} "
            )
            subarray.set_timeout_millis(6000)
            subarray.command_inout("Configure", csp_mid_configuration)

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

    def __init__(self, observation: Observation) -> None:
        """Init object."""
        super().__init__()
        self.observation = observation
        self._tel = names.TEL()

    def do(self, sub_array_id: int):
        """Domain logic for running a scan on subarray in csp.

        This implments the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        if self._tel.skalow:
            scan_config_arg = json.dumps(csp_low_scan)
        elif self._tel.skamid:
            scan_config_arg = self.observation.generate_run_scan_conf().as_json
        scan_duration = Memo().get("scan_duration")
        self._tel = names.TEL()
        subarray_name = self._tel.csp.subarray(sub_array_id)
        subarray = con_config.get_device_proxy(subarray_name)
        self._log(f"Commanding {subarray_name} to Scan with {scan_config_arg}")
        try:
            subarray.command_inout("Scan", scan_config_arg)
            sleep(scan_duration)
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
        ).to_become_equal_to("SCANNING", ignore_first=True)
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


class CSPEntryPoint(CompositeEntryPoint):
    """Derived Entrypoint scoped to SDP element."""

    nr_of_subarrays = 2

    def __init__(self, observation: Observation | None = None) -> None:
        """Init Object"""
        super().__init__()
        if observation is None:
            observation = Observation()
        self.observation = observation
        self.set_online_step = CSPSetOnlineStep(self.nr_of_subarrays)
        self.start_up_step = StartUpStep(self.nr_of_subarrays)
        self.assign_resources_step = CspAsignResourcesStep(observation)
        self.configure_scan_step = CspConfigureStep(observation)
        self.scan_step = CspScanStep(observation)


csp_mid_assign_resources_template = {
    "interface": "https://schema.skao.int/ska-csp-configure/2.0",
    "subarray_id": 1,
    "dish": {"receptor_ids": ["001", "002"]},
}

csp_mid_configure_scan_template = {
    "interface": "https://schema.skao.int/ska-csp-configure/2.0",
    "subarray": {"subarray_name": "science period 23"},
    "common": {
        "config_id": "sbi-mvp01-20200325-00001-science_A",
        "frequency_band": "1",
        "subarray_id": "1",
    },
    "cbf": {
        "delay_model_subscription_point": "sys/tg_test/1/string_scalar",
        "fsp": [
            {
                "fsp_id": 1,
                "function_mode": "CORR",
                "frequency_slice_id": 1,
                "integration_factor": 1,
                "zoom_factor": 0,
                "channel_averaging_map": [[0, 2], [744, 0]],
                "channel_offset": 0,
                "output_link_map": [[0, 0], [200, 1]],
            },
            {
                "fsp_id": 2,
                "function_mode": "CORR",
                "frequency_slice_id": 2,
                "integration_factor": 1,
                "zoom_factor": 1,
                "zoom_window_tuning": 650000,
                "channel_averaging_map": [[0, 2], [744, 0]],
                "channel_offset": 744,
                "output_link_map": [[0, 4], [200, 5]],
                "output_host": [[0, "192.168.1.1"]],
                "output_port": [[0, 9744, 1]],
            },
        ],
        "vlbi": {},
    },
    "pss": {},
    "pst": {},
    "pointing": {
        "target": {
            "system": "ICRS",
            "target_name": "Polaris Australis",
            "ra": "21:08:47.92",
            "dec": "-88:57:22.9",
        }
    },
}

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
                "pst_beams": [{"pst_beam_id": 1}],
            }
        ],
    },
}

csp_low_configure_scan = {
    "interface": "https://schema.skao.int/ska-csp-configure/2.0",
    "subarray": {"subarray_name": "science period 23"},
    "common": {
        "config_id": "sbi-mvp01-20200325-00001-science_A",
        "subarray_id": 1,
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
                "zooms": [
                    {
                        "zoom_id": 1,
                        "zoom_centre_hz": 90000000,
                        "zoom_resolution_hz": 14,
                        "zoom_channels": 2000,
                        "zoom_dest": {
                            "dest_ip": "10.0.5.1",
                            "dest_mac": "02:00:00:00:05:01",
                        },
                    },
                    {
                        "zoom_id": 2,
                        "zoom_centre_hz": 120000000,
                        "zoom_resolution_hz": 30,
                        "zoom_channels": 2000,
                        "zoom_dest": {
                            "dest_ip": "10.0.5.2",
                            "dest_mac": "02:00:00:00:05:02",
                        },
                    },
                ],
            },
            {
                "station_beam_id": 2,
                "station_delay_src": "tango://host:port/domain/family/member",
                "visibility_dest": [
                    {"dest_ip": "10.0.2.2", "dest_mac": "02:00:00:00:02:02"}
                ],
                "zooms": [
                    {
                        "zoom_id": 3,
                        "zoom_centre_hz": 190000000,
                        "zoom_resolution_hz": 60,
                        "zoom_channels": 2000,
                        "zoom_dest": {
                            "dest_ip": "10.0.5.3",
                            "dest_mac": "02:00:00:00:05:03",
                        },
                    }
                ],
            },
        ],
    },
}

csp_low_scan = {
    "common": {"subarray_id": 1},
    "lowcbf": {
        "scan_id": 987654321,
        "unix_epoch_seconds": 1616971738,
        "timestamp_ns": 987654321,
        "packet_offset": 123456789,
        "scan_seconds": 30,
    },
}
