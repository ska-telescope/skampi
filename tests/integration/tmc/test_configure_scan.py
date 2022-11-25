"""Configure scan on telescope subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from resources.models.mvp_model.states import ObsState
from ..conftest import SutTestSettings


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.skamid
@pytest.mark.configure
@scenario(
    "features/tmc_configure_scan.feature",
    "Configure the mid telescope subarray using TMC",
)
def test_tmc_configure_scan_on_mid_subarray():
    """Configure scan on TMC mid telescope subarray."""


@pytest.mark.skip(reason="test fails stuck in CONFIGURING")
@pytest.mark.skamid
@pytest.mark.configure
@pytest.mark.tmc
@scenario(
    "features/tmc_configure_scan.feature",
    "Configure invalid scan on subarray using TMC",
)
def test_configure_invalid_scan_on_tmc_subarray_in_mid():
    """Configure invalid scan on tmc subarray in mid."""


@given("an TMC")
def a_tmc():
    """an TMC"""


@given("an telescope subarray", target_fixture="configuration")
def an_telescope_subarray(
    set_up_subarray_log_checking_for_tmc,
    base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: SutTestSettings,
) -> conf_types.ScanConfiguration:
    """an telescope subarray."""
    return base_configuration


@given("a subarray in the IDLE state")
def a_subarray_in_the_idle_state():
    """a subarray in the IDLE state."""


# @when("I configure it for scan")


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
    tmc_subarray = con_config.get_device_proxy(
        tel.tm.subarray(sut_settings.subarray_id)
    )
    result = tmc_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)
