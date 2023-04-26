"""pytest global settings, fixtures and global bdd step implementations for
integration tests."""
import copy
import logging
import os
from types import SimpleNamespace
from typing import Any, Callable, Concatenate, ParamSpec, TypeVar

import pytest
from assertpy import assert_that
from mock import Mock, patch
from pytest_bdd import given, parsers, then, when
from pytest_bdd.parser import Feature, Scenario, Step
from resources.models.mvp_model.env import (
    Observation,
    init_observation_config,
    interject_observation_config,
)
from resources.models.mvp_model.states import ObsState
from resources.models.obsconfig.base import EncodedObject
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing.mvp_names import TEL, DeviceName
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.event_waiting.wait import EWhilstWaiting
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

logger = logging.getLogger(__name__)


def pytest_bdd_before_step_call(
    request: Any,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[[Any], Any],
    step_func_args: dict[str, Any],
):
    if os.getenv("SHOW_STEP_FUNCTIONS"):
        logger.info(
            "\n**********************************************************\n"
            f"***** {step.keyword} {step.name} *****\n"
            "**********************************************************"
        )


class SutTestSettings(SimpleNamespace):
    """Object representing env like SUT settings for fixtures in conftest."""

    mock_sut: bool = False
    nr_of_subarrays = 3
    subarray_id = 1
    scan_duration = 4
    _receptors = [1, 2, 3, 4]
    _nr_of_receptors = 4
    # specify if a specific test case needs running
    # for SDP visibility receive test: test_case = "vis-receive"
    test_case: str | None = None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.tel = TEL()
        logger.info("initialising sut settings")
        self.observation = init_observation_config()
        self.default_subarray_name: DeviceName = self.tel.tm.subarray(self.subarray_id)
        self.previous_state: Any = None
        self.next_state: Any = None
        self.observation = init_observation_config()
        self.disable_subarray_teardown = False
        self.restart_after_abort = False

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


