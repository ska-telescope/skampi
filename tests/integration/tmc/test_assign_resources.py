"""Assign resources to subarray feature tests."""
import logging

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then
from resources.models.mvp_model.states import ObsState
from ska_ser_skallop.connectors import configuration as con_config
from ska_ser_skallop.mvp_control.describing import mvp_names as names
from ska_ser_skallop.mvp_control.entry_points import types as conf_types
from ska_ser_skallop.mvp_fixtures.fixtures import fxt_types

from ..conftest import SutTestSettings

logger = logging.getLogger(__name__)

# log capturing


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.assign
@scenario("features/tmc_assign_resources.feature", "Assign resources to low subarray")
def test_assign_resources_to_tmc_subarray_in_low():
    """Assign resources to tmc subarray in low."""


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@scenario(
    "features/tmc_assign_resources.feature",
    "Release resources from low subarray",
)
def test_release_resources_from_tmc_subarray_in_low():
    """Release resources from tmc subarrays in low."""


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.assign
@scenario("features/tmc_assign_resources.feature", "Assign resources to mid subarray")
def test_assign_resources_to_tmc_subarray_in_mid():
    """Assign resources to tmc subarray in mid."""


@pytest.fixture(name="composition")
def fxt_default_composition(base_composition: conf_types.Composition):
    """
    A fixture for default composition

    :param base_composition : An object for base composition
    :return: base composition
    """
    return base_composition


@pytest.fixture(name="set_restart_after_abort")
def fxt_set_restart_after_abort(sut_settings: SutTestSettings):
    """
    A fixture to set restart after abort

    :param sut_settings: A class representing the settings for the system under test.
    """
    sut_settings.restart_after_abort = True


@pytest.fixture(name="setup_context_monitoring_for_abort_test")
def fxt_setup_context_monitoring_for_abort_test(
    context_monitoring: fxt_types.context_monitoring,
    sut_settings: SutTestSettings,
    log_checking: fxt_types.log_checking,
):
    """
    A fixture to setup context monitoring for abort test

    :param context_monitoring: Object containing information about
        the context in which the test is being executed
    :param sut_settings: A class representing the settings for the system under test.
    :param log_checking: The skallop log_checking fixture to use
    """
    _tel = names.TEL()
    log_checking.capture_logs_from_devices(
        str(_tel.tm.subarray(sut_settings.subarray_id)),
        str(_tel.tm.subarray(sut_settings.subarray_id).sdp_leaf_node),
    )
    context_monitoring.set_waiting_on(_tel.csp.subarray(sut_settings.subarray_id)).for_attribute(
        "obsstate"
    ).to_become_equal_to("ABORTED")
    context_monitoring.set_waiting_on(_tel.sdp.subarray(sut_settings.subarray_id)).for_attribute(
        "obsstate"
    ).to_become_equal_to(["ABORTED", "EMPTY", "IDLE"])


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@pytest.mark.assign
@scenario("features/tmc_assign_resources.feature", "Abort assigning")
def test_abort_in_resourcing_mid(
    set_restart_after_abort: None,
    setup_context_monitoring_for_abort_test: None,
    composition: conf_types.Composition,
):
    """
    Assign resources to tmc subarray in mid.

    :param set_restart_after_abort: A fixture to set restart after abort which is set as none
    :param setup_context_monitoring_for_abort_test: A fixture to setup
        context monitoring for abort test
    :param composition: A fixture that represents the composition of the subarray.
    """


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skalow
@pytest.mark.assign
@scenario("features/tmc_assign_resources.feature", "Abort assigning Low")
def test_abort_in_resourcing_low(
    set_restart_after_abort: None,
    setup_context_monitoring_for_abort_test: None,
    composition: conf_types.Composition,
):
    """
    Assign resources to tmc subarray in low.

    :param set_restart_after_abort: A fixture to set restart after abort which is set as none
    :param setup_context_monitoring_for_abort_test: A fixture to setup
        context monitoring for abort test
    :param composition: A fixture that represents the composition of the subarray.
    """


@pytest.mark.skip(reason="temp skip for at-489")
@pytest.mark.k8s
@pytest.mark.k8sonly
@pytest.mark.skamid
@scenario(
    "features/tmc_assign_resources.feature",
    "Release resources from mid subarray",
)
def test_release_resources_from_tmc_subarray_in_mid():
    """Release resources from tmc subarrays in mid."""


@given("an TMC")
def a_tmc():
    """an TMC"""


@given("an telescope subarray", target_fixture="composition")
def an_telescope_subarray(
    set_up_subarray_log_checking_for_tmc,
    base_composition: conf_types.Composition,
) -> conf_types.Composition:
    """
    an telescope subarray.

    :param set_up_subarray_log_checking_for_tmc: To set up subarray log checking for tmc.
    :param base_composition : An object for base composition
    :return: base composition
    """
    return base_composition


# use when from ..shared_assign_resources
# @when("I assign resources to it")


@then("the subarray must be in IDLE state")
def the_subarray_must_be_in_idle_state(sut_settings: SutTestSettings):
    """
    the subarray must be in IDLE state.

    :param sut_settings: A class representing the settings for the system under test.
    """
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.IDLE)


@given("a subarray in the IDLE state")
def a_subarray_in_the_idle_state():
    """a subarray in the IDLE state."""


# @when("I release all resources assigned to it")


@then("the subarray must be in EMPTY state")
def the_subarray_must_be_in_empty_state(sut_settings: SutTestSettings):
    """
    the subarray must be in EMPTY state.

    :param sut_settings: A class representing the settings for the system under test.
    """
    tel = names.TEL()
    subarray = con_config.get_device_proxy(tel.tm.subarray(sut_settings.subarray_id))
    result = subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.EMPTY)


@then("the subarray should go into an aborted state")
def the_subarray_should_go_into_an_aborted_state(
    integration_test_exec_settings: fxt_types.exec_settings,
    sut_settings: SutTestSettings,
    context_monitoring: fxt_types.context_monitoring,
):
    """
    The subarray should go into an aborted state

    :param integration_test_exec_settings: Object containing
        the execution settings for the integration test
    :param sut_settings: Object containing the system under test settings
    :param context_monitoring: The context monitoring configuration.
    """
    tel = names.TEL()
    tmc_subarray_name = str(tel.tm.subarray(sut_settings.subarray_id))
    integration_test_exec_settings.recorder.assert_no_devices_transitioned_after(  # noqa: E501
        tmc_subarray_name, time_source="local"
    )
    tmc_subarray = con_config.get_device_proxy(tmc_subarray_name)
    result = tmc_subarray.read_attribute("obsState").value
    assert_that(result).is_equal_to(ObsState.ABORTED)
