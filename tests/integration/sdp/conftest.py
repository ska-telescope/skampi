"""Pytest fixtures and bdd step implementations specific to sdp integration tests."""
import os

import pytest
from pytest_bdd import given

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

from resources.models.sdp_model.entry_point import SDPEntryPoint
from resources.models.sdp_model.mocking import setup_sdp_mock

from .. import conftest


@pytest.fixture(name="update_sut_settings")
def fxt_update_sut_settings(sut_settings: conftest.SutTestSettings):
    tel = names.TEL()
    if tel.skalow:
        sut_settings.nr_of_subarrays = 1


@pytest.fixture(name="set_sdp_entry_point", autouse=True)
def fxt_set_entry_point(
    set_session_exec_env: fxt_types.set_session_exec_env,
    update_sut_settings,
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


@pytest.fixture(name="sdp_start_up_test_exec_settings")
def fxt_sdp_start_up_test_exec_settings(
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """General startup test execution settings specific to sdp.

    :param exec_settings: Fixture as used by skallop
    """
    integration_test_exec_settings.time_out = 30


@pytest.fixture(name="assign_resources_test_exec_settings")
def fxt_sdp_assign_resources_exec_settings(
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """Set up test specific execution settings.

    :param exec_settings: The global test execution settings as a fixture.
    :return: test specific execution settings as a fixture
    """
    integration_test_exec_settings.time_out = 150


# log checking


@pytest.fixture(name="set_up_subarray_log_checking_for_sdp", autouse=True)
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


# resource configurations


@pytest.fixture(name="sdp_base_composition")
def fxt_sdp_base_composition(tmp_path) -> conf_types.Composition:
    """Setup a base composition configuration to use for sdp.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    composition = conf_types.CompositionByFile(
        tmp_path, conf_types.CompositionType.STANDARD
    )
    return composition


# scan configurations


@pytest.fixture(name="sdp_base_configuration")
def fxt_sdp_base_configuration(tmp_path) -> conf_types.ScanConfiguration:
    """Setup a base scan configuration to use for sdp.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    configuration = conf_types.ScanConfigurationByFile(
        tmp_path, conf_types.ScanConfigurationType.STANDARD
    )
    return configuration


# shared givens


@given("an SDP subarray in IDLE state", target_fixture="configuration")
def an_sdp_subarray_in_idle_state(
    set_up_subarray_log_checking_for_sdp,
    sdp_base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: conftest.SutTestSettings,
) -> conf_types.ScanConfiguration:
    """an SDP subarray in IDLE state."""
    subarray_allocation_spec.receptors = sut_settings.receptors
    subarray_allocation_spec.subarray_id = sut_settings.subarray_id
    # will use default composition for the allocated subarray
    # subarray_allocation_spec.composition
    sut_settings.default_subarray_name = sut_settings.tel.sdp.subarray(
        sut_settings.subarray_id
    )
    return sdp_base_configuration
