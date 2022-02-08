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

SCAN_DURATION = 2
RECEPTORS = [1, 2]
SUB_ARRAY_ID = 1


@pytest.fixture(name="configure_scan_test_exec_settings")
def fxt_configure_scan_test_exec_settings(
    exec_settings: fxt_types.exec_settings,
) -> fxt_types.exec_settings:
    """Set up test specific execution settings.

    :param exec_settings: The global test execution settings as a fixture.
    :return: test specific execution settings as a fixture
    """
    configure_scan_test_exec_settings = exec_settings.replica()
    configure_scan_test_exec_settings.time_out = 150
    if os.getenv("DEBUG"):
        exec_settings.run_with_live_logging()
        configure_scan_test_exec_settings.run_with_live_logging()
    elif os.getenv("LIVE_LOGGING"):
        configure_scan_test_exec_settings.run_with_live_logging()
    elif os.getenv("REPLAY_EVENTS_AFTERWARDS"):
        configure_scan_test_exec_settings.replay_events_afterwards()
    return configure_scan_test_exec_settings


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


@pytest.fixture(name="csp_base_configuration")
def fxt_csp_base_configuration(tmp_path) -> conf_types.ScanConfiguration:
    """Setup a base scan configuration to use for csp/cbf.

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


@pytest.fixture(name="set_up_log_checking_for_cbf")
@pytest.mark.usefixtures("set_cbf_entry_point")
def fxt_set_up_log_checking_for_cbf(log_checking: fxt_types.log_checking):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        cbf_subarray = str(tel.csp.cbf.subarray(SUB_ARRAY_ID))
        log_checking.capture_logs_from_devices(cbf_subarray)


@pytest.mark.skip(reason="test still in dev phase")
@scenario(
    "features/sdp_configure_scan.feature", "Configure scan on sdp subarray in low"
)
def test_configure_scan_on_sdp_subarray_in_low():
    """Configure scan on sdp subarray in low."""


# @pytest.mark.skip(reason="test still in dev phase")
@scenario(
    "features/sdp_configure_scan.feature", "Configure scan on sdp subarray in mid"
)
def test_configure_scan_on_sdp_subarray_in_mid():
    """Configure scan on sdp subarray in mid."""


@scenario("features/cbf_configure_scan.feature", "Configure scan on CBF mid subarray")
def test_configure_scan_on_cbf_mid_subarray():
    """Configure scan on CBF mid subarray."""


@given("an SDP subarray in IDLE state", target_fixture="configuration")
def an_sdp_subarray_in_idle_state(
    configure_scan_test_exec_settings,  # pylint: disable=unused-argument
    set_sdp_entry_point,  # pylint: disable=unused-argument
    set_up_log_checking_for_sdp,  # pylint: disable=unused-argument
    sdp_base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
) -> conf_types.ScanConfiguration:
    """an SDP subarray in IDLE state."""
    subarray_allocation_spec.receptors = RECEPTORS
    subarray_allocation_spec.subarray_id = SUB_ARRAY_ID
    # will use default composition for the allocated subarray
    # subarray_allocation_spec.composition
    return sdp_base_configuration


@given("an CBF subarray in IDLE state", target_fixture="configuration")
def an_cbf_subarray_in_idle_state(
    configure_scan_test_exec_settings,  # pylint: disable=unused-argument
    set_cbf_entry_point,  # pylint: disable=unused-argument
    set_up_log_checking_for_cbf,  # pylint: disable=unused-argument
    csp_base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
) -> conf_types.ScanConfiguration:
    """Given an CBF subarray in IDLE state."""
    subarray_allocation_spec.receptors = RECEPTORS
    subarray_allocation_spec.subarray_id = SUB_ARRAY_ID
    # will use default composition for the allocated subarray
    # subarray_allocation_spec.composition
    return csp_base_configuration


@when("I configure it for a scan")
def i_configure_it_for_a_scan(
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
    entry_point: fxt_types.entry_point,
    configuration: conf_types.ScanConfiguration,
    configure_scan_test_exec_settings: fxt_types.exec_settings,
):
    """I configure it for a scan."""
    sub_array_id = allocated_subarray.id
    receptors = allocated_subarray.receptors
    sb_id = allocated_subarray.sb_config.sbid

    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_configuring_a_subarray(
            configure_scan_test_exec_settings
        ):
            entry_point.configure_subarray(
                sub_array_id, receptors, configuration, sb_id, SCAN_DURATION
            )


@then("the subarray must be in the READY state")
def the_subarray_must_be_in_the_ready_state(
    allocated_subarray: fxt_types.allocated_subarray,
):
    """the subarray must be in the READY state."""
    sub_array_id = allocated_subarray.id
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(tel.sdp.subarray(sub_array_id))
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)


@then("the CBF subarray must be in the READY state")
def the_cbf_subarray_must_be_in_the_ready_state(
    allocated_subarray: fxt_types.allocated_subarray,
):
    """the subarray must be in the READY state."""
    sub_array_id = allocated_subarray.id
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(tel.csp.cbf.subarray(sub_array_id))
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)


@pytest.mark.skip(reason="only run this test for diagnostic purposes during dev")
@pytest.mark.usefixtures("setup_sdp_mock")
def test_test_sdp_configure_scan(run_mock):
    """Test the test using a mock SUT"""
    run_mock(test_configure_scan_on_sdp_subarray_in_mid)
