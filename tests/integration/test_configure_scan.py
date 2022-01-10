"""Configure scan on subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_control.event_waiting.wait import wait_for
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

SCAN_DURATION = 2


@pytest.mark.skip(reason="test still in dev phase")
@scenario(
    "features/sdp_configure_scan.feature", "Configure scan on sdp subarray in low"
)
def test_configure_scan_on_sdp_subarray_in_low():
    """Configure scan on sdp subarray in low."""


@pytest.mark.skip(reason="test still in dev phase")
@scenario(
    "features/sdp_configure_scan.feature", "Configure scan on sdp subarray in mid"
)
def test_configure_scan_on_sdp_subarray_in_mid():
    """Configure scan on sdp subarray in mid."""


@given("an SDP subarray in IDLE state")
def an_sdp_subarray_in_idle_state(set_sdp_entry_point):
    """an SDP subarray in IDLE state."""


@when("I configure it for a scan")
def i_configure_it_for_a_scan(
    allocated_subarray: fxt_types.allocated_subarray,
    exec_settings: fxt_types.exec_settings,
    entry_point: fxt_types.entry_point,
    tmp_path,
):
    """I configure it for a scan."""
    sub_array_id = allocated_subarray.id
    receptors = allocated_subarray.receptors
    sb_id = allocated_subarray.sb_config.sbid
    configuration = conf_types.ScanConfigurationByFile(
        tmp_path, conf_types.ScanConfigurationType.STANDARD
    )
    allocated_subarray.clear_configuration_when_finished(exec_settings)
    with wait_for(entry_point.set_waiting_for_configure(sub_array_id, receptors)):
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


@pytest.mark.skip(reason="only run this test for diagnostic purposes during dev")
@pytest.mark.usefixtures("setup_sdp_mock")
def test_test_sdp_configure_scan(run_mock):
    """Test the test using a mock SUT"""
    run_mock(test_configure_scan_on_sdp_subarray_in_mid)
