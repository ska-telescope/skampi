import logging

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when, parsers
from resources.models.mvp_model.states import ObsState
from ska_oso_scripting.objects import SubArray
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types, SubarrayConfigurationSpec

from .. import conftest
from resources.models.mvp_model.configuration import SKAScanConfiguration
from resources.models.mvp_model.env import Observation


"""
test_XTP-18866
----------------------------------
Tests to Run a scan on low subarray from OET (XTP-19865)
"""

"""Scan on telescope subarray feature tests."""


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.scan
@scenario("features/oet_scan.feature", "Run a scan on low subarray from OET")
def test_oet_scan_on_low_subarray():
    """Run a scan on OET low telescope subarray."""

@pytest.mark.skalow
@pytest.mark.scan
@pytest.mark.oet
@scenario(
    "features/oet_multi_scan.feature",
    "Run multiple scans on TMC subarray in low for same scan type",
)
def test_multiple_scans_on_tmc_subarray_in_low():
    """Run multiple scans on TMC subarray in low."""

@pytest.mark.k8s
@pytest.mark.oet
@pytest.mark.skalow
@pytest.mark.scanning
@scenario(
    "features/oet_multi_scan.feature",
    "Run multiple scans on TMC subarray in low for different scan type from OET",
)
def test_multiple_scans_on_tmc_subarray_in_low_for_different_scantype():
    """Run multiple scans on TMC subarray in low for different scan type from OET"""

@pytest.mark.k8s
@pytest.mark.oet
@pytest.mark.scan
@pytest.mark.skamid
@scenario("features/oet_multi_scan.feature", "Run multiple scans on mid subarray for same scan type from OET")
def test_oet_multi_scan_on_mid_subarray():
    """Run multiple scans on mid subarray for same scan type from OET."""

@pytest.mark.k8s
@pytest.mark.oet
@pytest.mark.skamid
@pytest.mark.scanning
@scenario("features/oet_multi_scan.feature","Run multiple scans on mid subarray for different scan type from OET")
def test_oet_multi_scan_on_mid_subarray_for_different_scantype():
    """Run multiple scans on mid subarray for different scan type from OET"""

@given("an OET")
def a_oet():
    """an OET"""

@given("an subarray that has just completed it's first scan")
def an_subarray_that_has_just_completed_its_first_scan(
    configured_subarray: fxt_types.configured_subarray,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    configured_subarray.scan(integration_test_exec_settings)

@given("a subarray in READY state", target_fixture="scan")
def a_low_subarray_in_ready_state(
    base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: conftest.SutTestSettings,
) -> conf_types.ScanConfiguration:
    """a subarray in READY state"""
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
    """I configure it for a scan using OET scan() command."""
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
    """The subarray must be in the SCANNING state until finished and check if the obsState is READY."""
    recorder = integration_test_exec_settings.recorder
    tel = names.TEL()
    tmc_subarray_name = str(tel.tm.subarray(configured_subarray.id))
    tmc_subarray = con_config.get_device_proxy(tmc_subarray_name)
    tmc_state_changes = recorder.get_transitions_for(
        tmc_subarray_name, "obsstate"
    )
    tmc_state_changes = recorder.get_transitions_for(tmc_subarray_name, "obsstate")
    assert_that(tmc_state_changes).is_equal_to(["READY", "SCANNING", "READY"])
    result = tmc_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)

@given(
    parsers.parse(
        "a subarray defined to perform scans for types {scan_target1} "
        "and {scan_target2}"
    ),
    target_fixture="scan_targets",
)
def a_subarray_defined_to_perform_scan_types(
    scan_target1: str,
    scan_target2: str,
    observation_config: Observation,
) -> dict[str, str]:
    """The subarray is defined to perform scans for provided scan types by validating the scan types."""
    scan_target = [scan_target1,scan_target2]
    # check that we have targets referencing this scan types
    scan_targets = {
        target_spec.scan_type: target_name
        for target_name, target_spec in observation_config.target_specs.items()
    }
    for scan_t in scan_target:
        assert (
			scan_t in observation_config.scan_type_configurations
		), f"Scan target {scan_t} not defined"
        assert scan_targets.get(
            scan_t
        ), f"Scan target {scan_t} not defined as part of scan targets"
    return scan_targets

@when(
    parsers.parse("I configure the subarray again for scan type {scan_type}"),
    target_fixture="configured_subarray",
)
@given(
    parsers.parse("a subarray configured for scan type {scan_type}"),
    target_fixture="configured_subarray",
)

def a_subarray_configured_for_scan_type(
    scan_type: str,
    factory_configured_subarray: fxt_types.factory_configured_subarray,
    observation_config: Observation,
    sut_settings: conftest.SutTestSettings,
    scan_targets: dict[str, str],
):
    """a subarray configured for scan type {scan_type}"""
    scan_duration = sut_settings.scan_duration
    configuration = SKAScanConfiguration(observation_config)
    configuration.set_next_target_to_be_configured(scan_targets[scan_type])
    configuration_specs = SubarrayConfigurationSpec(scan_duration, configuration)
    return factory_configured_subarray(
        injected_subarray_configuration_spec=configuration_specs
    )
