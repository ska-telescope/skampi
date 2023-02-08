"""pytest global settings, fixtures and global bdd step implementations for
integration tests."""
import json
import copy
import logging
from types import SimpleNamespace
import os

from typing import Any, Callable
from mock import patch, Mock

from resources.models.mvp_model.states import ObsState

import pytest
from assertpy import assert_that
from pytest_bdd import when, given, parsers

from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_management import telescope_management as tel
from ska_ser_skallop.mvp_fixtures.base import ExecSettings
from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from ska_ser_skallop.mvp_control.entry_points import configuration as entry_conf
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from resources.models.tmc_model.entry_point import TMCEntryPoint
from resources.models.obsconfig.config import Observation


logger = logging.getLogger(__name__)


class SutTestSettings(SimpleNamespace):
    """Object representing env like SUT settings for fixtures in conftest."""

    mock_sut: bool = False
    nr_of_subarrays = 3
    subarray_id = 1
    scan_duration = 4
    _receptors = [1, 2, 3, 4]
    _nr_of_receptors = 4
    _scan_configuration = None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        logger.info("initialising sut settings")
        self.observation = Observation()

    @property
    def nr_of_receptors(self):
        return self._nr_of_receptors

    @nr_of_receptors.setter
    def nr_of_receptors(self, value: int):
        self._nr_of_receptors = value
        self._receptors = [i for i in range(1, value + 1)]

    @property
    def receptors(self):
        return self._receptors

    @receptors.setter
    def receptors(self, receptor: list[int]):
        self._receptors = receptor

    @property
    def scan_configuration(self):
        return self._scan_configuration

    @scan_configuration.setter
    def scan_configuration(self, scan_configuration: None):
        self._scan_configuration = scan_configuration


@pytest.fixture(name="sut_settings", scope="function")
def fxt_conftest_settings() -> SutTestSettings:
    """Fixture to use for setting env like  SUT settings for fixtures in conftest"""
    return SutTestSettings()

class OnlineFlag:

    value: bool = False

    def __bool__(self):
        return self.value

    def set_true(self):
        self.value = True


# setting systems online
@pytest.fixture(name="online", autouse=True, scope="session")
def fxt_online():
    return OnlineFlag()

# setting systems online
def generate_configure_json_for_low(sut_settings: SutTestSettings):
    template = copy.deepcopy(LOW_CONFIGURE_JSON)
    #template["csp"]["common"]["config_id"] = f'{sb_id}-{template["sdp"]["scan_type"]}'
    template["csp"]["common"]["subarray_id"] = sut_settings.subarray_id
    template["tmc"]["scan_duration"] = sut_settings.scan_duration
    return json.dump(template)


@pytest.fixture(name="set_session_exec_settings", autouse=True, scope="session")
def fxt_set_session_exec_settings(
    session_exec_settings: fxt_types.session_exec_settings,
):
    if os.getenv("ATTR_SYNCH_ENABLED_GLOBALLY"):
        # logger.warning("disabled attribute synchronization globally")
        session_exec_settings.attr_synching = True
    if os.getenv("LIVE_LOGGING_EXTENDED"):
        session_exec_settings.run_with_live_logging()
    return session_exec_settings


@pytest.fixture(name="run_mock")
def fxt_run_mock_wrapper(
    request, _pytest_bdd_example, conftest_settings: SutTestSettings
):
    """Fixture that returns a function to use for running a test as a mock."""

    def run_mock(mock_test: Callable):
        """Test the test using a mock SUT"""
        conftest_settings.mock_sut = True
        # pylint: disable-next=too-many-function-args
        with patch(
            "ska_ser_skallop.mvp_fixtures.fixtures.TransitChecking"
        ) as transit_checking_mock:
            transit_checking_mock.return_value.checker = Mock(unsafe=True)
            mock_test(request, _pytest_bdd_example)  # type: ignore

    return run_mock


