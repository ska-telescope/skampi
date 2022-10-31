"""Start up the telescope from tmc feature tests."""
import logging
# import os

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then

from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from .. import conftest

logger = logging.getLogger(__name__)


@pytest.mark.skamid
@pytest.mark.startup
@scenario("features/tmc_start_up_telescope.feature", "Start up the telescope")
def test_tmc_start_up_telescope_mid():
    """Start up the telescope in mid."""

# marked as xfail due to SKB-170
@pytest.mark.xfail
@pytest.mark.skamid
@pytest.mark.standby
@scenario("features/tmc_start_up_telescope.feature", "Switch of the telescope")
def test_tmc_off_telescope_mid():
    """Off the telescope in mid."""


@given("an TMC")
def a_tmc():
    """an TMC"""
    tel = names.TEL()    
    sut_settings=conftest.SutTestSettings()

    central_node_name = tel.tm.central_node
    central_node = con_config.get_device_proxy(central_node_name)
    result=central_node.ping()
    assert result>0
    
    for index in range(1, sut_settings.nr_of_subarrays + 1):
        subarray_node= con_config.get_device_proxy(tel.tm.subarray(index))
        result=subarray_node.ping()
        assert result>0

    csp_master_leaf_node = con_config.get_device_proxy(tel.tm.csp_leaf_node)
    result=csp_master_leaf_node.ping()
    assert result>0

    sdp_master_leaf_node = con_config.get_device_proxy(tel.tm.sdp_leaf_node)
    result=sdp_master_leaf_node.ping()
    assert result>0

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        csp_subarray_leaf_node=con_config.get_device_proxy(tel.tm.subarray(index).csp_leaf_node)
        result=csp_subarray_leaf_node.ping()
        assert result>0

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        sdp_subarray_leaf_node=con_config.get_device_proxy(tel.tm.subarray(index).sdp_leaf_node)
        result=sdp_subarray_leaf_node.ping()
        assert result>0

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        dish_leaf_nodes=con_config.get_device_proxy(tel.tm.dish_leafnode(index))
        result=dish_leaf_nodes.ping()
        assert result>0




@given("a Telescope consisting of SDP, CSP and a Dish")
def a_telescope_with_csp_sdp_and_dish():
    """a Telescope consisting SDP, CSP and a Dish"""
    tel = names.TEL()    
    sut_settings=conftest.SutTestSettings()

    csp_master_leaf_node = con_config.get_device_proxy(tel.tm.csp_leaf_node)
    result=csp_master_leaf_node.ping()
    assert result>0

    sdp_master_leaf_node = con_config.get_device_proxy(tel.tm.sdp_leaf_node)
    result=sdp_master_leaf_node.ping()
    assert result>0

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        csp_subarray_leaf_node=con_config.get_device_proxy(tel.tm.subarray(index).csp_leaf_node)
        result=csp_subarray_leaf_node.ping()
        assert result>0

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        sdp_subarray_leaf_node=con_config.get_device_proxy(tel.tm.subarray(index).sdp_leaf_node)
        result=sdp_subarray_leaf_node.ping()
        assert result>0

    for index in range(1, sut_settings.nr_of_subarrays + 1):
        dish_leaf_nodes=con_config.get_device_proxy(tel.tm.dish_leafnode(index))
        result=dish_leaf_nodes.ping()
        assert result>0

@given("a Telescope consisting of SDP, CSP and a Dish that is ON")
def a_telescope_with_sdp_csp_and_dish_on():
    """a Telescope consisting of SDP, CSP and a Dish that is ON"""
    tel = names.TEL()    
    sut_settings=conftest.SutTestSettings()
    
    csp_master_leaf_node = con_config.get_device_proxy(tel.tm.csp_leaf_node)
    result = csp_master_leaf_node.read_attribute("state").value
    assert_that(str(result)).is_equal_to("ON")


    sdp_master_leaf_node = con_config.get_device_proxy(tel.tm.sdp_leaf_node)
    result = sdp_master_leaf_node.read_attribute("state").value
    assert_that(str(result)).is_equal_to("ON")


    for index in range(1, sut_settings.nr_of_subarrays + 1):
        csp_subarray_leaf_node=con_config.get_device_proxy(tel.tm.subarray(index).csp_leaf_node)
        result = csp_subarray_leaf_node.read_attribute("state").value
        assert_that(str(result)).is_equal_to("ON")


    for index in range(1, sut_settings.nr_of_subarrays + 1):
        sdp_subarray_leaf_node=con_config.get_device_proxy(tel.tm.subarray(index).sdp_leaf_node)
        result = sdp_subarray_leaf_node.read_attribute("state").value
        assert_that(str(result)).is_equal_to("ON")


    for index in range(1, sut_settings.nr_of_subarrays + 1):
        dish_leaf_nodes=con_config.get_device_proxy(tel.tm.dish_leafnode(index))
        result = dish_leaf_nodes.read_attribute("state").value
        assert_that(str(result)).is_equal_to("ON")


# when
# use @when("I start up the telescope") from ..conftest

# when
# use @when("I switch off the telescope") from ..conftest

# thens


@then("the sdp, csp and dish must be on")
def the_sdp_csp_and_dish_must_be_on(sut_settings: conftest.SutTestSettings):
    """the sdp, csp and dish must be on."""
    tel = names.TEL()
    mid = names.Mid()
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
    # Check state attribute of Dish Masters
    for dish_id in sut_settings.receptors:
        dish = con_config.get_device_proxy(mid.dish(dish_id))
        result = dish.read_attribute("state").value
        assert_that(str(result)).is_equal_to("ON")
    # Check telescopeState attribute of Central Node
    central_node = con_config.get_device_proxy(tel.tm.central_node)
    result = central_node.read_attribute("telescopeState").value
    assert_that(str(result)).is_equal_to("ON")


@then("the sdp, csp and dish must be off")
def the_sdp_csp_and_dish_must_be_off(sut_settings: conftest.SutTestSettings, integration_test_exec_settings: fxt_types.exec_settings,):
    """the sdp, csp and dish must be off."""
    tel = names.TEL()
    mid = names.Mid()
    # Check state attribute of SDP Master
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(str(tel.tm.central_node))
    sdp_master = con_config.get_device_proxy(tel.sdp.master)
    result = sdp_master.read_attribute("state").value
    assert_that(str(result)).is_equal_to("OFF")
    for index in range(1, sut_settings.nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.sdp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("OFF")
    # Check state attribute of CSP Master
    csp_master = con_config.get_device_proxy(tel.csp.controller)
    result = csp_master.read_attribute("state").value
    assert_that(str(result)).is_equal_to("OFF")
    for index in range(1, sut_settings.nr_of_subarrays + 1):
        subarray = con_config.get_device_proxy(tel.csp.subarray(index))
        result = subarray.read_attribute("state").value
        assert_that(str(result)).is_equal_to("OFF")
    # Check state attribute of Dish Masters
    for dish_id in sut_settings.receptors:
        dish = con_config.get_device_proxy(mid.dish(dish_id))
        result = dish.read_attribute("state").value
        assert_that(str(result)).is_equal_to("STANDBY")
    # Check telescopeState attribute of Central Node
    central_node = con_config.get_device_proxy(tel.tm.central_node)
    result = central_node.read_attribute("telescopeState").value
    assert_that(str(result)).is_equal_to("STANDBY")
