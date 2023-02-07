"""Assign resources to subarray feature tests."""
import logging
import pytest
import json,os
from assertpy import assert_that
from pytest_bdd import given, scenario, then, parsers

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

from resources.models.mvp_model.states import ObsState

from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)

# log capturing


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@scenario(
    "features/tmc_sut_2.2.feature", "Configure for a scan on a subarray - happy flow"
)
def test_tmc_low_subarray_for_configure_a_scan():
    """Configure tmc subarrays in low."""

# from conftest
# @given("the Telescope is in ON state")

@given(parsers.parse("the subarray {subarray_id} obsState is IDLE"))
def the_subarray_is_in_idle_state(subarray_id, sut_settings: SutTestSettings):
    """the subarray is in IDLE state."""
    sut_settings.subarray_id = subarray_id
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)


# using when from conftest
# @when(" I issue the configure command with <scan_type> and <scan_configuration> to the subarray <subarray_id>")


@then(parsers.parse("the subarray <subarray_id> obsState is READY"))
def the_subarray_must_be_in_ready_state(subarray_id, sut_settings: SutTestSettings, integration_test_exec_settings: fxt_types.exec_settings):
    """the subarray is in READY state."""
    sut_settings.subarray_id = subarray_id
    tel = names.TEL()
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(
        str(tel.tm.subarray(sut_settings.subarray_id)))
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.READY)

