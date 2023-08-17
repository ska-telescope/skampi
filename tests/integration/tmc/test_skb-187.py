"""Configure scan on telescope subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from resources.models.mvp_model.states import ObsState
from ska_control_model import ResultCode
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from ..conftest import SutTestSettings


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.configure
@scenario(
    "features/tmc_skb_187.feature",
    "Configure the mid telescope subarray using TMC with invaid input",
)
def test_tmc_configure_scan_with_invalid_input_on_mid_subarray():
    """Configure scan on TMC mid telescope subarray with invaid input."""


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.configure
@scenario(
    "features/tmc_skb_187.feature",
    "Configure the low telescope subarray using TMC with invalid input",
)
def test_tmc_configure_scan_with_invalid_input_on_low_subarray():
    """Configure scan on TMC low telescope subarray with invaid input."""


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
    """
    an telescope subarray.

    :param set_up_subarray_log_checking_for_tmc: To set up subarray log checking for tmc.
    :param base_configuration: the base scan configuration.
    :param subarray_allocation_spec: specification for the subarray allocation
    :param sut_settings: A class representing the settings for the system under test.
    :return: the updated base configuration for the subarray

    """
    return base_configuration


@given("a subarray in the IDLE state")
def a_subarray_in_the_idle_state():
    """a subarray in the IDLE state."""


@when("I configure it for scan")
def invoke_configure(sut_settings: SutTestSettings):
    tel = names.TEL()
    tmc_subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    pytest.command_result = tmc_subarray.command_inout("Configure", {})


@then("the subarray rejects the command and remain in IDLE obsstate")
def the_subarray_rejects_the_command_and_remain_in_the_IDLE_state(
    sut_settings: SutTestSettings,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    the subarray rejects the command and remain in IDLE obsstate.

    :param sut_settings: A class representing the settings for the system under test.
    :param integration_test_exec_settings: A fixture that represents the execution
        settings for the integration test.
    """
    assert_that(pytest.command_result[0][0]).is_equal_to(ResultCode.REJECTED)

    tel = names.TEL()
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(  # noqa: E501
        str(tel.tm.subarray(sut_settings.subarray_id)), time_source="local"
    )
    tmc_subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = tmc_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)