@pytest.fixture(name="set_exec_settings_from_env", autouse=True)
def fxt_set_exec_settings_from_env(exec_settings: fxt_types.exec_settings):
    """Set up general execution settings during setup and teardown.

    :param exec_settings: The global test execution settings as a fixture.
    :return: test specific execution settings as a fixture
    """
    if os.getenv("LIVE_LOGGING_EXTENDED"):
        logger.info("running live logs globally")
        exec_settings.run_with_live_logging()
    if os.getenv("ATTR_SYNCH_ENABLED_GLOBALLY"):
        logger.warning("enabled attribute synchronization globally")
        exec_settings.attr_synching = True
    exec_settings.time_out = 150


@pytest.fixture(name="integration_test_exec_settings")
def fxt_integration_test_exec_settings(
    exec_settings: fxt_types.exec_settings,
) -> fxt_types.exec_settings:
    """Set up test specific execution settings.

    :param exec_settings: The global test execution settings as a fixture.
    :return: test specific execution settings as a fixture
    """
    integration_test_exec_settings = exec_settings.replica()
    integration_test_exec_settings.time_out = 150

    if os.getenv("LIVE_LOGGING"):
        integration_test_exec_settings.run_with_live_logging()
        logger.info("running live logs globally")
    if os.getenv("REPLAY_EVENTS_AFTERWARDS"):
        logger.info("replay log messages after waiting")
        integration_test_exec_settings.replay_events_afterwards()
    if os.getenv("ATTR_SYNCH_ENABLED"):
        logger.warning("enabled attribute synchronization")
        exec_settings.attr_synching = True
    if os.getenv("ATTR_SYNCH_ENABLED_GLOBALLY"):
        exec_settings.attr_synching = True
    return integration_test_exec_settings


# global when steps
# start up


