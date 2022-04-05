"""Pytest fixtures and bdd step implementations specific to csp integration tests."""
import os
from typing import Callable

import pytest
import logging

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from pytest_bdd import given

from resources.models.csp_model.entry_point import CSPEntryPoint


from .. import conftest


@pytest.fixture(name="nr_of_subarrays", autouse=True, scope="session")
def fxt_nr_of_subarrays() -> int:
    """_summary_

    :return: _description_
    :rtype: int
    """
    # we only work with 1 subarray as CBF low currently limits deployment of only 1
    # cbf mid only controls the state of subarray 1 so will also limit to 1
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

    :param sut_settings: _description_
    :type sut_settings: conftest.SutTestSettings
    """

    CSPEntryPoint.nr_of_subarrays = nr_of_subarrays
    sut_settings.nr_of_subarrays = nr_of_subarrays


@pytest.fixture(autouse=True, scope="session")
def fxt_set_cbf_online(
    set_subsystem_online: Callable[[EntryPoint], None], nr_of_subarrays: int
):
    """_summary_

    :param nr_of_subarrays: _description_
    :type nr_of_subarrays: int
    :param set_subsystem_online: _description_
    :type set_subsystem_online: Callable[[EntryPoint], None]
    """
    logging.info("setting csp components online")
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

    :param set_session_exec_env: _description_
    :type set_session_exec_env: fxt_types.set_session_exec_env
    :param exec_settings: _description_
    :type exec_settings: fxt_types.exec_settings
    :param sut_settings: _description_
    :type sut_settings: conftest.SutTestSettings
    """
    exec_env = set_session_exec_env
    exec_settings.time_out = 20
    if not sut_settings.mock_sut:
        CSPEntryPoint.nr_of_subarrays = sut_settings.nr_of_subarrays
        exec_env.entrypoint = CSPEntryPoint
    else:
        exec_env.entrypoint = "mock"
    exec_env.scope = ["csp"]


# log checking


@pytest.fixture(name="set_up_subarray_log_checking_for_csp")
@pytest.mark.usefixtures("set_csp_entry_point")
def fxt_set_up_log_checking_for_csp(
    log_checking: fxt_types.log_checking, sut_settings: conftest.SutTestSettings
):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        csp_subarray = str(tel.csp.subarray(sut_settings.subarray_id))
        log_checking.capture_logs_from_devices(csp_subarray)


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


# shared givens


@given("an CSP subarray in IDLE state")
def an_sdp_subarray_in_idle_state(
    set_up_subarray_log_checking_for_csp,  # pylint: disable=unused-argument
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: conftest.SutTestSettings,
) -> None:
    """an SDP subarray in IDLE state."""
    subarray_allocation_spec.receptors = sut_settings.receptors
    subarray_allocation_spec.subarray_id = sut_settings.subarray_id
