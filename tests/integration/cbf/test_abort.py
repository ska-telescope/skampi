import pytest
import os

from pytest_bdd import given, scenario, then, when
from assertpy import assert_that

from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types


from resources.models.mvp_model.states import ObsState

from ..conftest import SutTestSettings


@pytest.fixture(name="set_up_log_checking_for_cbf_subarray_during_abort_test")
def fxt_set_up_log_checking_for_cbf(
    log_checking: fxt_types.log_checking, sut_settings: SutTestSettings
):
    """Set up log capturing (if enabled by CATPURE_LOGS).

    :param log_checking: The skallop log_checking fixture to use
    """
    if os.getenv("CAPTURE_LOGS"):
        tel = names.TEL()
        cbf_subarray = str(tel.csp.cbf.subarray(sut_settings.subarray_id))
        log_checking.capture_logs_from_devices(cbf_subarray)


@pytest.fixture(name="test_settings")
def fxt_test_settings(sut_settings: SutTestSettings):
    sut_settings.scan_duration=4


@pytest.mark.skalow
@pytest.mark.cbf
@pytest.mark.assign
@scenario("features/cbf_abort_scan.feature", "Test successful Abort Scan on CBF")
def test_test_successful_abort_scan_on_cbf():
    """Test successful Abort Scan on CBF."""


@then("the subarray goes to EMPTY")
def the_subarray_goes_to_empty(
    sut_settings: SutTestSettings,
):
    """the subarray goes to EMPTY."""
    tel = names.TEL()
    cbf_subarray = con_config.get_device_proxy(
        tel.csp.cbf.subarray(sut_settings.subarray_id)
    )
    result = cbf_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.EMPTY)
