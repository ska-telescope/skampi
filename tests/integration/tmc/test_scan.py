"""Run scan on telescope subarray feature tests."""

import logging
import os
import time

import pytest
from assertpy import assert_that
from integration.sdp.vis_receive_utils import POD_CONTAINER, compare_data
from pytest_bdd import given, scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from .. import conftest
from ..conftest import SutTestSettings
from ..sdp.vis_receive_utils import K8sElementManager

LOG = logging.getLogger(__name__)

NAMESPACE_SDP = os.environ.get("KUBE_NAMESPACE_SDP")


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.scan
@scenario("features/tmc_scan.feature", "Run a scan from TMC")
def test_tmc_scan_on_mid_subarray():
    """Run a scan on TMC mid telescope subarray."""


@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.scan
@scenario("features/tmc_scan.feature", "Run a scan on low subarray from TMC")
def test_tmc_scan_on_low_subarray():
    """Run a scan on TMC low telescope subarray."""


@given("an TMC")
def a_tmc():
    """an TMC"""


@given("a subarray in READY state", target_fixture="scan")
def a_subarray_in_ready_state(
    set_up_subarray_log_checking_for_tmc,
    base_configuration: conf_types.ScanConfiguration,
    subarray_allocation_spec: fxt_types.subarray_allocation_spec,
    sut_settings: SutTestSettings,
) -> conf_types.ScanConfiguration:
    """
    a subarray in READY state

    :param set_up_subarray_log_checking_for_tmc: To set up subarray log checking for tmc.
    :param base_configuration: the base scan configuration.
    :param subarray_allocation_spec: the specification for the subarray allocation.
    :param sut_settings: the SUT test settings.
    :return: the base configuration for the subarray.
    """
    return base_configuration


# @when("I command it to scan for a given period")


@then("the subarray must be in the SCANNING state until finished")
def the_sdp_subarray_must_be_in_the_scanning_state(
    configured_subarray: fxt_types.configured_subarray,
    context_monitoring: fxt_types.context_monitoring,
    integration_test_exec_settings: fxt_types.exec_settings,
):
    """
    the SDP subarray must be in the SCANNING state until finished.

    :param configured_subarray: The configured subarray.
    :param context_monitoring: The context monitoring configuration.
    :param integration_test_exec_settings: The integration test execution settings.
    """
    tel = names.TEL()
    tmc_subarray_name = tel.tm.subarray(configured_subarray.id)
    tmc_subarray = con_config.get_device_proxy(tmc_subarray_name)

    result = tmc_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.SCANNING)
    # afterwards it must be ready
    context_monitoring.re_init_builder()
    context_monitoring.wait_for(tmc_subarray_name).for_attribute("obsstate").to_become_equal_to(
        "READY", ignore_first=False, settings=integration_test_exec_settings
    )
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(  # noqa: E501
        tmc_subarray_name
    )
    result = tmc_subarray.read_attribute("obsstate").value
    assert_that(result).is_equal_to(ObsState.READY)


@then("the data received matches with the data sent")
def check_measurement_set(
    dataproduct_directory,
    k8s_element_manager: K8sElementManager,
    sut_settings: conftest.SutTestSettings,
):
    """
    Check the data received are same as the data sent.

    :param dataproduct_directory: The directory where outputs are written
    :param k8s_element_manager: Kubernetes element manager
    :param sut_settings: SUT settings fixture
    """
    # Wait 10 seconds before checking the measurement set.
    # This gives enough time for the receiver for finish writing the data.
    time.sleep(10)

    receive_pod = "sdp-receive-data"
    data_container = POD_CONTAINER

    # Add data product directory to k8s element manager for cleanup
    parse_dir = dataproduct_directory.index("ska-sdp")
    data_eb_dir = dataproduct_directory[:parse_dir]
    k8s_element_manager.output_directory(
        data_eb_dir,
        receive_pod,
        data_container,
        NAMESPACE_SDP,
    )

    result = compare_data(
        receive_pod,
        data_container,
        NAMESPACE_SDP,
        f"{dataproduct_directory}/output.scan-1.ms",
    )
    assert result.returncode == 0
    LOG.info("Data sent matches the data received")
