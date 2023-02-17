"""
test_XTP-
---------------------------------------------------------
Tests for Configuring a scan on low telescope subarray using OET from scan duration (XTP-).
"""
import pytest
from assertpy import assert_that
from pytest_bdd import given, when, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_oso_scripting.objects import SubArray
from resources.models.mvp_model.states import ObsState
from ..conftest import SutTestSettings

@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.configure
@scenario("features/oet_configure_scan.feature", "Configure the low telescope subarray using OET")
def test_oet_configure_scan_on_low_subarray():
    """Configure scan on OET low telescope subarray."""


@given("an OET")
def an_oet():
    """an OET"""

@given("a low telescope subarray in IDLE state")
def a_subarray_in_the_idle_state(
    running_telescope: fxt_types.running_telescope,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """I assign resources to it in low."""

    subarray_id = sut_settings.subarray_id
    subarray = SubArray(subarray_id)
    receptors = sut_settings.receptors
    observation = sut_settings.observation
    with context_monitoring.context_monitoring():
        with running_telescope.wait_for_allocating_a_subarray(
            subarray_id, receptors, integration_test_exec_settings
        ):
            config = observation.generate_low_assign_resources_config(subarray_id).as_object
            subarray.assign_from_cdm(config)

    """when resources assigned the low telescope subarray goes in IDLE state."""
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)    

@when("I configure it for a scan")
def i_configure_it_for_a_scan(
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """I configure it for a scan."""
    observation = sut_settings.observation
    scan_duration = sut_settings.scan_duration

    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_configuring_a_subarray(
            integration_test_exec_settings
        ):
            config = observation.generate_low_tmc_scan_config(scan_duration, low_tmc=True).as_object
            tel = names.TEL()
            subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
            #logging.info(f"...:{config. . }")
            subarray.configure_from_cdm(config)

@then("the subarray must be in the READY state")
def the_subarray_must_be_in_the_ready_state(
    sut_settings: SutTestSettings, integration_test_exec_settings: fxt_types.exec_settings
):
    """the subarray must be in the READY state."""
    tel = names.TEL()
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(
        str(tel.tm.subarray(sut_settings.subarray_id)))
    oet_subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = oet_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)
