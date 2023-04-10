"""Run scan on subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names


@pytest.mark.skamid
@pytest.mark.scan
@pytest.mark.sdp
@scenario("features/sdp_run_scan_on_subarray.feature", "Run a scan on a subarray - happy flow")
def test_run_a_scan_on_sdp_subarray_in_mid(run_scan_subarray_test_exec_settings):
    """CRun a scan on sdp subarray in Mid."""
    pass


@given("the subarray <subarray_id> obsState is READY")
def obs_state_is_ready(subarray_id):
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(
        tel.sdp.subarray(subarray_id)
    )
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)


@when("the user issues the scan command with a <scan_id> to the subarray <subarray_id>")
def issue_scan_command(scan_id, subarray_id):
    raise NotImplementedError(
        u'STEP: When the user issues the scan command with a <scan_id> to the subarray <subarray_id>')


@given("the subarray <subarray_id> obsState transitions to READY after the scan duration elapsed")
def obs_state_transitions_to_ready(subarray_id):
    result = None

    while result is None or result == ObsState.SCANNING:
        tel = names.TEL()
        sdp_subarray = con_config.get_device_proxy(
            tel.sdp.subarray(subarray_id)
        )
        result = sdp_subarray.read_attribute("obsstate").value

    assert_that(result).is_equal_to(ObsState.READY)


@then("the measurement set is present")
def measurement_set_is_present():
    raise NotImplementedError(u'STEP: Then the measurement set is present')


@then("the subarray <subarray_id> obsState transitions to SCANNING")
def step_impl():
    raise NotImplementedError(u'STEP: Then the subarray <subarray_id> obsState transitions to SCANNING')


@given("the <scan_id> is correctly represented in the measurement set")
def step_impl():
    raise NotImplementedError(u'STEP: And the <scan_id> is correctly represented in the measurement set')