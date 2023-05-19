"""
Pytest fixtures and bdd step implementations specific to cbf integration tests.
"""
import logging
import os
from typing import Callable

import pytest
from resources.models.cbf_model.entry_point import CBFEntryPoint
from resources.models.cbf_model.mocking import setup_cbf_mock
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from .. import conftest


@pytest.fixture(name="nr_of_subarrays", autouse=True, scope="session")
def fxt_nr_of_subarrays() -> int:
    # we only work with 1 subarray as CBF low currently
    # limits deployment of only 1
    # cbf mid only controls the state of subarray 1 so will also limit to 1
    return 1


@pytest.fixture(name="set_nr_of_subarray", autouse=True)
def fxt_set_nr_of_subarray(
    sut_settings: conftest.SutTestSettings, nr_of_subarrays: int
):
    """
    Set the number of subarrays in the SUT settings.

    :param sut_settings: _description_
    :type sut_settings: conftest.SutTestSettings
    :param nr_of_subarrays: The number of subarrays to set in the SUT settings.
    :type nr_of_subarrays: int
    """
    sut_settings.nr_of_subarrays = nr_of_subarrays


@pytest.fixture(name="set_cbf_entry_point", autouse=True)
def fxt_set_cbf_entry_point(
    set_nr_of_subarray,
    set_session_exec_env: fxt_types.set_session_exec_env,
    exec_settings: fxt_types.exec_settings,
    sut_settings: conftest.SutTestSettings,
):
    """_summary_
    :param set_nr_of_subarray: The number of subarrays to set in the SUT settings.
    :type set_nr_of_subarray: int
    :param set_session_exec_env: _description_
    :type set_session_exec_env: fxt_types.set_session_exec_env
    :param exec_settings: _description_
    :type exec_settings: fxt_types.exec_settings
    :param sut_settings: A class representing the settings for the system under test.
    :type sut_settings: conftest.SutTestSettings
    """
    exec_env = set_session_exec_env
    if not sut_settings.mock_sut:
        CBFEntryPoint.nr_of_subarrays = sut_settings.nr_of_subarrays
        exec_env.entrypoint = CBFEntryPoint
    else:
        exec_env.entrypoint = "mock"
    # include csp in scope when deployed
    if exec_env.telescope_type == "skalow":
        exec_env.scope = ["cbf scope", "csp controller"]
    else:
        exec_env.scope = ["cbf scope"]


# set online:
@pytest.fixture(autouse=True, scope="session")
def fxt_set_cbf_online_from_cbf(
    online: conftest.OnlineFlag,
    set_subsystem_online: Callable[[EntryPoint], None],
    nr_of_subarrays,
):
    """_summary_

    :param nr_of_subarrays: _description_
    :type nr_of_subarrays: int
    :param set_subsystem_online: _description_
    :type set_subsystem_online: Callable[[EntryPoint], None]
    :param online: An object for online flag
    :type online: conftest.OnlineFlag
    """
    if not online:
        if names.TEL().skalow:
            logging.info("setting cbf components online within cbf context")
            CBFEntryPoint.nr_of_subarrays = nr_of_subarrays
            entry_point = CBFEntryPoint()
            set_subsystem_online(entry_point)
            online.set_true()


# log checking


@pytest.fixture(name="set_up_log_checking_for_cbf_subarray")
@pytest.mark.usefixtures("set_cbf_entry_point")
def fxt_set_up_log_checking_for_cbf(
    log_checking: fxt_types.log_checking,
    sut_settings: conftest.SutTestSettings,
):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    :param sut_settings: A class representing the settings for the system under test.
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        cbf_subarray = str(tel.csp.cbf.subarray(sut_settings.subarray_id))
        log_checking.capture_logs_from_devices(cbf_subarray)


@pytest.fixture(name="cbf_base_composition")
def fxt_csp_base_composition(tmp_path) -> conf_types.Composition:
    """Setup a base composition configuration to use for csp/cbf.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    composition = conf_types.CompositionByFile(
        tmp_path, conf_types.CompositionType.STANDARD
    )
    return composition


# mocking


@pytest.fixture(name="setup_cbf_mock")
def fxt_setup_cbf_mock(mock_entry_point: fxt_types.mock_entry_point):
    """_summary_

    :param mock_entry_point: _description_
    :type mock_entry_point: fxt_types.mock_entry_point
    """
    setup_cbf_mock(mock_entry_point)
