"""Pytest fixtures and BDD step implementations specific to OET integration tests."""
import logging
import os

import pytest

from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_control.describing import mvp_names as names

from resources.models.tmc_model.entry_point import TMCEntryPoint
from .. import conftest


LOGGER = logging.getLogger(__name__)


@pytest.fixture(name="set_tmc_entry_point", autouse=True)
def fxt_set_entry_point(
    set_session_exec_env: fxt_types.set_session_exec_env,
    sut_settings: conftest.SutTestSettings,
):
    """Fixture to use for setting up the entry point as from only the interface to sdp."""
    exec_env = set_session_exec_env
    TMCEntryPoint.nr_of_subarrays = sut_settings.nr_of_subarrays
    exec_env.entrypoint = TMCEntryPoint
    #  TODO  determine correct scope for readiness checks to work
    exec_env.scope = ["sdp", "sdp control"]


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
        subarray = str(tel.tm.central_node)
        log_checking.capture_logs_from_devices(subarray)
