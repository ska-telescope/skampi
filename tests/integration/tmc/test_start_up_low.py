# """Start up the telescope from tmc feature tests."""
# import logging

# # import os

# import pytest
# from assertpy import assert_that
# from pytest_bdd import given, scenario, then

# from ska_ser_skallop.connectors import configuration as con_config
# from ska_ser_skallop.mvp_control.describing import mvp_names as names
# from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

# from ska_ser_skallop.mvp_fixtures.context_management import (
#     TelescopeContext,
# )
# from .. import conftest
# import time

# logger = logging.getLogger(__name__)

# @pytest.mark.k8s
# @pytest.mark.k8sonly
# @pytest.mark.skalow
# @pytest.mark.startup
# @scenario("features/tmc_start_up_telescope.feature", "Start up the telescope in low")
# def test_tmc_start_up_telescope_low():
#     """Start up the telescope in low."""


# @pytest.mark.skalow
# @pytest.mark.standby
# @scenario("features/tmc_start_up_telescope.feature", "Switch of the telescope in low")
# def test_tmc_off_telescope_low():
#     """Off the telescope in low."""


# @given("an TMCLow")
# def a_tmc_low():
#     """an TMCLow"""
#     logger.info("I am in TMClow")
#     tel = names.TEL()
#     logger.info("I am in Tel")
#     sut_settings = conftest.SutTestSettings()

#     central_node_name = tel.tm.central_node
#     logger.info("I am in CN")
#     central_node = con_config.get_device_proxy(central_node_name)
#     result = central_node.ping()
#     logger.info("I am in CN ping")
#     assert result > 0

#     for index in range(1, sut_settings.nr_of_subarrays + 1):
#         subarray_node = con_config.get_device_proxy(tel.tm.subarray(index))
#         logger.info("I am in SN ping")
#         result = subarray_node.ping()
#         logger.info("I am in SN ping")
#         assert result > 0

#     csp_master_leaf_node = con_config.get_device_proxy(tel.tm.csp_leaf_node)
#     result = csp_master_leaf_node.ping()
#     logger.info("I am in CSPMLN ping")
#     assert result > 0

#     sdp_master_leaf_node = con_config.get_device_proxy(tel.tm.sdp_leaf_node)
#     result = sdp_master_leaf_node.ping()
#     logger.info("I am in SDPMLN ping")
#     assert result > 0

#     for index in range(1, sut_settings.nr_of_subarrays + 1):
#         csp_subarray_leaf_node = con_config.get_device_proxy(
#             tel.tm.subarray(index).csp_leaf_node
#         )
#         result = csp_subarray_leaf_node.ping()
#         logger.info("I am in CSPSLN ping")
#         assert result > 0

#     for index in range(1, sut_settings.nr_of_subarrays + 1):
#         sdp_subarray_leaf_node = con_config.get_device_proxy(
#             tel.tm.subarray(index).sdp_leaf_node
#         )
#         result = sdp_subarray_leaf_node.ping()
#         logger.info("I am in SDPSLN ping")
#         assert result > 0

# @given("a Telescope consisting of SDP and CSP")
# def a_telescope_with_csp_and_sdp():
#     """a Telescope consisting of SDP and CSP"""
#     tel = names.TEL()
#     sut_settings = conftest.SutTestSettings()

#     csp_master_leaf_node = con_config.get_device_proxy(tel.tm.csp_leaf_node)
#     result = csp_master_leaf_node.ping()
#     logger.info("I am in cspMLN ping")
#     assert result > 0

#     sdp_master_leaf_node = con_config.get_device_proxy(tel.tm.sdp_leaf_node)
#     result = sdp_master_leaf_node.ping()
#     logger.info("I am in sdpMLN ping")
#     assert result > 0

#     for index in range(1, sut_settings.nr_of_subarrays + 1):
#         csp_subarray_leaf_node = con_config.get_device_proxy(
#             tel.tm.subarray(index).csp_leaf_node
#         )
#         result = csp_subarray_leaf_node.ping()
#         logger.info("I am in cspSLN ping")
#         assert result > 0

#     for index in range(1, sut_settings.nr_of_subarrays + 1):
#         sdp_subarray_leaf_node = con_config.get_device_proxy(
#             tel.tm.subarray(index).sdp_leaf_node
#         )
#         result = sdp_subarray_leaf_node.ping()
#         logger.info("I am in sdpSLN ping")
#         assert result > 0
#         logger.info("why not here")


# @given("a Telescope consisting of SDP and CSP that is ON")
# def a_telescope_with_sdp_and_csp_on():
#     """a Telescope consisting of SDP and CSP that is ON"""
#     tel = names.TEL()
#     sut_settings = conftest.SutTestSettings()

#     csp_master_leaf_node = con_config.get_device_proxy(tel.tm.csp_leaf_node)
#     logger.info("I am in get cspmln")
#     result = csp_master_leaf_node.read_attribute("state").value
#     logger.info("I am in read attr cspmln")
#     assert_that(str(result)).is_equal_to("ON")

