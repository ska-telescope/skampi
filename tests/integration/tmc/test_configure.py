"""Configure resources to subarray feature tests."""
import logging
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from resources.models.mvp_model.states import ObsState
from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)

# log capturing
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.configure
@scenario("features/tmc_configure.feature", "Configure tmc-mid subarray for a scan")
def test_configure_to_tmc_subarray_in_mid():
    """Configure to tmc subarray in mid."""


@given("an TMC")
def a_tmc():
    """an TMC"""


@given("an telescope subarray", target_fixture="composition")
def an_telescope_subarray(
    set_up_subarray_log_checking_for_tmc, base_composition: conf_types.Composition
) -> conf_types.Composition:
    """an telescope subarray."""
    return base_composition


# use when from ..shared_assign_resources
#@When("I configure it for a scan")


@then("the subarray must be in READY state")
def the_subarray_must_be_in_ready_state(sut_settings: SutTestSettings):
    """the subarray must be in READY state."""
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)