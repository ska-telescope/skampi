"""Configure scan on subarray feature tests."""
import os

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState

SCAN_DURATION = 1
RECEPTORS = [1, 2]
SUB_ARRAY_ID = 1


@pytest.fixture(name="run_scan_test_exec_settings")
def fxt_run_scan_test_exec_settings(
    exec_settings: fxt_types.exec_settings,
) -> fxt_types.exec_settings:
    """Set up test specific execution settings.

    :param exec_settings: The global test execution settings as a fixture.
    :return: test specific execution settings as a fixture
    """
    run_scan_test_exec_settings = exec_settings.replica()
    run_scan_test_exec_settings.time_out = 150
    if os.getenv("DEBUG"):
        exec_settings.run_with_live_logging()
        run_scan_test_exec_settings.run_with_live_logging()
    elif os.getenv("LIVE_LOGGING"):
        run_scan_test_exec_settings.run_with_live_logging()
    elif os.getenv("REPLAY_EVENTS_AFTERWARDS"):
        run_scan_test_exec_settings.replay_events_afterwards()
    return run_scan_test_exec_settings


# scan configurations


@pytest.fixture(name="sdp_base_configuration")
def fxt_sdp_base_composition(tmp_path) -> conf_types.ScanConfiguration:
    """Setup a base scan configuration to use for sdp.

    :param tmp_path: a temporary path for sending configuration as a file.
    :return: the configuration settings.
    """
    configuration = conf_types.ScanConfigurationByFile(
        tmp_path, conf_types.ScanConfigurationType.STANDARD
    )
    return configuration


# log capturing


@pytest.fixture(name="set_up_log_checking_for_sdp")
@pytest.mark.usefixtures("set_sdp_entry_point")
def fxt_set_up_log_capturing_for_sdp(log_checking: fxt_types.log_checking):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        sdp_subarray = str(tel.sdp.subarray(SUB_ARRAY_ID))
        log_checking.capture_logs_from_devices(sdp_subarray)


@pytest.mark.skalow
@pytest.mark.scan
@scenario("features/sdp_scan.feature", "Run a scan on sdp subarray in low")
def test_run_a_scan_on_sdp_subarray_in_low():
    """CRun a scan on sdp subarray in low."""


@pytest.mark.skamid
@pytest.mark.scan
@scenario("features/sdp_scan.feature", "Run a scan on sdp subarray in mid")
def test_run_a_scan_on_sdp_subarray_in_mid():
    """Run a scan on sdp subarray in mid."""


@given("an SDP subarray in READY state")
def an_sdp_subarray_in_ready_state(
    run_scan_test_exec_settings,  # pylint: disable=unused-argument
    set_sdp_entry_point,  # pylint: disable=unused-argument
    set_up_log_checking_for_sdp,  # pylint: disable=unused-argument
    sdp_base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
) -> conf_types.ScanConfiguration:
    """an SDP subarray in READY state."""
    subarray_allocation_spec.receptors = RECEPTORS
    subarray_allocation_spec.subarray_id = SUB_ARRAY_ID
    # will use default composition for the allocated subarray
    # subarray_allocation_spec.composition
    return sdp_base_configuration


@when("I command it to scan for a given period")
def i_command_it_to_scan(
    configured_subarray: fxt_types.configured_subarray,
    run_scan_test_exec_settings: fxt_types.exec_settings,
):
    """I configure it for a scan."""
    configured_subarray.set_to_scanning(run_scan_test_exec_settings)


@then("the SDP subarray must be in the SCANNING state until finished")
def the_sdp_subarray_must_be_in_the_scanning_state(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    run_scan_test_exec_settings: fxt_types.exec_settings,
):
    """the SDP subarray must be in the SCANNING state until finished."""
    tel = names.TEL()
    sdp_subarray_name = tel.sdp.subarray(configured_subarray.id)
    sdp_subarray = con_config.get_device_proxy(sdp_subarray_name)

    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.SCANNING)
    # afterwards it must be ready
    context_monitoring.wait_for(sdp_subarray_name).for_attribute(
        "obsstate"
    ).to_become_equal_to(
        "READY", ignore_first=False, settings=run_scan_test_exec_settings
    )
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)
