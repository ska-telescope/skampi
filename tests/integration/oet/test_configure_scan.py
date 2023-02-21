"""
test_XTP-18866
----------------------------------
Tests for Configure the low telescope subarray using OET (XTP-19864)
"""

"""Configure scan on telescope subarray feature tests."""
from pathlib import Path
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
@scenario(
    "features/oet_configure_scan.feature",
    "Configure the low telescope subarray using OET",
)
def test_oet_configure_scan_on_low_subarray():
    """Configure scan on OET low telescope subarray."""


@given("an OET")
def an_oet():
    """an OET"""


@given("a valid scan configuration", target_fixture="valid_config_from_file")
def a_valid_scan_configuration():
    return Path("./tests/resources/test_data/OET_integration/configure_low.json")


@when("I configure it for a scan")
def i_configure_it_for_a_scan(
    valid_config_from_file: Path,
    allocated_subarray: fxt_types.allocated_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
):
    """I configure it for a scan."""
    subarray_id = sut_settings.subarray_id
    subarray = SubArray(subarray_id)
    with context_monitoring.context_monitoring():
        with allocated_subarray.wait_for_configuring_a_subarray(
            integration_test_exec_settings
        ):
            subarray.configure_from_file(str(valid_config_from_file), False)


@then("the subarray must be in the READY state")
def the_subarray_must_be_in_the_ready_state(
    sut_settings: SutTestSettings,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """the subarray must be in the READY state."""
    tel = names.TEL()
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(
        str(tel.tm.subarray(sut_settings.subarray_id))
    )
    oet_subarray = con_config.get_device_proxy(
        tel.tm.subarray(sut_settings.subarray_id)
    )
    result = oet_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)