#     sdp_master_leaf_node = con_config.get_device_proxy(tel.tm.sdp_leaf_node)
#     logger.info("I am in get sdpmln")
#     result = sdp_master_leaf_node.read_attribute("state").value
#     logger.info("I am in read attr sdpmln")
#     assert_that(str(result)).is_equal_to("ON")
#     logger.info("I am in assert sdpmln")

#     for index in range(1, sut_settings.nr_of_subarrays + 1):
#         csp_subarray_leaf_node = con_config.get_device_proxy(
#             tel.tm.subarray(index).csp_leaf_node
#         )
#         logger.info("I am in get dv proxy cspsln")
#         result = csp_subarray_leaf_node.read_attribute("state").value
#         logger.info("I am in assert dv proxy cspsln")
#         assert_that(str(result)).is_equal_to("ON")

#     for index in range(1, sut_settings.nr_of_subarrays + 1):
#         sdp_subarray_leaf_node = con_config.get_device_proxy(
#             tel.tm.subarray(index).sdp_leaf_node
#         )
#         logger.info("I am in get dv proxy sdpsln")
#         result = sdp_subarray_leaf_node.read_attribute("state").value
#         assert_that(str(result)).is_equal_to("ON")
#         logger.info("I am in assert dv proxy sdpsln")

# # use @when("I start up the telescope") from ..conftest


# @then("the sdp and csp must be on")
# def the_sdp_and_csp_must_be_on(sut_settings: conftest.SutTestSettings):
#     """the sdp and csp must be on"""
#     tel = names.TEL()
#     logger.info("I am in 4th TEL")
#     # Check state attribute of SDP Master
#     sdp_master = con_config.get_device_proxy(tel.sdp.master)
#     logger.info("I am in get2 dv proxy sdpm")
#     result = sdp_master.read_attribute("state").value
#     logger.info("I am in assert dv proxy sdpm")
#     assert_that(str(result)).is_equal_to("ON")
#     logger.info("I am in get3 assert dv proxy sdpm")
#     for index in range(1, sut_settings.nr_of_subarrays + 1):
#         subarray = con_config.get_device_proxy(tel.sdp.subarray(index))
#         logger.info("I am in get3  dv proxy subarray")
#         result = subarray.read_attribute("state").value
#         logger.info("I am in assert  dv proxy subarray")
#         assert_that(str(result)).is_equal_to("ON")
#     # Check state attribute of CSP Master
#     csp_master = con_config.get_device_proxy(tel.csp.controller)
#     logger.info("I am in get3 dv proxy cspmaster")
#     result = csp_master.read_attribute("state").value
#     logger.info("I am in result dv proxy cspmaster")
#     assert_that(str(result)).is_equal_to("ON")
#     logger.info("I am in assert dv proxy cspmaster")
#     for index in range(1, sut_settings.nr_of_subarrays + 1):
#         subarray = con_config.get_device_proxy(tel.csp.subarray(index))
#         logger.info("I am in assert dv proxy cspsubarray")
#         result = subarray.read_attribute("state").value
#         logger.info("I am in result4 dv proxy cspsubarray")
#         assert_that(str(result)).is_equal_to("ON")
#         logger.info("I am in assert5 dv proxy cspsubarray")
#     # Check telescopeState attribute of Central Node
#     central_node = con_config.get_device_proxy(tel.tm.central_node)
#     logger.info("I am in assert5 dv proxy cn")
#     result = central_node.read_attribute("telescopeState").value
#     logger.info("I am in assert6 dv proxy cspsubarray")
#     assert_that(str(result)).is_equal_to("ON")

# @then("the sdp and csp must be off")
# def the_sdp_and_csp_must_be_off(
#     sut_settings: conftest.SutTestSettings,
#     integration_test_exec_settings: fxt_types.exec_settings,
# ):
#     """the sdp and csp must be off."""
#     tel = names.TEL()
#     # Check state attribute of SDP Master
#     integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(
#         str(tel.tm.central_node)
#     )
#     sdp_master = con_config.get_device_proxy(tel.sdp.master)
#     result = sdp_master.read_attribute("state").value
#     assert_that(str(result)).is_equal_to("OFF")
#     for index in range(1, sut_settings.nr_of_subarrays + 1):
#         subarray = con_config.get_device_proxy(tel.sdp.subarray(index))
#         result = subarray.read_attribute("state").value
#         assert_that(str(result)).is_equal_to("OFF")
#     # Check state attribute of CSP Master
#     csp_master = con_config.get_device_proxy(tel.csp.controller)
#     result = csp_master.read_attribute("state").value
#     assert_that(str(result)).is_equal_to("OFF")
#     for index in range(1, sut_settings.nr_of_subarrays + 1):
#         subarray = con_config.get_device_proxy(tel.csp.subarray(index))
#         result = subarray.read_attribute("state").value
#         assert_that(str(result)).is_equal_to("OFF")
#     # Check telescopeState attribute of Central Node
#     central_node = con_config.get_device_proxy(tel.tm.central_node)
#     result = central_node.read_attribute("telescopeState").value
#     logger.info("I am in assert6 dv proxy CN")
#     assert_that(str(result)).is_equal_to("OFF")
#     logger.info("I am in assert6 dv proxy Cn")