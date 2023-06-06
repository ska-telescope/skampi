"""Run abort on scanning subarray,feature tests."""
import pytest
from assertpy import assert_that
from pytest_bdd import scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from ..conftest import SutTestSettings


@pytest.fixture(name="disable_clear_and_tear_down")
def fxt_disable_abort(configured_subarray: fxt_types.configured_subarray):
    """
    A fixture for disable abort

    :param configured_subarray: skallop configured_subarray fixture
    """
    configured_subarray.disable_automatic_clear()
    configured_subarray.disable_automatic_teardown()


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.scan
@pytest.mark.xfail(reason="intermittent")
@scenario("features/tmc_abort_scanning.feature", "Abort scanning")
def test_tmc_abort_scanning_on_mid_subarray(disable_clear_and_tear_down: None):
    """
    Run a abort on TMC mid subarray when Scanning

    :param disable_clear_and_tear_down: object to disable clear and tear down
    """


@pytest.mark.skip(reason="This functionality not tested at CSP/CBF, raised SKB-221.")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.scan
@scenario("features/tmc_abort_scanning.feature", "Abort scanning Low")
def test_tmc_abort_scanning_on_low_subarray(disable_clear_and_tear_down: None):
    """
    Run a abort on TMC low subarray when Scanning
    :param disable_clear_and_tear_down: object to disable clear and tear down
    """


# from conftest
# @given("an subarray busy scanning")

# from conftest
# @when("I command it to Abort")


@then("the subarray should go into an aborted state")
def the_subarray_should_go_into_aborted_state(
    sut_settings: SutTestSettings,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    the subarray should go into an aborted state.

    :param sut_settings: A class representing the settings for the system under test.
    :param integration_test_exec_settings: A dictionary containing the execution
        settings for the integration tests.
    """
    tel = names.TEL()
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(  # noqa: E501
        str(tel.tm.subarray(sut_settings.subarray_id)), time_source="local"
    )
    tmc_subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = tmc_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.ABORTED)
