"""Domain logic for the cdp."""
import logging
import copy
from typing import Union, List
import json
from time import sleep

import copy
from ska_ser_skallop.utils.singleton import Memo
from ska_ser_skallop.mvp_control.configuration import types
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.entry_points.composite import (
    CompositeEntryPoint,
    NoOpStep,
    MessageBoardBuilder,
)
from ska_ser_skallop.event_handling.builders import get_message_board_builder
from ...csp_model.entry_point import (
    StartUpStep,
    CspAsignResourcesStep,
    CspConfigureStep,
    CspScanStep,
)

from ...obsconfig.config import Observation


logger = logging.getLogger(__name__)


class StartUpLnStep(StartUpStep):
    """Implementation of Startup step for CSP LN"""

    def __init__(self, nr_of_subarrays: int) -> None:
        super().__init__(nr_of_subarrays)
        self._csp_master_ln_name = self._tel.tm.csp_leaf_node  # type: ignore

    def do(self):
        """Domain logic for starting up a telescope on the interface to CSP LN.

        This implements the set_telescope_to_running method on the entry_point.
        """
        self._log(f"commanding {self._csp_master_ln_name} to On")
        csp_master_ln = con_config.get_device_proxy(self._csp_master_ln_name)  # type: ignore
        csp_master_ln.command_inout("On")

    def undo(self):
        """Domain logic for switching the CSP LN off."""
        self._log(f"commanding {self._csp_master_ln_name} to Off")
        csp_master_ln = con_config.get_device_proxy(self._csp_master_ln_name)  # type: ignore
        csp_master_ln.command_inout("Off")


class CspLnAssignResourcesStep(CspAsignResourcesStep):
    """Implementation of Assign Resources Step for CSP LN."""

    def do(
            self,
            sub_array_id: int,
            dish_ids: List[int],
            composition: types.Composition,  # pylint: disable=
            sb_id: str,
    ):
        """Domain logic for assigning resources to a subarray in csp LN.

        This implements the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration parameters
        :param sb_id: a generic id to identify a sb to assign resources
        """

        try:
            csp_subarray_ln_name = self._tel.tm.subarray(sub_array_id).csp_leaf_node  # type: ignore
            csp_subarray_ln = con_config.get_device_proxy(csp_subarray_ln_name)  # type: ignore
            if self._tel.skamid:
                config = self.observation.generate_assign_resources_config(sub_array_id).as_json
            elif self._tel.skalow:
                # TODO Low json from CDM is not available. Once it is available pull json from CDM
                config_json = copy.deepcopy(ASSIGN_RESOURCE_CSP_JSON_LOW)
                config = json.dumps(config_json)

            logger.info(f"commanding {csp_subarray_ln_name} with AssignResources: {config} ")
            csp_subarray_ln.command_inout("AssignResources", config)


        except Exception as exception:

            logger.exception(exception)
            raise exception

    def undo(self, sub_array_id: int):
        """Domain logic for releasing resources on a subarray in csp.

        This implements the tear_down_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        csp_subarray_ln_name = self._tel.tm.subarray(sub_array_id).csp_leaf_node  # type: ignore
        csp_subarray_ln = con_config.get_device_proxy(csp_subarray_ln_name)  # type: ignore
        self._log(f"Commanding {csp_subarray_ln_name} to ReleaseAllResources")
        csp_subarray_ln.command_inout("ReleaseAllResources")


class CspLnConfigureStep(CspConfigureStep):
    """Implementation of Configure Scan Step for CSP LN."""

    def do(
            self,
            sub_array_id: int,
            dish_ids: List[int],
            configuration: types.ScanConfiguration,
            sb_id: str,
            duration: float,
    ):
        """Domain logic for configuring a scan on subarray in csp LN.

        This implements the compose_subarray method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        :param dish_ids: this dish indices (in case of mid) to control
        :param composition: The assign resources configuration parameters
        :param sb_id: a generic ide to identify a sb to assign resources
        """
        # scan duration needs to be a memorized for future objects that many require it
        Memo(scan_duration=duration)
        csp_subarray_ln_name = self._tel.tm.subarray(sub_array_id).csp_leaf_node  # type: ignore
        csp_subarray_ln = con_config.get_device_proxy(csp_subarray_ln_name)  # type: ignore
        if self._tel.skamid:
            config = self.observation.generate_scan_config_parsed_for_csp(
                scan_duration=duration
            )
        elif self._tel.skalow:
            config_json = copy.deepcopy(CONFIGURE_CSP_JSON_LOW)
            config = json.dumps(config_json)


        logger.info(f"commanding {csp_subarray_ln_name} with Configure: {config}")
        csp_subarray_ln.command_inout("Configure", config)

    def undo(self, sub_array_id: int):
        """Domain logic for clearing configuration on a subarray in csp LN.

        This implements the clear_configuration method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        csp_subarray_ln_name = self._tel.tm.subarray(sub_array_id).csp_leaf_node  # type: ignore
        csp_subarray_ln = con_config.get_device_proxy(csp_subarray_ln_name)  # type: ignore
        self._log(f"commanding {csp_subarray_ln_name} with the End command")
        csp_subarray_ln.command_inout("End")