@pytest.fixture(name="assign_resources_test_exec_settings")
def fxt_sdp_assign_resources_exec_settings(
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """Set up test specific execution settings.

    :param exec_settings: The global test execution settings as a fixture.
    :return: test specific execution settings as a fixture
    """
    return integration_test_exec_settings


@pytest.fixture(name="disable_clear")
def fxt_disable_abort(configured_subarray: fxt_types.configured_subarray):
    configured_subarray.disable_automatic_clear()


@pytest.fixture(name="sut_settings", scope="function", autouse=True)
def fxt_conftest_settings() -> SutTestSettings:
    """
    Fixture to use for setting env like  SUT settings for fixtures in conftest

    :return: sut test settings
    """
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
def fxt_run_mock_wrapper(request, _pytest_bdd_example, conftest_settings: SutTestSettings):
    """
    Fixture that returns a function to use for running a test as a mock.

    :param request: A request object
    :param _pytest_bdd_example: An object for pytest bdd example
    :param conftest_settings: An object for conftest_settings
    :return: run mock
    """

    def run_mock(mock_test: Callable):
        """
        Test the test using a mock SUT

        :param mock_test: A mock_test object
        """
        conftest_settings.mock_sut = True
        # pylint: disable-next=too-many-function-args
        with patch(
            "ska_ser_skallop.mvp_fixtures.fixtures.TransitChecking"
        ) as transit_checking_mock:
            transit_checking_mock.return_value.checker = Mock(unsafe=True)
            mock_test(request, _pytest_bdd_example)

    return run_mock


@pytest.fixture(name="set_exec_settings_from_env", autouse=True)
def fxt_set_exec_settings_from_env(exec_settings: fxt_types.exec_settings):
    """Set up general execution settings during setup and teardown.

    :param exec_settings: The global test execution settings as a fixture.
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
    """
    Pytest fixture that provides an instance of the `Observation`
    class representing the observation configuration
    for the system under test.

    :param sut_settings: A class representing the settings for the system under test.
    :return: A class representing the observation configuration for the system under test.
    """
    return sut_settings.observation


@pytest.fixture(name="mocked_observation_config")
def fxt_mocked_observation_config(observation_config: Observation):
    mocked_config = Mock(spec=Observation, wraps=observation_config)
    with interject_observation_config(mocked_config):
        yield mocked_config


T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R")


def _inject_method(injectable: T, method: Callable[Concatenate[T, P], R]) -> Callable[P, R]:
    def _replaced_method(*args: P.args, **kwargs: P.kwargs) -> R:
        return method(injectable, *args, **kwargs)

    return _replaced_method


ObservationConfigInterjector = Callable[[str, Callable[Concatenate[Observation, P], R]], None]


@pytest.fixture(name="interject_into_observation_config")
def fxt_observation_config_interjector(
    observation_config: Observation, mocked_observation_config: Mock
) -> ObservationConfigInterjector[P, R]:
    obs = observation_config

    def interject_observation_method(
        method_name: str, intj_fn: Callable[Concatenate[Observation, P], R]
    ):
        injected_method = _inject_method(obs, intj_fn)
        mocked_observation_config.configure_mock(**{f"{method_name}.side_effect": injected_method})

    return interject_observation_method


# global given steps


@given("an subarray busy scanning")
def an_subarray_busy_scanning(
    configured_subarray: fxt_types.configured_subarray,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """an subarray busy scanning"""
    configured_subarray.set_to_scanning(integration_test_exec_settings)


# global when steps
# start up


@when("I start up the telescope")
def i_start_up_the_telescope(
    standby_telescope: fxt_types.standby_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    I start up the telescope.

    :param standby_telescope: The standby telescope instance to be started.
    :param entry_point: The entry point to the system under test.
    :param context_monitoring: The context monitoring configuration.
    :param integration_test_exec_settings: The integration test execution settings.
    """
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
    """
    I start up the telescope.

    :param standby_telescope: The standby telescope instance to be started.
    :param entry_point: The entry point to the system under test.
    :param context_monitoring: The context monitoring configuration.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    standby_telescope.disable_automatic_setdown()
    with context_monitoring.context_monitoring():
        with standby_telescope.wait_for_starting_up(integration_test_exec_settings):
            logger.info("The entry point being used is : %s", entry_point)
            entry_point.set_telescope_to_running()


@when("I switch off the telescope")
def i_switch_off_the_telescope(
    running_telescope: fxt_types.running_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    I switch off the telescope.
    :param running_telescope: The running telescope instance.
    :param entry_point: The entry point to the system under test.
    :param context_monitoring: The context monitoring configuration.
    :param integration_test_exec_settings: The integration test execution settings.

    """
    # we disable automatic shutdown as this is done by the test itself
    running_telescope.disable_automatic_setdown()
    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_shutting_down(integration_test_exec_settings):
            entry_point.set_telescope_to_standby()


# Currently, resources_list is not utilised, raised SKB for the same:
# https://jira.skatelescope.org/browse/SKB-202
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
    """
    I assign resources to it

    :param telescope_context: A fixture that represents the telescope context.
    :param context_monitoring: A fixture that represents the context monitoring service.
    :param entry_point: A fixture that represents the entry point for the subarray.
    :param sb_config: A fixture that represents the scan configuration for the subarray.
    :param composition: A fixture that represents the composition of the subarray.
    :param integration_test_exec_settings: A fixture that represents the execution
        settings for the integration test.
    :param sut_settings: An instance of the `SutTestSettings` class representing
        the settings for the system under test.
    :param resources_list: A list of resources to be assigned to the subarray.
    :param subarray_id: An integer representing the ID of the subarray to which
        the resources should be assigned.
    """

    receptors = sut_settings.receptors
    with context_monitoring.context_monitoring():
        with telescope_context.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            entry_point.compose_subarray(subarray_id, receptors, composition, sb_config.sbid)


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
    """
    I assign resources to it

    :param running_telescope: Dictionary containing the running telescope's devices
    :param context_monitoring: Object containing information about
        the context in which the test is being executed
    :param entry_point: Information about the entry point used for the test
    :param sb_config: Object containing the Subarray Configuration
    :param composition: Object containing information about the composition of the subarray
    :param integration_test_exec_settings: Object containing
        the execution settings for the integration test
    :param sut_settings: Object containing the system under test settings
    """

    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            entry_point.compose_subarray(subarray_id, receptors, composition, sb_config.sbid)


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
    """
    I configure it for a scan.

    :param allocated_subarray: The allocated subarray to be configured.
    :param context_monitoring: Context monitoring object.
    :param entry_point: The entry point to be used for the configuration.
    :param configuration: The scan configuration to be used for the scan.
    :param integration_test_exec_settings: The integration test execution settings.
    :param sut_settings: SUT settings object.
    """
    sub_array_id = allocated_subarray.id
    sb_id = allocated_subarray.sb_config.sbid
    scan_duration = sut_settings.scan_duration

    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_configuring_a_subarray(integration_test_exec_settings):
            entry_point.configure_subarray(sub_array_id, configuration, sb_id, scan_duration)


@when("I command it to scan for a given period")
def i_execute_scan(
    configured_subarray: fxt_types.configured_subarray,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    I configure it for a scan.

    :param configured_subarray: The configured subarray.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    configured_subarray.set_to_scanning(integration_test_exec_settings)


# scans
@given("an subarray busy scanning")
def i_command_it_to_scan(
    configured_subarray: fxt_types.configured_subarray,
    integration_test_exec_settings: fxt_types.exec_settings,
    context_monitoring: fxt_types.context_monitoring,
):
    """
    I configure it for a scan.

    :param configured_subarray: The configured subarray.
    :param integration_test_exec_settings: The integration test execution settings.
    :param context_monitoring: Context monitoring object.
    """
    integration_test_exec_settings.attr_synching = False
    with context_monitoring.context_monitoring():
        configured_subarray.set_to_scanning(integration_test_exec_settings)


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


@when("I release all resources assigned to it")
def i_release_all_resources_assigned_to_it(
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    I release all resources assigned to it.

    :param allocated_subarray: The allocated subarray to be configured.
    :param context_monitoring: Context monitoring object.
    :param entry_point: The entry point to be used for the configuration.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    sub_array_id = allocated_subarray.id

    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_releasing_a_subarray(integration_test_exec_settings):
            entry_point.tear_down_subarray(sub_array_id)


def generate_invalid_config(observation: Observation):
    incorrect_config: dict[str, str] = {}
    return EncodedObject(incorrect_config)


def generate_invalid_sdp_processing_block_script(observation: Observation):
    original = observation.generate_sdp_assign_resources_config().as_object
    incorrect = copy.deepcopy(original)
    incorrect.processing_blocks[0].script.name = "vis_receive"
    return EncodedObject(incorrect)


def generate_invalid_processing_block_script(observation: Observation):
    original = observation.generate_assign_resources_config().as_object
    incorrect = copy.deepcopy(original)
    incorrect.sdp_config.processing_blocks[0].script.name = "vis_receive"
    return EncodedObject(incorrect)


@pytest.fixture(name="invalid_assign_config_interjected")
def fxt_invalid_assign_config_interjected(
    interject_into_observation_config: ObservationConfigInterjector[
        [], EncodedObject[dict[str, Any]]
    ],
    entry_point: fxt_types.entry_point,
):
    interject_into_observation_config("generate_assign_resources_config", generate_invalid_config)
    entry_point.__init__()


@pytest.fixture(name="invalid_processing_block_script_interjected")
def fxt_invalid_processing_block_script_interjected(
    interject_into_observation_config: ObservationConfigInterjector[[], EncodedObject[Any]],
    entry_point: fxt_types.entry_point,
):
    interject_into_observation_config(
        "generate_assign_resources_config", generate_invalid_processing_block_script
    )
    interject_into_observation_config(
        "generate_sdp_assign_resources_config",
        generate_invalid_sdp_processing_block_script,
    )
    entry_point.__init__()


class StepResult:
    def __init__(self) -> None:
        self.expected_exception_raised = False
        self.exception: Exception | None = None
        self.result_ok = True
        self.result: Callable[[], Any] = lambda: None

    def result_ok_but_expected_exception_not_raised(self) -> bool:
        if self.result_ok:
            if not self.expected_exception_raised:
                return True
        return False


@when(
    "I assign resources with an invalid processing block script name",
    target_fixture="step_result",
)
def when_i_assign_resources_with_invalid_pb(
    running_telescope: fxt_types.running_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    composition: conf_types.Composition,
    sb_config: fxt_types.sb_config,
    sut_settings: SutTestSettings,
    invalid_processing_block_script_interjected,  # type: ignore this creates an empty assign config
) -> StepResult:
    subarray_id = sut_settings.subarray_id
    sut_settings.previous_state = ObsState.EMPTY
    receptors = sut_settings.receptors
    step_result = _assign_resources_with_invalid_config(
        subarray_id,
        receptors,
        entry_point,
        context_monitoring,
        integration_test_exec_settings,
        composition,
        sb_config,
        sut_settings,
    )
    if step_result.result_ok_but_expected_exception_not_raised():
        subarray_device = con_config.get_device_proxy(sut_settings.default_subarray_name)
        result = subarray_device.read_attribute("obsstate").value
        if result == ObsState.EMPTY:
            step_result.result_ok = False
            step_result.result = lambda: except_it(
                "exception not raised when calling assign but it did return " "back to EMPTY"
            )
        else:
            integration_test_exec_settings.touch()
            running_telescope.release_subarray_when_finished(
                subarray_id, receptors, integration_test_exec_settings
            )
            step_result.result_ok = False
            step_result.result = lambda: except_it(
                "exception not raised when calling assign but it did "
                "successfully go to IDLE\n"
                "Are you sure the config is invalid?"
            )
    return step_result


@when("I assign resources with invalid config", target_fixture="step_result")
def when_i_assign_resources_with_invalid_config(
    running_telescope: fxt_types.running_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    composition: conf_types.Composition,
    sb_config: fxt_types.sb_config,
    sut_settings: SutTestSettings,
    invalid_assign_config_interjected,  # type: ignore this creates an empty assign config
) -> StepResult:
    subarray_id = sut_settings.subarray_id
    sut_settings.previous_state = ObsState.EMPTY
    receptors = sut_settings.receptors
    step_result = _assign_resources_with_invalid_config(
        subarray_id,
        receptors,
        entry_point,
        context_monitoring,
        integration_test_exec_settings,
        composition,
        sb_config,
        sut_settings,
    )
    if step_result.result_ok_but_expected_exception_not_raised():
        subarray_device = con_config.get_device_proxy(sut_settings.default_subarray_name)
        result = subarray_device.read_attribute("obsstate").value
        if result == ObsState.EMPTY:
            step_result.result_ok = False
            step_result.result = lambda: except_it(
                "exception not raised when calling assign but it " "did return back to EMPTY"
            )
        else:
            integration_test_exec_settings.touch()
            running_telescope.release_subarray_when_finished(
                subarray_id, receptors, integration_test_exec_settings
            )
            step_result.result_ok = False
            step_result.result = lambda: except_it(
                "exception not raised when calling assign but it did "
                "successfully go to IDLE\n"
                "Are you sure the config is invalid?"
            )
    return step_result


def _assign_resources_with_invalid_config(
    subarray_id: int,
    receptors: list[int],
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    composition: conf_types.Composition,
    sb_config: fxt_types.sb_config,
    sut_settings: SutTestSettings,
) -> StepResult:
    settings = integration_test_exec_settings
    subarray = sut_settings.default_subarray_name
    step_result = StepResult()

    with context_monitoring.context_monitoring():
        context_monitoring.builder.set_waiting_on(subarray).for_attribute(
            "obsstate"
        ).to_become_equal_to("RESOURCING")
        try:
            settings.time_out = 2
            # we force attr synching to False to prevent
            # reverts to state causing inconsistent interpretations
            settings.attr_synching = False
            with context_monitoring.wait_before_complete(settings):
                try:
                    entry_point.compose_subarray(
                        subarray_id, receptors, composition, sb_config.sbid
                    )
                except Exception as exception:
                    step_result.exception = exception
                    step_result.expected_exception_raised = True
        except EWhilstWaiting:
            if not step_result.expected_exception_raised:
                step_result.result_ok = False
                step_result.result = lambda: except_it(
                    "expected timeout waiting for resourcing ocurred but"
                    " no expected command exception thrown"
                )
            return step_result
    # this means we did not have a time out waiting for RESOURCING so now we
    # will attempt to wait for the next state IDLE or alternatively EMPTY if it reverted
    context_monitoring.re_init_builder()
    with context_monitoring.context_monitoring():
        context_monitoring.builder.set_waiting_on(subarray).for_attribute(
            "obsstate"
        ).to_become_equal_to(["EMPTY", "IDLE"], ignore_first=False)
        try:
            settings.time_out = 100
            with context_monitoring.wait_before_complete(settings):
                pass
        except EWhilstWaiting:
            # this means we are stuck in RESOURCING so will attempt to reset
            if step_result.expected_exception_raised:
                step_result.result_ok = False
                step_result.result = lambda: except_it(
                    "exception raised when calling assign but it seems be" " stuck in RESOURCING"
                )
                return step_result
            else:
                step_result.result_ok = False
                step_result.result = lambda: except_it(
                    "exception not raised when calling assign but it seems"
                    " to be stuck in RESOURCING"
                )
                return step_result
    assert step_result.result_ok
    return step_result


def except_it(args: str):
    raise Exception(args)


@when("I assign resources with a duplicate sb id", target_fixture="step_result")
def when_i_assign_resources_with_a_duplicate_sb_id(
    running_telescope: fxt_types.running_telescope,
    allocated_subarray: fxt_types.allocated_subarray,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    composition: conf_types.Composition,
    sb_config: fxt_types.sb_config,
    sut_settings: SutTestSettings,
) -> StepResult:
    subarray_id = allocated_subarray.id
    receptors = allocated_subarray.receptors
    sut_settings.previous_state = ObsState.IDLE
    step_result = _assign_resources_with_invalid_config(
        subarray_id,
        receptors,
        entry_point,
        context_monitoring,
        integration_test_exec_settings,
        composition,
        sb_config,
        sut_settings,
    )
    if step_result.result_ok:
        if not step_result.expected_exception_raised:
            subarray_device = con_config.get_device_proxy(sut_settings.default_subarray_name)
            result = subarray_device.read_attribute("obsstate").value
            if result == ObsState.EMPTY:
                allocated_subarray.disable_automatic_teardown()
                step_result.result_ok = False
                step_result.result = lambda: except_it(
                    "exception not raised when calling assign but it did " "return back to EMPTY"
                )
            else:
                step_result.result_ok = False
                step_result.result = lambda: except_it(
                    "exception not raised when calling assign but it did "
                    "successfully go to IDLE\n"
                    "Are you sure the config is invalid?"
                )
    return step_result


@pytest.fixture(name="invalid_scan_config_interjected")
def fxt_invalid_scan_config_interjected(
    allocated_subarray: fxt_types.allocated_subarray,
    interject_into_observation_config: ObservationConfigInterjector[
        [], EncodedObject[dict[str, Any]]
    ],
    entry_point: fxt_types.entry_point,
    sut_settings: SutTestSettings,
):
    subarray_name = str(sut_settings.default_subarray_name)
    subarray_id = allocated_subarray.id
    sdp_subarray_name = str(sut_settings.tel.sdp.subarray(subarray_id))
    csp_subarray_name = str(sut_settings.tel.csp.subarray(subarray_id))

    if subarray_name == sdp_subarray_name:
        interject_into_observation_config("generate_sdp_scan_config", generate_invalid_config)
    elif subarray_name == csp_subarray_name:
        interject_into_observation_config("generate_csp_scan_config", generate_invalid_config)
    else:
        interject_into_observation_config("generate_scan_config", generate_invalid_config)
    entry_point.__init__()


@when(
    "I configure it for a scan with an invalid configuration",
    target_fixture="step_result",
)
def i_configure_it_for_a_scan_with_an_invalid_config(
    allocated_subarray: fxt_types.allocated_subarray,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    configuration: conf_types.ScanConfiguration,
    sut_settings: SutTestSettings,
    invalid_scan_config_interjected,  # type: ignore this causes an empty scan config
) -> StepResult:
    subarray_id = allocated_subarray.id
    sb_id = allocated_subarray.sb_config.sbid
    subarray = sut_settings.default_subarray_name
    receptors = allocated_subarray.receptors
    settings = integration_test_exec_settings
    sut_settings.previous_state = ObsState.IDLE
    duration = sut_settings.scan_duration
    # setup a normal context and specifically wait for CONFIGURING
    step_result = StepResult()
    step_result.result_ok = False
    with context_monitoring.context_monitoring():
        context_monitoring.builder.set_waiting_on(subarray).for_attribute(
            "obsstate"
        ).to_become_equal_to("CONFIGURING")
        try:
            settings.time_out = 1
            # we force attr synching to False to prevent
            # reverts to state causing inconsistent interpretations
            settings.attr_synching = False
            with context_monitoring.wait_before_complete(settings):
                try:
                    entry_point.configure_subarray(
                        subarray_id, receptors, configuration, sb_id, duration
                    )
                except Exception as exception:
                    step_result.exception = exception
                    step_result.expected_exception_raised = True
                    step_result.result_ok = True
        except EWhilstWaiting:
            if not step_result.expected_exception_raised:
                step_result.result = lambda: except_it(
                    "expected timeout waiting for CONFIGURING ocurred but no"
                    " expected command exception thrown"
                )
            return step_result
    # this means we did not have a time out waiting for RESOURCING so now we
    # will attempt to wait for the next state IDLE or alternatively EMPTY if it reverted
    context_monitoring.re_init_builder()
    with context_monitoring.context_monitoring():
        context_monitoring.builder.set_waiting_on(subarray).for_attribute(
            "obsstate"
        ).to_become_equal_to(["IDLE", "READY"], ignore_first=False)
        try:
            settings.time_out = 20
            with context_monitoring.wait_before_complete(settings):
                pass
        except EWhilstWaiting:
            # this means we are stuck in CONFIGURING so will attempt to reset
            if step_result.expected_exception_raised:
                step_result.result_ok = False
                step_result.result = lambda: except_it(
                    "exception raised when calling configure but it seems be"
                    " stuck in CONFIGURING"
                )
            else:
                step_result.result = lambda: except_it(
                    "exception not raised when calling configure but it "
                    "seems to be stuck in CONFIGURING"
                )
            return step_result
    if not step_result.expected_exception_raised:
        subarray_device = con_config.get_device_proxy(sut_settings.default_subarray_name)
        result = subarray_device.read_attribute("obsstate").value
        if result == ObsState.IDLE:
            step_result.result = lambda: except_it(
                "exception not raised when calling configure but it did return " "back to IDLE"
            )
        else:
            allocated_subarray.clear_configuration_when_finished(integration_test_exec_settings)
            step_result.result = lambda: except_it(
                "exception not raised when calling configure but it did "
                "successfully go to IDLE"
                "Are you sure the config is invalid?"
            )
    return step_result


@when(
    "I command the assign resources twice in consecutive fashion",
    target_fixture="step_result",
)
def i_command_the_assign_resources_twice_in_consecutive_fashion(
    running_telescope: fxt_types.running_telescope,
    entry_point: fxt_types.entry_point,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    composition: conf_types.Composition,
    sb_config: fxt_types.sb_config,
    sut_settings: SutTestSettings,
) -> StepResult:
    """I assign resources to it."""

    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
    step_result = StepResult()
    sut_settings.next_state = ObsState.IDLE
    step_result.result_ok = False
    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            entry_point.compose_subarray(subarray_id, receptors, composition, sb_config.sbid)
            try:
                entry_point.compose_subarray(subarray_id, receptors, composition, sb_config.sbid)
            except Exception as exception:
                step_result.expected_exception_raised = True
                step_result.result_ok = True
                step_result.exception = exception
    return step_result


# thens
@then("the subarray should throw an exception and continue with first command")
def the_subarray_should_throw_an_exception_and_continue_with_first_command(
    step_result: StepResult,
    sut_settings: SutTestSettings,
):
    step_result.result()
    assert (
        step_result.expected_exception_raised
    ), "No exception was raised after commanding the assign resources twice"
    logger.info(f"exception successfully raised with {step_result.exception.args}")
    subarray = con_config.get_device_proxy(sut_settings.default_subarray_name)
    result = subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(sut_settings.next_state)


@then("the subarray should throw an exception and remain in the previous state")
def the_subarray_should_throw_an_exception_remain_in_the_previous_state(
    sut_settings: SutTestSettings, step_result: StepResult
):
    step_result.result()
    # we have to wait for a limited time to ensure any state transitions are stable
    subarray = con_config.get_device_proxy(sut_settings.default_subarray_name)
    result = subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(sut_settings.previous_state)


@given("an subarray busy configuring")
def an_subarray_busy_configuring(allocated_subarray: fxt_types.allocated_subarray):
    """
    an subarray busy configuring

    :param allocated_subarray: The allocated subarray to be configured.
    """
    allocated_subarray.set_to_configuring(clear_afterwards=False)
    allocated_subarray.disable_automatic_clear()


@given("an subarray busy assigning", target_fixture="allocated_subarray")
def an_subarray_busy_assigning(
    running_telescope: fxt_types.running_telescope,
    sb_config: fxt_types.sb_config,
    composition: conf_types.Composition,
    exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """an subarray busy assigning

    Create a subarray but block only until it is in RESOURCING
    :param running_telescope: An object for running telescope
    :param sb_config: The SB configuration to use as context
        defaults to SBConfig()
    :param composition: The type of composition configuration to use
        , defaults to conf_types.Composition
        ( conf_types.CompositionType.STANDARD )
    :type composition: conf_types.Composition, optional
    :param exec_settings: A fixture that returns the execution settings of the test
    :param sut_settings: The settings of the system under test
    :return: A subarray context manager to ue for subsequent commands
    """
    subarray_id = sut_settings.subarray_id
    receptors = sut_settings.receptors
    allocated_subbaray = running_telescope.set_to_resourcing(
        subarray_id, receptors, sb_config, exec_settings, composition
    )
    allocated_subbaray.disable_automatic_teardown()
    return allocated_subbaray


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
            if sut_settings.restart_after_abort:
                allocated_subarray.restart_after_test(integration_test_exec_settings)
            else:
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
