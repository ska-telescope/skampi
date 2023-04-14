"""Assign Resource on a CSP Subarray"""
import logging

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types

from ...conftest import SutTestSettings

logger = logging.getLogger(__name__)


@pytest.mark.skalow
@pytest.mark.assign
@scenario(
    "features/tmc_cspln_assign.feature",
    "Assign resources to csp low subarray using TMC leaf node",
)
def test_assign_resources_on_csp_in_low():
    """AssignResources on csp subarray in low using the leaf node."""


@given("a CSP subarray in the EMPTY state", target_fixture="composition")
def an_csp_subarray_in_empty_state(
    set_csp_ln_entry_point, base_composition: conf_types.Composition
) -> conf_types.Composition:
    """an CSP subarray in Empty state.

    :param set_csp_ln_entry_point: An object to set csp leafnode entry point
    :param base_composition : An object for base composition
    :return: base composition
    """
    logger.info("an_csp_subarray_in_empty_state")
    return base_composition


@given("a TMC CSP subarray Leaf Node")
def a_csp_sln():
    """a TMC CSP subarray Leaf Node."""


# @when("I assign resources to it") from ...conftest


@then("the CSP subarray must be in IDLE state")
def the_csp_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
    """
    the CSP Subarray must be in IDLE state.

    :param sut_settings: A class representing the settings for the system under test.
    """

    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.csp.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)
