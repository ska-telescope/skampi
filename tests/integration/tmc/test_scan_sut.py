"""Scan low TMC Subarray: Happy flow"""
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
    "features/tmc_low_scan_sut.feature",
    "execute a scan for the elapsed scan duration",
)
def test_tmc_low_subarray_for_a_scan():
    """Run a Scan on low tmc subarrays"""

# from conftest
# @given("the subarray <subarray_id> obsState is READY")

@then(parsers.parse("the subarray {subarray_id} obsState transitions to SCANNING"))
def the_subarray_obsstate_transitions_to_scanning(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
    subarray_id: int,
):
    """the SDP subarray must be in the SCANNING state until finished."""
    configured_subarray.id = subarray_id
    tel = names.TEL()
    tmc_subarray_name = tel.tm.subarray(configured_subarray.id)
    tmc_subarray = con_config.get_device_proxy(tmc_subarray_name)

    result = tmc_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.SCANNING)

@then(parsers.parse("the subarray {subarray_id} obsState transitions to READY after the scan duration elapsed"))
def subarray_obsState_transitions_to_ready(context_monitoring: fxt_types.context_monitoring, 
            sut_settings: SutTestSettings,
            integration_test_exec_settings: fxt_types.exec_settings,
            subarray_id: int,):
    
    tel = names.TEL()
    context_monitoring.re_init_builder()
    context_monitoring.wait_for(str(tel.tm.subarray(sut_settings.subarray_id))).for_attribute(
        "obsstate"
    ).to_become_equal_to(
        "READY", ignore_first=False, settings=integration_test_exec_settings
    )
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(
        str(tel.tm.subarray(sut_settings.subarray_id))
    )
    subarray = con_config.get_device_proxy(tel.tm.subarray(subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)

