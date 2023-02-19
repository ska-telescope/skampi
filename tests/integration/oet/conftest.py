"""Pytest fixtures and BDD step implementations specific to OET integration tests."""
import logging
import os
from typing import Callable

import pytest

from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.entry_points.base import EntryPoint

from resources.models.tmc_model.entry_point import TMCEntryPoint
from .. import conftest


LOGGER = logging.getLogger(__name__)


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
    """
    if not online:
        logging.info("setting csp components online within tmc context")
        TMCEntryPoint.nr_of_subarrays = nr_of_subarrays
        entry_point = TMCEntryPoint()
        set_subsystem_online(entry_point)
        online.set_true()


@pytest.fixture(name="set_tmc_entry_point", autouse=True)
def fxt_set_entry_point(
    set_session_exec_env: fxt_types.set_session_exec_env,
    sut_settings: conftest.SutTestSettings,
):
    """Fixture to use for setting up the entry point as from only the interface to sdp."""
    exec_env = set_session_exec_env
    sut_settings.nr_of_subarrays = 1
    TMCEntryPoint.nr_of_subarrays = sut_settings.nr_of_subarrays
    exec_env.entrypoint = TMCEntryPoint
    #  TODO  determine correct scope for readiness checks to work
    exec_env.scope = ["tmc", "mid"]

@pytest.fixture(name="base_configuration")
def fxt_oet_base_configuration(tmp_path) -> conf_types.ScanConfiguration:
    """Setup a base scan configuration to use for oet.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    configuration = conf_types.ScanConfigurationByFile(
        tmp_path, conf_types.ScanConfigurationType.STANDARD
    )
    return configuration

# log checking


@pytest.fixture(name="set_up_tmc_log_checking", autouse=True)
@pytest.mark.usefixtures("set_tmc_entry_point")
def fxt_set_up_log_capturing_for_cbf(
    log_checking: fxt_types.log_checking, sut_settings: conftest.SutTestSettings
):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        subarray = str(tel.tm.subarray(1))
        log_checking.capture_logs_from_devices(subarray)
        