class CSPLnScanStep(CspScanStep):
    """Implementation of Scan Step for CSP LN."""

    def do(self, sub_array_id: int):
        """Domain logic for running a scan on subarray in csp.

        This implements the scan method on the entry_point.

        :param sub_array_id: The index id of the subarray to control
        """
        # scan_config = self.observation.generate_run_scan_conf().as_json
        scan_duration = Memo().get("scan_duration")
        csp_subarray_ln_name = self._tel.tm.subarray(sub_array_id).csp_leaf_node  # type: ignore
        csp_subarray_ln = con_config.get_device_proxy(csp_subarray_ln_name)  # type: ignore


        if self._tel.skamid:
            csp_run_scan_config = self.observation.generate_csp_run_scan_config()

        elif self._tel.skalow:
            csp_run_scan_config=copy.deepcopy(SCAN_CSP_JSON_LOW)

        self._log(
                f"Commanding {csp_subarray_ln_name} to Scan with {csp_run_scan_config}"
            )
        try:
            csp_subarray_ln.command_inout("Scan", json.dumps(csp_run_scan_config))
            sleep(scan_duration)
            csp_subarray_ln.command_inout("EndScan")
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
        """Domain logic specifying what needs to be done for waiting for subarray to be scanning.

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


class CSPLnEntryPoint(CompositeEntryPoint):
    """Derived Entrypoint scoped to CSP LN element."""

    nr_of_subarrays = 2

    def __init__(self, observation: Observation | None = None) -> None:
        """Init Object"""
        super().__init__()
        if observation is None:
            observation = Observation()
        self.set_online_step = NoOpStep()
        self.start_up_step = StartUpLnStep(self.nr_of_subarrays)
        self.assign_resources_step = CspLnAssignResourcesStep(observation)
        self.configure_scan_step = CspLnConfigureStep(observation)
        self.scan_step = CSPLnScanStep(observation)


assignresources_csp = {
    "interface": "https: //schema.skao.int/ska-mid-csp-assignresources/2.0",
    "subarray_id": 1,
    "dish": {"receptor_ids": ["0001", "0002"]},
}

configure_csp = {
    "interface": "https://schema.skao.int/ska-csp-configure/2.0",
    "subarray": {"subarray_name": "science period 23"},
    "common": {
        "config_id": "sbi-mvp01-20200325-00001-science_A",
        "frequency_band": "1",
        "subarray_id": "1",
    },
    "cbf": {
        "delay_model_subscription_point": "ska_mid/tm_leaf_node/csp_subarray01/delayModel",
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
            "reference_frame": "ICRS",
            "target_name": "Polaris Australis",
            "ra": "21:08:47.92",
            "dec": "-88:57:22.9",
        }
    },
}



ASSIGN_RESOURCE_CSP_JSON_LOW={
  "interface": "https://schema.skao.int/ska-low-csp-assignresources/2.0",
  "common": {
    "subarray_id": 1
  },
  "lowcbf": {
    "resources": [
      {
        "device": "fsp_01",
        "shared": True,
        "fw_image": "pst",
        "fw_mode": "unused"
      },
      {
        "device": "p4_01",
        "shared": True,
        "fw_image": "p4.bin",
        "fw_mode": "p4"
      }
    ]
  }
}

SCAN_CSP_JSON_LOW = {
  "common": {
    "subarray_id": 1
  },
  "lowcbf": {
    "scan_id": 987654321,
    "scan_seconds": 30
  }
}


CONFIGURE_CSP_JSON_LOW = {
  "interface": "https://schema.skao.int/ska-csp-configure/2.0",
  "subarray": {
    "subarray_name": "science period 23"
  },
  "common": {
    "config_id": "sbi-mvp01-20200325-00001-science_A",
    "subarray_id": 1
  },
  "lowcbf": {
    "stations": {
      "stns": [
        [
          1,
          0
        ],
        [
          2,
          0
        ],
        [
          3,
          0
        ],
        [
          4,
          0
        ]
      ],
      "stn_beams": [
        {
          "beam_id": 1,
          "freq_ids": [
            64,
            65,
            66,
            67,
            68,
            68,
            70,
            71
          ],
          "boresight_dly_poly": "url"
        }
      ]
    },
    "timing_beams": {
      "beams": [
        
      ]
    },
    
  }
}