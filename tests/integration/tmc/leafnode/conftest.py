"""Pytest fixtures and bdd step implementations specific to tmc integration tests."""

import os
import pytest

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from resources.models.tmc_model.leafnodes.cspln_entry_point import (
    CSPLnEntryPoint
)

from tests.integration import conftest

@pytest.fixture(name="set_csp_ln_entry_point", autouse=True)
def fxt_set_entry_point(
    nr_of_subarrays: int,
    set_session_exec_env: fxt_types.set_session_exec_env,
    sut_settings: conftest.SutTestSettings,
):
    """Fixture to use for setting up the entry point as from only the interface to csp."""
    exec_env = set_session_exec_env
    sut_settings.nr_of_subarrays = nr_of_subarrays
    CSPLnEntryPoint.nr_of_subarrays = sut_settings.nr_of_subarrays
    exec_env.entrypoint = CSPLnEntryPoint
    #  TODO  determine correct scope for readiness checks to work
    exec_env.scope = [
        "csp",
        "csp control",
    ]


@pytest.fixture(name="set_up_subarray_log_checking_for_csp_ln", autouse=True)
@pytest.mark.usefixtures("set_csp_ln_entry_point")
def fxt_set_up_log_capturing_for_csp(
    log_checking: fxt_types.log_checking,
    sut_settings: conftest.SutTestSettings
):
    """Set up log capturing (if enabled by CAPTURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    """

    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        if tel.skamid:
            subarrays = [
                str(tel.skamid.tm.subarray(index).csp_leaf_node)
                for index in range(1, sut_settings.nr_of_subarrays + 1)
            ]
            log_checking.capture_logs_from_devices(*subarrays)