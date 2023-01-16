"""Start up the telescope from tmc feature tests."""
import logging

# import os

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from tests.integration.tmc import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from ska_ser_skallop.mvp_fixtures.context_management import (
    TelescopeContext,
)
from .. import conftest

logger = logging.getLogger(__name__)

@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.startup
@scenario("features/tmc_start_up_telescope.feature", "Start up the telescope in low")
def test_tmc_start_up_telescope_low():
    """Start up the telescope in low."""


@given("an TMCLow")
def a_tmc_low():
    """an TMCLow"""
    logger.info("I am in TMClow")
    tel = names.TEL()
    sut_settings = conftest.SutTestSettings()

    central_node_name = tel.tm.central_node
    central_node = con_config.get_device_proxy(central_node_name)
    result = central_node.ping()
    assert result > 0

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        subarray_node = con_config.get_device_proxy(tel.tm.subarray(index))
        result = subarray_node.ping()
        assert result > 0

    csp_master_leaf_node = con_config.get_device_proxy(tel.tm.csp_leaf_node)
    result = csp_master_leaf_node.ping()
    assert result > 0

    sdp_master_leaf_node = con_config.get_device_proxy(tel.tm.sdp_leaf_node)
    result = sdp_master_leaf_node.ping()
    assert result > 0

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        csp_subarray_leaf_node = con_config.get_device_proxy(
            tel.tm.subarray(index).csp_leaf_node
        )
        result = csp_subarray_leaf_node.ping()
        assert result > 0

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        sdp_subarray_leaf_node = con_config.get_device_proxy(
            tel.tm.subarray(index).sdp_leaf_node
        )
        result = sdp_subarray_leaf_node.ping()
        assert result > 0

@given("a Telescope consisting of SDP and CSP")
def a_telescope_with_csp_and_sdp():
    """a Telescope consisting of SDP and CSP"""
    tel = names.TEL()
    sut_settings = conftest.SutTestSettings()

    csp_master_leaf_node = con_config.get_device_proxy(tel.tm.csp_leaf_node)
    result = csp_master_leaf_node.ping()
    assert result > 0

    sdp_master_leaf_node = con_config.get_device_proxy(tel.tm.sdp_leaf_node)
    result = sdp_master_leaf_node.ping()
    assert result > 0

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        csp_subarray_leaf_node = con_config.get_device_proxy(
            tel.tm.subarray(index).csp_leaf_node
        )
        result = csp_subarray_leaf_node.ping()
        assert result > 0

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        sdp_subarray_leaf_node = con_config.get_device_proxy(
            tel.tm.subarray(index).sdp_leaf_node
        )
        result = sdp_subarray_leaf_node.ping()
        assert result > 0


@given("a Telescope consisting of SDP and CSP that is ON")
def a_telescope_with_sdp_and_csp_on():
    """a Telescope consisting of SDP and CSP that is ON"""
    tel = names.TEL()
    sut_settings = conftest.SutTestSettings()

    csp_master_leaf_node = con_config.get_device_proxy(tel.tm.csp_leaf_node)
    result = csp_master_leaf_node.read_attribute("state").value
    assert_that(str(result)).is_equal_to("ON")

    sdp_master_leaf_node = con_config.get_device_proxy(tel.tm.sdp_leaf_node)
    result = sdp_master_leaf_node.read_attribute("state").value
    assert_that(str(result)).is_equal_to("ON")

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        csp_subarray_leaf_node = con_config.get_device_proxy(
            tel.tm.subarray(index).csp_leaf_node
        )
        result = csp_subarray_leaf_node.read_attribute("state").value
        assert_that(str(result)).is_equal_to("ON")

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        sdp_subarray_leaf_node = con_config.get_device_proxy(
            tel.tm.subarray(index).sdp_leaf_node
        )
        result = sdp_subarray_leaf_node.read_attribute("state").value
        assert_that(str(result)).is_equal_to("ON")

# use @when("I start up the telescope") from ..conftest


@then("the sdp and csp must be on")
def the_sdp_and_csp_must_be_on(sut_settings: conftest.SutTestSettings):
    """the sdp and csp must be on"""
    tel = names.TEL()
    # Check state attribute of SDP Master
    sdp_master = con_config.get_device_proxy(tel.sdp.master)
    result = sdp_master.read_attribute("state").value
    assert_that(str(result)).is_equal_to("ON")
    for index in range(1, sut_settings.nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.sdp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("ON")
    # Check state attribute of CSP Master
    csp_master = con_config.get_device_proxy(tel.csp.controller)
    result = csp_master.read_attribute("state").value
    assert_that(str(result)).is_equal_to("ON")
    for index in range(1, sut_settings.nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.csp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("ON")
    # Check telescopeState attribute of Central Node
    central_node = con_config.get_device_proxy(tel.tm.central_node)
    result = central_node.read_attribute("telescopeState").value
    assert_that(str(result)).is_equal_to("ON")