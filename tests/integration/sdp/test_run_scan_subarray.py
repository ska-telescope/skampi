"""Run scan on subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from resources.models.mvp_model.states import ObsState

from .. import conftest

@pytest.mark.skamid
@pytest.mark.scan
@pytest.mark.sdp
@scenario("features/sdp_run_scan_on_subarray.feature", "Run a scan on a subarray - happy flow")
def test_run_a_scan_on_sdp_subarray_in_mid(run_scan_subarray_test_exec_settings):
    """CRun a scan on sdp subarray in Mid."""
    pass


@given("the subarray {subarray_id:d} obsState is READY", target_fixture="composition")
def obs_state_is_ready(subarray_id):
    tel = names.TEL()
    sdp_subarray = con_config.get_device_proxy(
        tel.sdp.subarray(subarray_id)
    )
    result = sdp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)


@when("I issue the scan command with a {scan_ID:d} to the subarray {subarray_id:d} and the scan completes", target_fixture="composition")
def issue_scan_command(scan_id, subarray_id):
    raise Exception("Not Implemented")


@then("the subarray {subarray_id:d} obsState transitions to READY", target_fixture="composition")
def obs_state_transitions_to_ready(subarray_id):

    result = None

    while result is None or result == ObsState.SCANNING:
        tel = names.TEL()
        sdp_subarray = con_config.get_device_proxy(
            tel.sdp.subarray(subarray_id)
        )
        result = sdp_subarray.read_attribute("obsstate").value 

    assert_that(result).is_equal_to(ObsState.READY)


@then("the measurement set is present", target_fixture="composition")
def measurement_set_is_present():
    raise Exception("Not Implemented")


@then("the {scan_id:d} is correctly represented in the measurement set", target_fixture="composition")
def scan_id_is_in_measurement_set(scan_id):
    raise Exception("Not Implemented")