import os

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from ...conftest import SutTestSettings


@pytest.fixture(name="setup_log_checking")
def fxt_setup_log_checking(
    log_checking: fxt_types.log_checking,
    sut_settings: SutTestSettings,
):
    """ "
    A fixture to setup the log check

    :param log_checking: skallop fixture used to set up log checking.
    :param sut_settings: A class representing the settings for the system under test.
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        csp_subarray_leaf_node = str(tel.tm.subarray(sut_settings.subarray_id).csp_leaf_node)
        csp_subarray = str(tel.csp.subarray(sut_settings.subarray_id))
        log_checking.capture_logs_from_devices(csp_subarray_leaf_node, csp_subarray)


@pytest.mark.csp_related
@pytest.mark.skamid
@scenario("features/tmc_cspln_scan.feature", "Scan the csp mid using csp leaf node")
def test_scan_cspsubarray_for_a_scan_in_mid():
    """Scan cspsubarray for a scan in mid using the csp leaf node."""


@pytest.mark.csp_related
@pytest.mark.skalow
@scenario("features/tmc_cspln_scan.feature", "Scan the csp low using csp leaf node")
def test_scan_cspsubarray_for_a_scan_in_low():
    """Scan cspsubarray for a scan in low using the csp leaf node."""


@given("a CSP subarray in the READY state")
def a_csp():
    """a CSP subarray in the READY state."""


@given("a TMC CSP subarray Leaf Node", target_fixture="configuration")
def a_tmc_csp_subarray_leaf_node(set_csp_ln_entry_point, setup_log_checking):
    """
    a tmc CSP subarray leaf node.

    :param set_csp_ln_entry_point: An object to set csp leafnode entry point
    :param setup_log_checking: skallop fixture used to set up log checking.
    """


@then("the CSP subarray shall go from READY to SCANNING")
def the_csp_subarray_shall_go_from_ready_to_scanning_state(
    configured_subarray: fxt_types.configured_subarray,
):
    """
    the CSP subarray shall go from READY to SCANNING.

    :param configured_subarray: The configured subarray
    """
    tel = names.TEL()
    sub_array_id = configured_subarray.id
    csp_subarray = con_config.get_device_proxy(tel.csp.subarray(sub_array_id))
    result = csp_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.SCANNING)


@then("the CSP shall go back to READY when finished")
def the_csp_subarray_goes_back_to_ready_state(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    The CSP goes back to READY state when finished.

    :param configured_subarray: The configured subarray
    :param context_monitoring: Context monitoring object.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    tel = names.TEL()
    csp_subarray_name = tel.csp.subarray(configured_subarray.id)
    csp_subarray = con_config.get_device_proxy(csp_subarray_name)
    context_monitoring.re_init_builder()
    integration_test_exec_settings.attr_synching = True
    context_monitoring.wait_for(csp_subarray_name).for_attribute("obsstate").to_become_equal_to(
        "READY", ignore_first=False, settings=integration_test_exec_settings
    )
    result = csp_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)
