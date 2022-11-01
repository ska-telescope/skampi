"""Pytest fixtures and bdd step implementations specific to tmc integration tests."""

import os
import pytest

from pytest_bdd import given
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from resources.models.tmc_model.leafnodes.sdpln_entry_point import (
    SDPLnEntryPoint
)
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

from ... import conftest

@pytest.fixture(name="set_sdp_ln_entry_point", autouse=True)
def fxt_set_entry_point(
    nr_of_subarrays: int,
    set_session_exec_env: fxt_types.set_session_exec_env,
    sut_settings: conftest.SutTestSettings,
):
    """Fixture to use for setting up the entry point as from only the interface to sdp."""
    exec_env = set_session_exec_env
    sut_settings.nr_of_subarrays = nr_of_subarrays
    SDPLnEntryPoint.nr_of_subarrays = sut_settings.nr_of_subarrays
    exec_env.entrypoint = SDPLnEntryPoint
    #  TODO  determine correct scope for readiness checks to work
    exec_env.scope = [
        "sdp",
        "sdp control",
    ]


@pytest.fixture(name="set_up_subarray_log_checking_for_sdp_ln", autouse=True)
@pytest.mark.usefixtures("set_sdp_ln_entry_point")
def fxt_set_up_log_capturing_for_sdp(
    log_checking: fxt_types.log_checking,
    sut_settings: conftest.SutTestSettings
):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    """

    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        if tel.skamid:
            subarrays = [
                str(tel.skamid.tm.subarray(index).sdp_leaf_node)
                for index in range(1, sut_settings.nr_of_subarrays + 1)
            ]
            log_checking.capture_logs_from_devices(*subarrays)


@given("an SDP subarray in the IDLE state", target_fixture="configuration")
def an_sdp_subarray_in_idle_state(
    sdp_base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: conftest.SutTestSettings,
) -> conf_types.ScanConfiguration:
    """an SDP subarray in the IDLE state."""
    subarray_allocation_spec.receptors = sut_settings.receptors
    subarray_allocation_spec.subarray_id = sut_settings.subarray_id
    # will use default composition for the allocated subarray
    # subarray_allocation_spec.composition
    return sdp_base_configuration
