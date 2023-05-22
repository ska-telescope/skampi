import logging

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from resources.models.mvp_model.states import ObsState
from ska_oso_scripting.objects import SubArray
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from .. import conftest

"""
test_XTP-18866
----------------------------------
Tests to Run a scan on low subarray from OET (XTP-19865)
"""

"""Scan on telescope subarray feature tests."""


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.scan
@scenario("features/oet_scan.feature", "Run a scan on low subarray from OET")
def test_oet_scan_on_low_subarray():
    """Run a scan on OET low telescope subarray."""


@given("an OET")
def a_oet():
    """an OET"""


@given("a subarray in READY state", target_fixture="scan")
def a_low_subarray_in_ready_state(
    base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: conftest.SutTestSettings,
) -> conf_types.ScanConfiguration:
    """
    a subarray in READY state
    :param base_configuration: the base scan configuration.
    :param subarray_allocation_spec: the specification for the subarray allocation.
    :param sut_settings: the SUT test settings.
    :return: the base configuration for the subarray.`
    """
    subarray_allocation_spec.receptors = sut_settings.receptors
    subarray_allocation_spec.subarray_id = sut_settings.subarray_id
    return base_configuration


@when("I command it to scan for a given period")
def i_command_it_to_scan_low(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: conftest.SutTestSettings,
):
    """
    I configure it for a scan.
    :param configured_subarray: The configured subarray
    :param context_monitoring: Context monitoring object.
    :param integration_test_exec_settings: The integration test execution settings.
    :param sut_settings: SUT settings object.

    """
    subarray_id = sut_settings.subarray_id
    tel = names.TEL()
    context_monitoring.set_waiting_on(
        tel.tm.subarray(subarray_id)
    ).for_attribute("obsstate").to_change_in_order(["SCANNING", "READY"])
    integration_test_exec_settings.attr_synching = False
    logging.info(
        "context_monitoring._wait_after_setting_builder ="
        f" {context_monitoring._wait_after_setting_builder}"
    )
    with context_monitoring.observe_while_running(
        integration_test_exec_settings
    ) as concurrent_monitoring:
        subarray = SubArray(subarray_id)
        subarray.scan()  # this is a blocking command
        concurrent_monitoring.wait_until_complete()


@then("the subarray must be in the SCANNING state until finished")
def the_subarray_must_be_in_the_scanning_state(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    The subarray must be in the SCANNING state until finished.
    :param configured_subarray: The configured subarray
    :param context_monitoring: Context monitoring object.
    :param integration_test_exec_settings: The integration test execution settings.

    :raises AssertionError: If the subarray is not in the expected state.

    """
    recorder = integration_test_exec_settings.recorder
    tel = names.TEL()
    tmc_subarray_name = str(tel.tm.subarray(configured_subarray.id))
    tmc_subarray = con_config.get_device_proxy(tmc_subarray_name)
    tmc_state_changes = recorder.get_transitions_for(
        tmc_subarray_name, "obsstate"
    )
    try:
        assert_that(tmc_state_changes).is_equal_to(
            ["READY", "SCANNING", "READY"]
        )
    except AssertionError as error:
        logging.info(f"events recorded not correct: {recorder._occurrences}")
        raise error
    result = tmc_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)
