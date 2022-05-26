"""Pytest fixtures and bdd step implementations specific to tmc integration tests."""
import os

import pytest

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

from resources.models.tmc_model.entry_point import TMCEntryPoint

from .. import conftest


@pytest.fixture(name="set_tmc_entry_point", autouse=True)
def fxt_set_entry_point(
    set_session_exec_env: fxt_types.set_session_exec_env,
    sut_settings: conftest.SutTestSettings,
):
    """Fixture to use for setting up the entry point as from only the interface to sdp."""
    exec_env = set_session_exec_env
    sut_settings.receptors = [1]
    TMCEntryPoint.nr_of_subarrays = sut_settings.nr_of_subarrays
    exec_env.entrypoint = TMCEntryPoint
    #  TODO  determine correct scope for readiness checks to work
    exec_env.scope = ["sdp", "sdp control"]


@pytest.fixture(name="tmc_start_up_test_exec_settings", autouse=True)
def fxt_sdp_start_up_test_exec_settings(
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """General startup test execution settings specific to telescope from tmc.

    :param exec_settings: Fixture as used by skallop
    """
    integration_test_exec_settings.time_out = 30


@pytest.fixture(name="assign_resources_test_exec_settings", autouse=True)
def fxt_tmc_assign_resources_exec_settings(
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """Set up test specific execution settings.

    :param exec_settings: The global test execution settings as a fixture.
    :return: test specific execution settings as a fixture
    """
    integration_test_exec_settings.time_out = 30


# log checking


@pytest.fixture(name="set_up_subarray_log_checking_for_tmc", autouse=True)
@pytest.mark.usefixtures("set_tmc_entry_point")
def fxt_set_up_log_capturing_for_cbf(
    log_checking: fxt_types.log_checking, sut_settings: conftest.SutTestSettings
):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        subarray = str(tel.tm.subarray(sut_settings.subarray_id))
        log_checking.capture_logs_from_devices(subarray)


# resource configurations


@pytest.fixture(name="base_composition")
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
