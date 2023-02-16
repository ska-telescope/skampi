"""Configure low TMC Subarray: Happy flow"""
import logging

import pytest
from assertpy import assert_that
from pytest_bdd import parsers, scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@scenario(
    "features/tmc_configure_scan_sut.feature",
    "Configure for a scan on a subarray - happy flow",
)
def test_tmc_low_subarray_for_configure_a_scan():
    """Configure low tmc subarrays"""


# from conftest
# @given("the Telescope is in ON state")

# from conftest
# @given(parsers.parse("the subarray {subarray_id} obsState is IDLE")

# from conftest
# @when(parsers.parse("I issue the configure command with {scan_type} and {scan_configuration} to the subarray {subarray_id}"))


@then(parsers.parse("the subarray {subarray_id} obsState is READY"))
def the_subarray_must_be_in_ready_state(
    subarray_id: int,
    sut_settings: SutTestSettings,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """the subarray is in READY state."""
    tel = names.TEL()
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(
        str(tel.tm.subarray(sut_settings.subarray_id))
    )
    subarray = con_config.get_device_proxy(tel.tm.subarray(subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)


@then(
    parsers.parse(
        "the {scan_type} is correctly configured on the subarray {subarray_id}"
    )
)
def the_configuration_is_verified_for_csp_sdp_subarray(subarray_id):
    # TODO: Sdp Subarray updates scan_type attribute value from AssignResources json
    pass
