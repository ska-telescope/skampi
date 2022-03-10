"""Pytest fixtures and bdd step implementations specific to sdp integration tests."""
import os

import pytest

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.sdp_model.entry_point import SDPEntryPoint
from resources.models.sdp_model.mocking import setup_sdp_mock

from .. import conftest


@pytest.fixture(name="set_sdp_entry_point", autouse=True)
def fxt_set_entry_point(
    set_session_exec_env: fxt_types.set_session_exec_env,
    sut_settings: conftest.SutTestSettings,
):
    """Fixture to use for setting up the entry point as from only the interface to sdp."""
    exec_env = set_session_exec_env
    if not sut_settings.mock_sut:
        SDPEntryPoint.nr_of_subarrays = sut_settings.nr_of_subarrays
        exec_env.entrypoint = SDPEntryPoint
    else:
        exec_env.entrypoint = "mock"
    exec_env.scope = ["sdp"]


@pytest.fixture(name="setup_sdp_mock")
def fxt_setup_sdp_mock(mock_entry_point: fxt_types.mock_entry_point):
    """Fixture to use for injecting a mocked entrypoin for sdp in stead of the real one."""
    setup_sdp_mock(mock_entry_point)


@pytest.fixture(name="sdp_start_up_test_exec_settings", autouse=True)
def fxt_sdp_start_up_test_exec_settings(
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """General startup test execution settings specific to sdp.

    :param exec_settings: Fixture as used by skallop
    """
    integration_test_exec_settings.time_out = 30


@pytest.fixture(name="assign_resources_test_exec_settings", autouse=True)
def fxt_sdp_assign_resources_exec_settings(
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """Set up test specific execution settings.

    :param exec_settings: The global test execution settings as a fixture.
    :return: test specific execution settings as a fixture
    """
    integration_test_exec_settings.time_out = 150


# log checking


@pytest.fixture(name="set_up_log_checking_for_sdp", autouse=True)
@pytest.mark.usefixtures("set_sdp_entry_point")
def fxt_set_up_log_capturing_for_cbf(
    log_checking: fxt_types.log_checking, sut_settings: conftest.SutTestSettings
):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        sdp_subarray = str(tel.sdp.subarray(sut_settings.subarray_id))
        log_checking.capture_logs_from_devices(sdp_subarray)
