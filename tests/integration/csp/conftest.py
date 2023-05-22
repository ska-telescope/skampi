"""
Pytest fixtures and bdd step implementations specific to csp integration tests.
"""
import logging
import os
from typing import Callable

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, then
from resources.models.csp_model.entry_point import CSPEntryPoint
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from .. import conftest
from ..conftest import SutTestSettings


@pytest.fixture(name="nr_of_subarrays", autouse=True, scope="session")
def fxt_nr_of_subarrays() -> int:
    """_summary_

    :return: _description_
    :rtype: int
    """
    # we only work with 1 subarray as CBF low currently limits
    # deployment of only 1
    # cbf mid only controls the state of subarray 1
    # so will also limit to 1
    tel = names.TEL()
    if tel.skalow:
        return 1
    return 2


@pytest.fixture(name="set_nr_of_subarray", autouse=True)
def fxt_set_nr_of_subarray(
    sut_settings: conftest.SutTestSettings,
    exec_settings: fxt_types.exec_settings,
    nr_of_subarrays: int,
):
    """_summary_
    :param nr_of_subarrays: _description_
    :type nr_of_subarrays: int
    :param sut_settings: _description_
    :type sut_settings: conftest.SutTestSettings
    :param exec_settings: A fixture that returns the execution settings of the test
    :type exec_settings: fxt_types.exec_settings
    """

    CSPEntryPoint.nr_of_subarrays = nr_of_subarrays
    sut_settings.nr_of_subarrays = nr_of_subarrays


@pytest.fixture(autouse=True, scope="session")
def fxt_set_csp_online_from_csp(
    set_session_exec_settings: fxt_types.session_exec_settings,
    set_subsystem_online: Callable[[EntryPoint], None],
    wait_sut_ready_for_session: Callable[[EntryPoint], None],
    nr_of_subarrays: int,
):
    """_summary_

    :param nr_of_subarrays: _description_
    :type nr_of_subarrays: int
    :param set_subsystem_online: _description_
    :type set_subsystem_online: Callable[[EntryPoint], None]
    :param set_session_exec_settings: A fixture to set session execution settings.
    :param wait_sut_ready_for_session: callable fixture to wait for sut.
    :type set_session_exec_settings: fxt_types.session_exec_settings
    """
    # we first wait in case csp is not ready
    set_session_exec_settings.time_out = 300
    set_session_exec_settings.log_enabled = True
    tel = names.TEL()
    set_session_exec_settings.capture_logs_from(str(tel.csp.subarray(1)))
    entry_point = CSPEntryPoint()
    logging.info("wait for sut to be ready in the context of csp")
    wait_sut_ready_for_session(entry_point)
    logging.info("setting csp components online within csp context")
    CSPEntryPoint.nr_of_subarrays = nr_of_subarrays
    entry_point = CSPEntryPoint()
    set_subsystem_online(entry_point)


@pytest.fixture(name="set_csp_entry_point", autouse=True)
def fxt_set_csp_entry_point(
    set_nr_of_subarray,
    set_session_exec_env: fxt_types.set_session_exec_env,
    exec_settings: fxt_types.exec_settings,
    sut_settings: conftest.SutTestSettings,
):
    """_summary_

    :param set_nr_of_subarray: To set the number of subarray
    :type set_nr_of_subarray: int
    :param set_session_exec_env: _description_
    :type set_session_exec_env: fxt_types.set_session_exec_env
    :param exec_settings: _description_
    :type exec_settings: fxt_types.exec_settings
    :param sut_settings: _description_
    :type sut_settings: conftest.SutTestSettings
    """
    exec_env = set_session_exec_env
    if not sut_settings.mock_sut:
        CSPEntryPoint.nr_of_subarrays = sut_settings.nr_of_subarrays
        exec_env.entrypoint = CSPEntryPoint
    else:
        exec_env.entrypoint = "mock"
    exec_env.scope = ["csp"]
    sut_settings.default_subarray_name = sut_settings.tel.csp.subarray(
        sut_settings.subarray_id
    )


# log checking


@pytest.fixture(name="set_up_subarray_log_checking_for_csp")
@pytest.mark.usefixtures("set_csp_entry_point")
def fxt_set_up_log_checking_for_csp(
    log_checking: fxt_types.log_checking,
    sut_settings: conftest.SutTestSettings,
):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    :param sut_settings: A class representing the settings for the system under test.
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        csp_subarray = str(tel.csp.subarray(sut_settings.subarray_id))
        log_checking.capture_logs_from_devices(csp_subarray)


