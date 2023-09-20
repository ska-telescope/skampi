"""Configure scan on telescope subarray feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from ..conftest import SutTestSettings


# @pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.configure
@scenario(
    "features/tmc_configure_scan.feature",
    "Configure the mid telescope subarray using TMC",
)
def test_tmc_configure_scan_on_mid_subarray():
    """Configure scan on TMC mid telescope subarray."""


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.configure
@scenario(
    "features/tmc_configure_scan.feature",
    "Configure the low telescope subarray using TMC",
)
def test_tmc_configure_scan_on_low_subarray():
    """Configure scan on TMC low telescope subarray."""


@pytest.fixture(name="disable_clear_and_tear_down")
def fxt_disable_abort(allocated_subarray: fxt_types.allocated_subarray):
    """
    A fixture for disable abort

    :param allocated_subarray: skallop allocated_subarray fixture
    """
    allocated_subarray.disable_automatic_clear()
    allocated_subarray.disable_automatic_teardown()


@pytest.fixture(name="setup_monitoring_for_config_abort")
def fxt_setup_monitoring_for_config_abort(
    context_monitoring: fxt_types.context_monitoring,
    sut_settings: SutTestSettings,
):
    """
    A fixture to setup context monitoring for configure abort

    :param context_monitoring: The context monitoring configuration.
    :param sut_settings: A class representing the settings for the system under test.
    """
    tel = names.TEL()
    sub_id = sut_settings.subarray_id
    context_monitoring.set_waiting_on(tel.csp.subarray(sub_id)).for_attribute(
        "obsstate"
    ).and_observe()
    context_monitoring.set_waiting_on(tel.sdp.subarray(sub_id)).for_attribute(
        "obsstate"
    ).and_observe()


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.skamid
@pytest.mark.configure
@scenario("features/tmc_configure_scan.feature", "Abort configuring")
def test_abort_configuring_on_mid_tmc_subarray(
    disable_clear_and_tear_down: None,
    set_up_subarray_log_checking_for_tmc: None,
    setup_monitoring_for_config_abort: None,
):
    """
    Abort configuring.

    :param disable_clear_and_tear_down: object to disable clear and tear down
    :param set_up_subarray_log_checking_for_tmc: To set up subarray log checking for tmc.
    :param setup_monitoring_for_config_abort: To set up monitoring for config abort

    """


@pytest.mark.skip(reason="This functionality not tested at CSP/CBF, raised SKB-221")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.configure
@scenario("features/tmc_configure_scan.feature", "Abort configuring Low")
def test_abort_configuring_on_low_tmc_subarray(
    disable_clear_and_tear_down: None,
    set_up_subarray_log_checking_for_tmc: None,
    setup_monitoring_for_config_abort: None,
):
    """Abort TMC low configuring obstate.

    :param disable_clear_and_tear_down: object to disable clear and tear down
    :param set_up_subarray_log_checking_for_tmc: To set up subarray log checking for tmc.
    :param setup_monitoring_for_config_abort: To set up monitoring for config abort

    """


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


# @when("I configure it for scan")


@then("the subarray must be in the READY state")
def the_subarray_must_be_in_the_ready_state(
    sut_settings: SutTestSettings,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    the subarray must be in the READY state.

    :param sut_settings: A class representing the settings for the system under test.
    :param integration_test_exec_settings: A fixture that represents the execution
        settings for the integration test.
    """
    tel = names.TEL()
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(  # noqa: E501
        str(tel.tm.subarray(sut_settings.subarray_id)), time_source="local"
    )
    tmc_subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = tmc_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)
