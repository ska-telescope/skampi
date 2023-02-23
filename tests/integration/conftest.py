"""pytest global settings, fixtures and global bdd step implementations for
integration tests."""
import logging
from types import SimpleNamespace
import os

from typing import Any, Callable, Union, cast
from mock import patch, Mock
from assertpy import assert_that
import pytest
from pytest_bdd import when, given, then, parsers

from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types, SubarrayConfigurationSpec
from ska_ser_skallop.connectors import configuration as con_config

from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_management import telescope_management as tel

# from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.describing.mvp_names import TEL, DeviceName
from ska_ser_skallop.mvp_fixtures.base import ExecSettings
from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from ska_ser_skallop.mvp_control.entry_points import configuration as entry_conf
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from resources.models.tmc_model.entry_point import TMCEntryPoint
from resources.models.obsconfig.config import Observation
from resources.models.mvp_model.states import ObsState
from tests.resources.models.mvp_model.configuration import SKAScanConfiguration
from tests.resources.models.obsconfig.target_spec import TargetSpec


logger = logging.getLogger(__name__)


class SutTestSettings(SimpleNamespace):
    """Object representing env like SUT settings for fixtures in conftest."""

    mock_sut: bool = False
    nr_of_subarrays = 3
    subarray_id = 1
    scan_duration = 4
    _receptors = [1, 2, 3, 4]
    _nr_of_receptors = 4

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.tel = TEL()
        logger.info("initialising sut settings")
        self.tel = TEL()
        self.observation = Observation()
        self.default_subarray_name: DeviceName = self.tel.tm.subarray(self.subarray_id)

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


@pytest.fixture(name="configuration")
def fxt_configuration(
    tmp_path: str, observation_config: Observation
) -> conf_types.ScanConfiguration:
    """Setup a base scan configuration to use for sdp.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    _tel = TEL()
    if _tel.skalow:
        configuration = conf_types.ScanConfigurationByFile(
            tmp_path, conf_types.ScanConfigurationType.STANDARD
        )
    else:
        configuration = SKAScanConfiguration(observation_config)
    return configuration


@pytest.fixture(name="disable_clear")
def fxt_disable_abort(configured_subarray: fxt_types.configured_subarray):
    configured_subarray.disable_automatic_clear()


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


@pytest.fixture(name="observation_config")
def fxt_observation_config(sut_settings: SutTestSettings) -> Observation:
    return sut_settings.observation


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
        with standby_telescope.wait_for_starting_up(integration_test_exec_settings):
            logger.info("The entry point being used is : %s", entry_point)
            entry_point.set_telescope_to_running()


@given("the Telescope is in ON state")
def the_telescope_is_on(
    standby_telescope: fxt_types.standby_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """I start up the telescope."""
    standby_telescope.disable_automatic_setdown()
    with context_monitoring.context_monitoring():
        with standby_telescope.wait_for_starting_up(integration_test_exec_settings):
            logger.info("The entry point being used is : %s", entry_point)
            entry_point.set_telescope_to_running()


@given(
    parsers.parse(
        "a subarray defined to perform scans for types {scan_target1} "
        "and {scan_target2}"
    ),
    target_fixture="scan_targets",
)
def a_subarray_defined_to_perform_scan_types(
    scan_target1: str,
    scan_target2: str,
    observation_config: Observation,
) -> dict[str, str]:
    assert (
        scan_target1 in observation_config.scan_type_configurations
    ), f"Scan target {scan_target1} not defined"
    assert (
        scan_target2 in observation_config.scan_type_configurations
    ), f"Scan target {scan_target2} not defined"
    # check that we have targets referencing this scan types
    scan_targets = {
        target_spec.scan_type: target_name
        for target_name, target_spec in observation_config.target_specs.items()
    }
    assert scan_targets.get(
        scan_target1
    ), f"Scan target {scan_target1} not defined as part of scan targets"
    assert scan_targets.get(
        scan_target2
    ), f"Scan target {scan_target2} not defined as part of scan targets"
    return scan_targets


@when(
    parsers.parse("I configure the subarray again for scan type {scan_type}"),
    target_fixture="configured_subarray",
)
@given(
    parsers.parse("a subarray configured for scan type {scan_type}"),
    target_fixture="configured_subarray",
)
def a_subarray_configured_for_scan_type(
    scan_type: str,
    factory_configured_subarray: fxt_types.factory_configured_subarray,
    observation_config: Observation,
    configuration: conf_types.ScanConfiguration,
    sut_settings: SutTestSettings,
    scan_targets: dict[str, str],
):
    """a subarray configured for scan type {scan_type}"""
    scan_duration = sut_settings.scan_duration
    configuration = SKAScanConfiguration(observation_config)
    configuration.set_next_target_to_be_configured(scan_targets[scan_type])
    configuration_specs = SubarrayConfigurationSpec(scan_duration, configuration)
    return factory_configured_subarray(
        injected_subarray_configuration_spec=configuration_specs
    )


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


# Currently, resources_list is not utilised, raised SKB for the same:https://jira.skatelescope.org/browse/SKB-202
@when(
    parsers.parse(
        "I issue the assignResources command with the {resources_list} to the"
        " subarray {subarray_id}"
    )
)
def assign_resources_with_subarray_id(
    telescope_context: fxt_types.telescope_context,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
    resources_list: list,
    subarray_id: int,
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


# scan configuration


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


@when("I command it to scan for a given period")
def i_command_it_to_scan(
    configured_subarray: fxt_types.configured_subarray,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """I configure it for a scan."""
    configured_subarray.set_to_scanning(integration_test_exec_settings)


# scans
@given("the subarray has just completed it's first scan for given configuration")
@given("an subarray that has just completed it's first scan")
def an_subarray_that_has_just_completed_its_first_scan(
    configured_subarray: fxt_types.configured_subarray,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    configured_subarray.scan(integration_test_exec_settings)


@given("an subarray busy scanning")
def i_command_it_to_scan(
    configured_subarray: fxt_types.configured_subarray,
    integration_test_exec_settings: fxt_types.exec_settings,
    context_monitoring: fxt_types.context_monitoring,
):
    """I configure it for a scan."""
    integration_test_exec_settings.attr_synching = False
    with context_monitoring.context_monitoring():
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


@when("I command it to Abort")
def i_command_it_to_abort(
    context_monitoring: fxt_types.context_monitoring,
    allocated_subarray: fxt_types.allocated_subarray,
    entry_point: fxt_types.entry_point,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    subarray = sut_settings.default_subarray_name
    sub_array_id = sut_settings.subarray_id
    context_monitoring.builder.set_waiting_on(subarray).for_attribute(
        "obsstate"
    ).to_become_equal_to("ABORTED")
    with context_monitoring.context_monitoring():
        with context_monitoring.wait_before_complete(integration_test_exec_settings):
            allocated_subarray.reset_after_test(integration_test_exec_settings)
            entry_point.abort_subarray(sub_array_id)

    integration_test_exec_settings.touch()


@then("the subarray should go into an aborted state")
def the_subarray_should_go_into_an_aborted_state(
    sut_settings: SutTestSettings,
):
    subarray = con_config.get_device_proxy(sut_settings.default_subarray_name)
    result = subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.ABORTED)