@when("I start up the telescope")
def i_start_up_the_telescope(
    standby_telescope: fxt_types.standby_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """I start up the telescope."""
    with context_monitoring.context_monitoring():
        with standby_telescope.wait_for_starting_up(
            integration_test_exec_settings):
            logger.info("The entry point being used is : %s", entry_point)
            entry_point.set_telescope_to_running()


@given("the Telescope is in ON state")
def the_telescope_is_on(
    standby_telescope : fxt_types.standby_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """I start up the telescope."""
    standby_telescope.disable_automatic_setdown()
    with context_monitoring.context_monitoring():
        with standby_telescope.wait_for_starting_up(
            integration_test_exec_settings):
            logger.info("The entry point being used is : %s", entry_point)
            entry_point.set_telescope_to_running()
   
            
@when("I switch off the telescope")
def i_switch_off_the_telescope(
    running_telescope: fxt_types.running_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """I switch off the telescope."""
    # we disable automatic shutdown as this is done by the test itself
    running_telescope.disable_automatic_setdown()
    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_shutting_down(integration_test_exec_settings):
            entry_point.set_telescope_to_standby()

#Currently, resources_list is not utilised, raised SKB for the same:https://jira.skatelescope.org/browse/SKB-202
@when(parsers.parse("I issue the assignResources command with the {resources_list} to the subarray {subarray_id}"))
def assign_resources_with_subarray_id(
    telescope_context: fxt_types.telescope_context,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
    resources_list:list,
    subarray_id:int
):
    """I assign resources to it."""

    receptors = sut_settings.receptors
    with context_monitoring.context_monitoring():
        with telescope_context.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            entry_point.compose_subarray(
                subarray_id, receptors, composition, sb_config.sbid
            )


@when("I assign resources to it")
def i_assign_resources_to_it(
    running_telescope: fxt_types.running_telescope,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """I assign resources to it."""

    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            entry_point.compose_subarray(
                subarray_id, receptors, composition, sb_config.sbid
            )


@given(parsers.parse("the subarray {subarray_id} obsState is IDLE"))
def the_subarray_is_in_idle(
    telescope_context: fxt_types.telescope_context,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
    subarray_id: int,
):
    """I assign resources to it."""

    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
    with context_monitoring.context_monitoring():
        with telescope_context.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings,
            release_when_finished=False,
        ):
            entry_point.compose_subarray(
                subarray_id, receptors, composition, sb_config.sbid
            )
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)



# scan configuration
@when("I configure it for a scan")
def i_configure_it_for_a_scan(
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    configuration: conf_types.ScanConfiguration,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """I configure it for a scan."""
    sub_array_id = allocated_subarray.id
    receptors = allocated_subarray.receptors
    sb_id = allocated_subarray.sb_config.sbid
    scan_duration = sut_settings.scan_duration

    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_configuring_a_subarray(
            integration_test_exec_settings
        ):
            entry_point.configure_subarray(
                sub_array_id, receptors, configuration, sb_id, scan_duration
            )


# fixture for SUT2.2
@when("I issue the configure command with <scan_type/config_id> and <scan_configuration> to the subarray <subarray_id>")
def i_configure_it_for_a_scan(
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    configuration: conf_types.ScanConfiguration,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
    scan_type:str,
    scan_configuration:str,
    subarray_id:int,
):
    """I configure it for a scan."""
    sub_array_id = allocated_subarray.id
    receptors = allocated_subarray.receptors
    sb_id = allocated_subarray.sb_config.sbid
    scan_duration = sut_settings.scan_duration

    # set input values
    sut_settings.subarray_id = subarray_id
    sut_settings.scan_configuration = scan_configuration

    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_configuring_a_subarray(
            integration_test_exec_settings
        ):
            entry_point.configure_subarray(
                sub_array_id, receptors, configuration, sb_id, scan_duration
            )

# scans
@when("I command it to scan for a given period")
def i_command_it_to_scan(
    configured_subarray: fxt_types.configured_subarray,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """I configure it for a scan."""
    configured_subarray.set_to_scanning(integration_test_exec_settings)



@when("I release all resources assigned to it")
def i_release_all_resources_assigned_to_it(
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """I release all resources assigned to it."""
    sub_array_id = allocated_subarray.id

    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_releasing_a_subarray(
            integration_test_exec_settings
        ):
            entry_point.tear_down_subarray(sub_array_id)


# temp change
LOW_CONFIGURE_JSON = {
  "interface": "https://schema.skao.int/ska-low-tmc-configure/3.0",
  "transaction_id": "txn-....-00001",
  "mccs": {
    "stations": [
      {
        "station_id": 1
      },
      {
        "station_id": 2
      }
    ],
    "subarray_beams": [
      {
        "subarray_beam_id": 1,
        "station_ids": [
          1,
          2
        ],
        "update_rate": 0.0,
        "channels": [
          [
            0,
            8,
            1,
            1
          ],
          [
            8,
            8,
            2,
            1
          ],
          [
            24,
            16,
            2,
            1
          ]
        ],
        "antenna_weights": [
          1.0,
          1.0,
          1.0
        ],
        "phase_centre": [
          0.0,
          0.0
        ],
        "target": {
          "reference_frame": "HORIZON",
          "target_name": "DriftScan",
          "az": 180.0,
          "el": 45.0
        }
      }
    ]
  },
  "sdp": {
    "interface": "https://schema.skao.int/ska-sdp-configure/0.4",
    "scan_type": "science_A"
  },
  "csp": {
    "interface": "https://schema.skao.int/ska-csp-configure/2.0",
    "subarray": {
      "subarray_name": "science period 23"
    },
    "common": {
      "config_id": "sbi-mvp01-20200325-00001-science_A"
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
          {
            "pst_beam_id": 13,
            "stn_beam_id": 1,
            "offset_dly_poly": "url",
            "stn_weights": [
              0.9,
              1.0,
              1.0,
              0.9
            ],
            "jones": "url",
            "dest_chans": [
              128,
              256
            ],
            "rfi_enable": [
              "true",
              "true",
              "true"
            ],
            "rfi_static_chans": [
              1,
              206,
              997
            ],
            "rfi_dynamic_chans": [
              242,
              1342
            ],
            "rfi_weighted": 0.87
          }
        ]
      }
    }
  },
  "tmc": {
    "scan_duration": 10.0
  }
}