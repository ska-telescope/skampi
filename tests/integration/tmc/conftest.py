"""Pytest fixtures and bdd step implementations specific to tmc integration
tests."""
import logging
import os
from typing import Callable

import pytest
from resources.models.tmc_model.entry_point import TMCEntryPoint
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from .. import conftest

logger = logging.getLogger(__name__)


@pytest.fixture(name="set_tmc_entry_point", autouse=True)
@pytest.mark.usefixtures("set_up_subarray_log_checking_for_tmc")
def fxt_set_entry_point(
    nr_of_subarrays: int,
    set_session_exec_env: fxt_types.set_session_exec_env,
    sut_settings: conftest.SutTestSettings,
):
    """Fixture to use for setting up the entry point as from only the
    interface to sdp.
    :param nr_of_subarrays: The number of subarrays to set in the SUT settings.
    :param set_session_exec_env: A fixture to set session execution environment
    :param sut_settings: A class representing the settings for the system under test.
    """
    exec_env = set_session_exec_env
    sut_settings.nr_of_subarrays = nr_of_subarrays
    sut_settings.nr_of_receptors = 4
    TMCEntryPoint.nr_of_subarrays = sut_settings.nr_of_subarrays
    TMCEntryPoint.receptors = sut_settings.receptors
    exec_env.entrypoint = TMCEntryPoint
    # exec_env.maintain_on = True
    #  TODO  determine correct scope for readiness checks to work
    exec_env.scope = [
        # "tm",
        # "mid",
        "sdp",
        "csp",
        # "tmc scope",
        "csp scope",
        "csp control",
        "sdp control",
    ]


@pytest.fixture(name="nr_of_subarrays", autouse=True, scope="session")
def fxt_nr_of_subarrays() -> int:
    """_summary_

    :return: _description_
    :rtype: int
    """
    # we only work with 1 subarray as CBF low currently limits deployment of
    # only 1.
    # cbf mid only controls the state of subarray 1 so will also limit to 1
    tel = names.TEL()
    if tel.skalow:
        return 1
    return 2


@pytest.fixture(autouse=True, scope="session")
def fxt_set_csp_online_from_tmc(
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
    """
    if not online:
        logging.info("setting csp components online within tmc context")
        TMCEntryPoint.nr_of_subarrays = nr_of_subarrays
        entry_point = TMCEntryPoint()
        set_subsystem_online(entry_point)
        online.set_true()


@pytest.fixture(name="tmc_start_up_test_exec_settings", autouse=True)
def fxt_sdp_start_up_test_exec_settings(
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """General startup test execution settings specific to telescope from tmc.

    :param integration_test_exec_settings: Fixture as used by skallop
    """
    integration_test_exec_settings.time_out = 100


@pytest.fixture(name="assign_resources_test_exec_settings", autouse=True)
def fxt_tmc_assign_resources_exec_settings(
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """Set up test specific execution settings.

    :param integration_test_exec_settings: The global test execution settings as a fixture.
    """
    integration_test_exec_settings.time_out = 100


# log checking


@pytest.fixture(name="set_up_subarray_log_checking_for_tmc")
def fxt_set_up_log_capturing_for_cbf(
    log_checking: fxt_types.log_checking,
    sut_settings: conftest.SutTestSettings,
):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    :param sut_settings: A class representing the settings for the system under test.
    """
    index = sut_settings.subarray_id
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        subarray = str(tel.tm.subarray(index))
        sdp_subarray1 = str(tel.sdp.subarray(index))
        if tel.skamid:
            subarray_ln = str(tel.skamid.tm.subarray(index).sdp_leaf_node)
            log_checking.capture_logs_from_devices(subarray, sdp_subarray1, subarray_ln)
        else:
            subarray_ln = str(tel.skalow.tm.subarray(index).sdp_leaf_node)
            log_checking.capture_logs_from_devices(subarray, sdp_subarray1, subarray_ln)


# resource configurations


@pytest.fixture(name="base_composition")
def fxt_sdp_base_composition(tmp_path) -> conf_types.Composition:
    """Setup a base composition configuration to use for sdp.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    composition = conf_types.CompositionByFile(tmp_path, conf_types.CompositionType.STANDARD)
    return composition


# scan configurations


@pytest.fixture(name="base_configuration")
def fxt_sdp_base_configuration(tmp_path) -> conf_types.ScanConfiguration:
    """Setup a base scan configuration to use for sdp.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    configuration = conf_types.ScanConfigurationByFile(
        tmp_path, conf_types.ScanConfigurationType.STANDARD
    )
    return configuration


@pytest.fixture(autouse=True)
def override_timeouts(exec_settings):
    """
    Sets timeout for test environment.
    :param exec_settings: _Description_
    """
    exec_settings.time_out = 100