# transition monitoring


@pytest.fixture(autouse=True)
def fxt_setup_transition_monitoring(
    context_monitoring: fxt_types.context_monitoring,
):
    """
    A fixture for setting up the transition monitoring.

    :param context_monitoring: An instance of the ContextMonitoring class
        containing context monitoring settings.
    :type context_monitoring: fxt_types.context_monitoring
    """
    tel = names.TEL()
    (
        context_monitoring.set_waiting_on(tel.csp.cbf.subarray(1))
        .for_attribute("obsstate")
        .and_observe()
    )


@pytest.fixture(name="csp_base_composition")
def fxt_csp_base_composition(tmp_path) -> conf_types.Composition:
    """Setup a base composition configuration to use for csp/cbf.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    composition = conf_types.CompositionByFile(
        tmp_path, conf_types.CompositionType.STANDARD
    )
    return composition


@pytest.fixture(name="csp_base_configuration")
def fxt_csp_base_configuration(tmp_path) -> conf_types.ScanConfiguration:
    """Setup a base scan configuration to use for csp/cbf.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    configuration = conf_types.ScanConfigurationByFile(
        tmp_path, conf_types.ScanConfigurationType.STANDARD
    )
    return configuration


@pytest.fixture(name="monitor_cbf")
def fxt_monitor_cbf(context_monitoring: fxt_types.context_monitoring):
    """
    A fixture for monitoring the CBF.

    :param context_monitoring: An instance of the ContextMonitoring class
        containing context monitoring settings.
    :type context_monitoring: fxt_types.context_monitoring
    """
    tel = names.TEL()
    (
        context_monitoring.set_waiting_on(tel.csp.cbf.subarray(1))
        .for_attribute("obsstate")
        .and_observe()
    )


# shared givens


@given("an CSP subarray", target_fixture="composition")
def an_csp_subarray(
    set_up_subarray_log_checking_for_csp,  # pylint: disable=unused-argument
    monitor_cbf,  # pylint: disable=unused-argument
    csp_base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """
    an CSP subarray.
    :param set_up_subarray_log_checking_for_csp: Object for
        set_up_subarray_log_checking_for_csp parameter.
    :param monitor_cbf: Object for monitor_cbf parameter.
    :param csp_base_composition: Object for csp_base_composition parameter.
    :return: A class representing the csp base configuration for the system under test.
    """
    return csp_base_composition


@given("an CSP subarray in IDLE state", target_fixture="configuration")
def an_csp_subarray_in_idle_state(
    set_up_subarray_log_checking_for_csp,  # pylint: disable=unused-argument
    csp_base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: conftest.SutTestSettings,
) -> None:
    """
    an CSP subarray in IDLE state.

    :param set_up_subarray_log_checking_for_csp: A fixture used for setting up
        subarray log checking for the CSP.
    :param csp_base_configuration: An instance of the ScanConfiguration class
        representing the CSP base configuration.
    :param subarray_allocation_spec: An instance of the SubarrayAllocationSpec class
        representing the subarray allocation specification.
    :param sut_settings: An instance of the SutTestSettings class
        representing the settings for the system under test.
    :return: A class representing the csp base configuration for the system under test.
    """
    subarray_allocation_spec.receptors = sut_settings.receptors
    subarray_allocation_spec.subarray_id = sut_settings.subarray_id
    return csp_base_configuration


@then(parsers.parse("the CSP subarray must be in {obsstate} state"))
def the_csp_subarray_must_be_in_some_obsstate(
    sut_settings: SutTestSettings,
    obsstate: ObsState,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """the subarray must be in IDLE state.

    :param sut_settings: An instance of SutTestSettings class
        containing test settings for the SUT.
    :type sut_settings: SutTestSettings

    :param obsstate: An instance of ObsState enum class representing the observation state.
    :type obsstate: ObsState

    :param integration_test_exec_settings: A dictionary containing the execution
        settings for the integration tests.
    :type integration_test_exec_settings: fxt_types.exec_settings
    """
    tel = names.TEL()
    csp_subarray_name = tel.csp.subarray(sut_settings.subarray_id)
    recorder = integration_test_exec_settings.recorder
    recorder.assert_no_devices_transitioned_after(
        str(csp_subarray_name), time_source="local"
    )
    csp_subarray = con_config.get_device_proxy(
        csp_subarray_name, fast_load=True
    )
    result = csp_subarray.read_attribute("obsstate").value

    assert_that(result).is_equal_to(eval(f"ObsState.{obsstate}"))
